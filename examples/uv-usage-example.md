# UV Usage Examples for LLM Runner

This document demonstrates practical usage of the LLM Runner with UV in different scenarios.

## Prerequisites

1. **Install UV** (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. **Set Environment Variables**:
```bash
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_MODEL="gpt-4"
```

## Basic Usage

### 1. Install Dependencies

```bash
# Install all dependencies (uses system Python)
uv sync

# Install with development dependencies
uv sync --group dev
```

### 2. Run the Script

```bash
# Method 1: Direct script execution (recommended for CI/CD)
uv run llm_runner.py \
  --input-file examples/simple-example.json \
  --output-file result.json \
  --log-level INFO

# Method 2: Use the installed entry point
uv run llm-runner \
  --input-file examples/simple-example.json \
  --output-file result.json \
  --log-level INFO
```

## CI/CD Integration Examples

### GitHub Actions

```yaml
name: LLM Task Automation

on: [push, pull_request]

jobs:
  llm-task:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Install UV
      run: curl -LsSf https://astral.sh/uv/install.sh | sh
    
    - name: Run LLM Task
      run: |
        uv run llm_runner.py \
          --input-file .github/context.json \
          --output-file output/result.json \
          --log-level INFO
      env:
        AZURE_OPENAI_ENDPOINT: ${{ secrets.AZURE_OPENAI_ENDPOINT }}
        AZURE_OPENAI_MODEL: ${{ secrets.AZURE_OPENAI_MODEL }}
```

### Azure DevOps

```yaml
trigger:
- main

pool:
  vmImage: 'ubuntu-latest'

steps:
- script: |
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo "##vso[task.setvariable variable=PATH]${HOME}/.local/bin:${PATH}"
  displayName: 'Install UV'

- script: |
    uv run llm_runner.py \
      --input-file context.json \
      --output-file $(Build.ArtifactStagingDirectory)/result.json
  displayName: 'Run LLM Task'
  env:
    AZURE_OPENAI_ENDPOINT: $(AZURE_OPENAI_ENDPOINT)
    AZURE_OPENAI_MODEL: $(AZURE_OPENAI_MODEL)
```

### Docker Usage

```dockerfile
FROM python:3.11-slim

# Install UV
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Copy project files
WORKDIR /app
COPY . .

# Install dependencies
RUN uv sync

# Set default command
CMD ["uv", "run", "llm_runner.py", "--help"]
```

## Development Workflow

### 1. Setup Development Environment

```bash
# Install with development dependencies
uv sync --group dev

# Run linting and formatting
uv run ruff check .
uv run ruff format .

# Run type checking
uv run mypy llm_runner.py
```

### 2. Testing

```bash
# Run validation tests
uv run python test_runner.py

# Run unit tests (when implemented)
uv run pytest tests/

# Run with coverage
uv run pytest tests/ --cov=llm_runner
```

### 3. Quick Development Runs

```bash
# Run with debug logging
uv run llm_runner.py \
  --input-file examples/simple-example.json \
  --output-file debug-output.json \
  --log-level DEBUG

# Test different examples
uv run llm_runner.py --input-file examples/pr-review-example.json --output-file pr-result.json
uv run llm_runner.py --input-file examples/minimal-example.json --output-file minimal-result.json
```

## UV Project Benefits

### 1. **System Python Usage**
- Uses your system Python installation
- No Python version management overhead
- Perfect for containers with pre-installed Python

### 2. **Fast Dependency Resolution**
- 10-100x faster than pip
- Parallel downloads and efficient caching
- Lock file ensures reproducible builds

### 3. **CI/CD Optimized**
- Single command dependency installation
- No virtual environment activation needed
- Works seamlessly in containers

### 4. **Development Experience**
- Integrated linting and formatting
- Type checking configuration
- Clear development vs production dependencies

## Lock File Management

```bash
# Update dependencies and regenerate lock file
uv sync --upgrade

# Add new dependency
uv add requests

# Add development dependency
uv add --dev black

# Remove dependency
uv remove requests
```

## Troubleshooting

### UV Not Found
```bash
# Check if UV is installed
uv --version

# If not found, reinstall
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # or restart terminal
```

### Missing Dependencies
```bash
# Ensure dependencies are synced
uv sync

# For development work
uv sync --group dev
```

### Python Version Issues
```bash
# Check Python version
python --version

# UV will use system Python by default
# Ensure you have Python 3.11+ installed
```

## Best Practices

1. **Always commit `uv.lock`** - Ensures reproducible builds
2. **Use `uv run` in CI/CD** - No activation needed
3. **Separate dev dependencies** - Keep production lean
4. **Pin major versions** - For stability in production
5. **Use environment variables** - Never commit secrets

This setup provides a modern, fast, and reliable Python development experience optimized for CI/CD workflows! 