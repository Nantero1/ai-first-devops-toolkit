# LLM Runner - CI/CD LLM Utilities

A simple, zero-friction utility for running LLM-driven tasks in CI/CD pipelines using Microsoft Semantic Kernel.

## Features

- 🚀 **Zero-friction CLI**: Single script, minimal configuration
- 🔐 **Enterprise security**: Azure RBAC via DefaultAzureCredential
- 📋 **Structured outputs**: Optional Pydantic models for deterministic results
- 🎨 **Beautiful logging**: Rich console output with timestamps and colors
- 📁 **File-based I/O**: CI/CD friendly with JSON input/output
- 🔧 **Simple & extensible**: Easy to understand and modify

## Quick Start

### 1. Install Dependencies with UV

```bash
# Install UV if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies (will use system Python)
uv sync
```

### 2. Set Environment Variables

```bash
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_MODEL="gpt-4"
export AZURE_OPENAI_API_VERSION="2024-08-01-preview"  # Optional
```

### 3. Basic Usage

```bash
# Run directly with UV (recommended for CI/CD)
uv run llm_runner.py \
  --input-file examples/simple-example.json \
  --output-file result.json \
  --log-level INFO

# Or use the installed script entry point
uv run llm-runner \
  --input-file examples/simple-example.json \
  --output-file result.json \
  --log-level INFO
```

## Input Format

The script accepts JSON input with the following structure:

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant."
    },
    {
      "role": "user", 
      "content": "Your task description here",
      "name": "optional-user-name"
    }
  ],
  "context": {
    "session_id": "optional-session-id",
    "metadata": {
      "any": "additional context"
    }
  }
}
```

**Required fields:**
- `messages`: Array of chat messages with `role` and `content`

**Optional fields:**
- `context`: Additional context passed to the LLM kernel
- `name`: Optional name for user messages

## CLI Options

| Option | Required | Description |
|--------|----------|-------------|
| `--input-file` | ✅ | JSON file containing messages and context |
| `--output-file` | ✅ | Output file for LLM response (JSON format) |
| `--schema-file` | ❌ | Pydantic model schema for structured output |
| `--log-level` | ❌ | Logging level: DEBUG, INFO, WARNING, ERROR |

## Examples

### Simple Text Generation

```bash
uv run llm_runner.py \
  --input-file examples/simple-example.json \
  --output-file simple-output.json
```

### PR Review with Context

```bash
uv run llm_runner.py \
  --input-file examples/pr-review-example.json \
  --output-file pr-review-result.json \
  --log-level DEBUG
```

### Minimal Usage (No Context)

```bash
uv run llm_runner.py \
  --input-file examples/minimal-example.json \
  --output-file changelog.json
```

## Output Format

The script outputs JSON with the following structure:

```json
{
  "success": true,
  "response": "LLM response content here",
  "metadata": {
    "runner": "llm_runner.py",
    "timestamp": "auto-generated"
  }
}
```

## CI/CD Integration

### GitHub Actions

```yaml
- name: Install UV
  run: curl -LsSf https://astral.sh/uv/install.sh | sh
  
- name: Generate PR Review
  run: |
    uv run llm_runner.py \
      --input-file .github/pr-context.json \
      --output-file pr-review.json \
      --log-level INFO
  env:
    AZURE_OPENAI_ENDPOINT: ${{ secrets.AZURE_OPENAI_ENDPOINT }}
    AZURE_OPENAI_MODEL: ${{ secrets.AZURE_OPENAI_MODEL }}
```

### Azure DevOps

```yaml
- script: |
    curl -LsSf https://astral.sh/uv/install.sh | sh
  displayName: 'Install UV'
  
- script: |
    uv run llm_runner.py \
      --input-file $(Build.SourcesDirectory)/context.json \
      --output-file $(Build.ArtifactStagingDirectory)/result.json
  displayName: 'Run LLM Task'
  env:
    AZURE_OPENAI_ENDPOINT: $(AZURE_OPENAI_ENDPOINT)
    AZURE_OPENAI_MODEL: $(AZURE_OPENAI_MODEL)
```

## Authentication

The script uses Azure's `DefaultAzureCredential` which supports multiple authentication methods:

1. **Environment variables** (for local development)
2. **Managed Identity** (recommended for Azure-hosted CI/CD)
3. **Azure CLI** (for local development)
4. **Service Principal** (for non-Azure CI/CD)

### Required Azure Permissions

Your identity needs the following permissions on the Azure OpenAI resource:
- `Cognitive Services OpenAI User` role
- Or custom role with `Microsoft.CognitiveServices/accounts/OpenAI/*/read` and `Microsoft.CognitiveServices/accounts/OpenAI/*/action` permissions

## Error Handling

The script uses **simple error handling**:
- ✅ All errors logged to `stderr`
- ✅ Standard Python exceptions (no custom exit codes)
- ✅ CI/CD can use `failOnStdErr` to detect failures
- ✅ Natural failures when input is malformed

## Development

### Running Tests

```bash
# Install development dependencies
uv sync --group dev

# Run unit tests (when implemented)
uv run pytest tests/

# Run with different log levels for debugging
uv run llm_runner.py --input-file examples/simple-example.json --output-file test.json --log-level DEBUG

# Run linting and formatting
uv run ruff check .
uv run ruff format .
uv run mypy llm_runner.py
```

### Extending the Script

The script follows **KISS principles**:
- Easy to understand and modify
- Minimal dependencies
- Clear separation of concerns
- Non-expert friendly

Key extension points:
- `load_schema_model()`: Add custom Pydantic models
- `execute_llm_task()`: Modify LLM execution logic
- Exception classes: Add custom error types

## Use Cases

### Automated Code Review
Generate detailed code reviews for pull requests with security and quality analysis.

### Changelog Generation  
Automatically create changelog entries from commit messages and PR descriptions.

### Documentation Updates
Generate or update documentation based on code changes.

### Release Notes
Create formatted release notes from version control history.

### Security Analysis
Analyze code changes for potential security vulnerabilities.

## Architecture

Built on **Microsoft Semantic Kernel** for:
- Enterprise-ready Azure OpenAI integration
- Future-proof model compatibility
- Extensible plugin system
- Structured output support

## License

MIT License - See LICENSE file for details.

## Support

For issues and questions:
1. Check the examples in the `examples/` directory
2. Review the error logs (beautiful output with Rich!)
3. Validate your Azure authentication and permissions
4. Ensure your input JSON follows the required format 