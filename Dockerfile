# Multi-stage build following uv Docker best practices
# Base: Custom miniconda RHEL 8 image with Python 3.12 and uv
# ================================
# System and Azure DevOps dependencies:
# ================================

FROM teambank.jfrog.io/cdos-base-images-docker/miniconda:rhel8-4.11.0 AS base
ARG TARGETARCH

# https://github.com/docker/buildx/issues/844
# it's apparently a feature to silently keep building with the wrong arch if the
# upstream image is not a multiarch image and is not available in the requested arch
RUN arch=$(arch); \
    [ "$arch" = "aarch64" ] && arch=arm64; \
    [ "$arch" = "x86_64" ]  && arch=amd64; \
    [ "$arch" = "arm64" ] && arch=arm64; \
    [ "$TARGETARCH" = "$arch" ] || { echo "ERROR! Image build is running on $arch but $TARGETARCH was requested! Quitting!" && false; }

COPY yq_$TARGETARCH /usr/local/bin/yq

# Install system dependencies including essential tools for Azure DevOps
RUN chmod +x /usr/local/bin/yq && \
    microdnf update -y && \
    microdnf install -y \
    jq \
    curl \
    wget \
    git \
    openssh-clients \
    tar \
    gzip \
    unzip \
    gettext && \
    microdnf clean all

# Install Azure CLI (required for most Azure DevOps pipelines)
RUN rpm --import https://packages.microsoft.com/keys/microsoft.asc && \
    echo -e "[azure-cli]\nname=Azure CLI\nbaseurl=https://packages.microsoft.com/rhel/8/prod\nenabled=1\ngpgcheck=1\ngpgkey=https://packages.microsoft.com/keys/microsoft.asc" > /etc/yum.repos.d/azure-cli.repo && \
    microdnf install -y azure-cli && \
    microdnf clean all

# Install Azure DevOps CLI extension
RUN az extension add -n azure-devops --system

# ================================
# Python specific stuff:
# ================================

# Enable uv optimizations for Docker
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_CACHE_DIR=/opt/uv-cache/
ENV PYTHONOPTIMIZE=2

# Create conda environment with Python 3.12
ENV CONDA_DEFAULT_ENV=llm-runtime
COPY environment.yml /tmp/environment.yml

RUN --mount=type=secret,id=ARTIFACTORY_USR \
    --mount=type=secret,id=ARTIFACTORY_PSW \
    export DEVOPS_USER=not_needed && \
    export DEVOPS_PWD=any_value && \
    export ARTIFACTORY_USER=$(cat /run/secrets/ARTIFACTORY_USR) && \
    export ARTIFACTORY_PWD=$(cat /run/secrets/ARTIFACTORY_PSW) && \
    envsubst < ~/.netrc.tpl > ~/.netrc && \
    conda env create -f /tmp/environment.yml --quiet && \
    echo "source activate $CONDA_DEFAULT_ENV" > ~/.bashrc && \
    conda clean -afy && \
    rm /tmp/environment.yml

# Activate conda environment for all subsequent commands
ENV PATH="/opt/conda/envs/$CONDA_DEFAULT_ENV/bin:$PATH"

# Intermediate layer: Install dependencies only
# This layer will be cached until pyproject.toml or uv.lock changes
RUN --mount=type=cache,target=/opt/uv-cache/ \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --compile-bytecode

# Copy the entire project
COPY . /app
WORKDIR /app

# Final sync: Install the project itself
RUN --mount=type=cache,target=/opt/uv-cache/ \
    uv sync --locked --compile-bytecode

# Performance optimization: Disable uv sync, code is already compiled
ENV UV_NO_SYNC=true

# Set to sane defaults during POC
ENV AZURE_OPENAI_ENDPOINT=https://ai-openai-dev-swecen-001.openai.azure.com/
ENV AZURE_OPENAI_MODEL=gpt-4.1-nano
ENV AZURE_OPENAI_API_VERSION=2024-12-01-preview

# Copy and set up entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set the entrypoint to activate conda environment
ENTRYPOINT ["/entrypoint.sh"]

# Default command to run the main application
CMD ["uv", "run", "llm_ci_runner.py", "--help"] 
