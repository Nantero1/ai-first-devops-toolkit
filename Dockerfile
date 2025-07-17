# ============================
# STAGE 1: Build Environment
# ============================
FROM teambank.jfrog.io/cdos-base-images-docker/rhel:8 AS builder
ARG TARGETARCH

# Validate architecture match to prevent silent wrong-arch builds
RUN arch=$(arch); \
    [ "$arch" = "aarch64" ] && arch=arm64; \
    [ "$arch" = "x86_64" ]  && arch=amd64; \
    [ "$arch" = "arm64" ] && arch=arm64; \
    [ "$TARGETARCH" = "$arch" ] || { echo "ERROR! Image build is running on $arch but $TARGETARCH was requested! Quitting!" && false; }

USER 0

# Install build dependencies and clean cache
RUN microdnf clean all && \
    microdnf update -y && \
    microdnf install --nodocs -y \
    python3.12 \
    python3.12-pip \
    python3.12-devel && \
    microdnf clean all

COPY ./files/.netrc.tpl /root/.netrc.tpl
COPY ./files/pip.conf /root/.pip/pip.conf

# Configure Python and uv
ENV PATH="/root/.local/bin:$PATH"
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_CACHE_DIR=/opt/uv-cache/
ENV PYTHONOPTIMIZE=2

# Set Python 3.12 as default python
RUN alternatives --set python3 /usr/bin/python3.12 && \
    alternatives --set python /usr/bin/python3.12

# Copy dependency files and install Python packages
WORKDIR /app
COPY pyproject.toml uv.lock ./

# Setup .netrc for private repository access during build
RUN --mount=type=secret,id=ARTIFACTORY_USR \
    --mount=type=secret,id=ARTIFACTORY_PSW \
    --mount=type=cache,target=/opt/uv-cache/ \
    export ARTIFACTORY_USER=$(cat /run/secrets/ARTIFACTORY_USR) && \
    export ARTIFACTORY_PWD=$(cat /run/secrets/ARTIFACTORY_PSW) && \
    envsubst < ~/.netrc.tpl > ~/.netrc && \
    python -m pip install uv && \
    uv sync --no-install-project --compile-bytecode --upgrade && \
    rm ~/.netrc

# Copy application code and install the project
COPY llm_ci_runner/ ./llm_ci_runner/
COPY README.md LICENSE NOTICE ./

COPY scripts/optimize_venv.py /tmp/optimize_venv.py
RUN --mount=type=cache,target=/opt/uv-cache/ \
    uv sync --compile-bytecode --upgrade && \
# Optimize image size by removing source files for packages with compiled bytecode
# Keep essential modules and packages that are needed for imports
    python /tmp/optimize_venv.py /app/.venv && \
    rm /tmp/optimize_venv.py

# ============================
# STAGE 2: Runtime Environment  
# ============================
FROM teambank.jfrog.io/cdos-base-images-docker/rhel:8 AS runtime
ARG TARGETARCH

# Validate architecture match in runtime stage too
RUN arch=$(arch); \
    [ "$arch" = "aarch64" ] && arch=arm64; \
    [ "$arch" = "x86_64" ]  && arch=amd64; \
    [ "$arch" = "arm64" ] && arch=arm64; \
    [ "$TARGETARCH" = "$arch" ] || { echo "ERROR! Image build is running on $arch but $TARGETARCH was requested! Quitting!" && false; }

USER 0

# Install runtime dependencies and Python 3.12
COPY yq_$TARGETARCH /usr/local/bin/yq
RUN chmod +x /usr/local/bin/yq && \
    microdnf update -y && \
    microdnf install --nodocs -y \
    python3.12 \
    jq \
    curl \
    wget \
    tar \
    gzip \
    unzip \
    git \
    gettext \
    shadow-utils \
    sudo \
    util-linux && \
    microdnf clean all

# Set Python 3.12 as default python
RUN alternatives --set python3 /usr/bin/python3.12 && \
    alternatives --set python /usr/bin/python3.12

# Create AzDevOps_azpcontainer user with UID 1001 and configure sudo privileges
RUN useradd -m -u 1001 AzDevOps_azpcontainer 2>/dev/null || true && \
    usermod -aG wheel AzDevOps_azpcontainer && \
    echo "AzDevOps_azpcontainer ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/azdevops && \
    chmod 0440 /etc/sudoers.d/azdevops

# Configure environment paths
ENV PATH="/root/.local/bin:$PATH"

# Copy the Python virtual environment and application from builder
COPY --from=builder /app /app
COPY --from=builder /usr/local/bin/uv /usr/local/bin/uv
COPY --from=builder /usr/local/lib64/python3.12/site-packages/uv /usr/local/lib64/python3.12/site-packages/uv

WORKDIR /app

# for test coverage report generation
ENV DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=true

# Set up Python virtual environment
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"

# Performance optimizations for runtime
ENV UV_NO_SYNC=true
ENV UV_LINK_MODE=copy

# Color support for Azure DevOps
ENV TERM=xterm-256color
ENV FORCE_COLOR=1
ENV COLORTERM=truecolor
ENV COLUMNS=120
ENV TTY_COMPATIBLE=1

# Set default Azure OpenAI configuration for POC
ENV AZURE_OPENAI_ENDPOINT=https://ai-openai-dev-swecen-001.openai.azure.com/
ENV AZURE_OPENAI_MODEL=gpt-4.1-nano-stable
ENV AZURE_OPENAI_API_VERSION=2024-12-01-preview

# Copy and configure entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set entrypoint and default command
ENTRYPOINT ["/entrypoint.sh"]
CMD ["uv", "run", "python", "-m", "llm_ci_runner", "--help"] 
