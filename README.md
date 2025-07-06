# LLM Runner - CI/CD LLM Utilities

A simple, zero-friction utility for running LLM-driven tasks in CI/CD pipelines using Microsoft Semantic Kernel.

## Features

- 🚀 **Zero-friction CLI**: Single script, minimal configuration
- 🔐 **Enterprise security**: Azure RBAC via DefaultAzureCredential
- 🎯 **100% Schema Enforcement**: Token-level constraint enforcement with guaranteed compliance
- 📋 **Dynamic Schema Support**: Runtime conversion of JSON schemas to Pydantic models
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
| `--schema-file` | ❌ | **JSON schema file for 100% enforcement** (see Structured Outputs) |
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

## Structured Outputs with 100% Schema Enforcement

The LLM Runner provides **guaranteed schema compliance** through token-level constraint enforcement using Semantic Kernel's KernelBaseModel integration.

### How It Works

When you provide a `--schema-file`, the runner:

1. **Converts JSON Schema → Pydantic Model**: Runtime conversion using `create_dynamic_model_from_schema()`
2. **Enables Token-Level Constraints**: Uses `settings.response_format = ModelClass` 
3. **Guarantees 100% Compliance**: Azure OpenAI's structured outputs enforce schema at generation time
4. **Validates All Constraints**: Enums, ranges, array limits, string lengths, required fields

### Creating a Schema File

Create a JSON schema file with your desired structure:

```json
{
  "type": "object",
  "properties": {
    "sentiment": {
      "type": "string",
      "enum": ["positive", "negative", "neutral"],
      "description": "Overall sentiment of the content"
    },
    "confidence": {
      "type": "number",
      "minimum": 0,
      "maximum": 1,
      "description": "Confidence score (0-1)"
    },
    "key_points": {
      "type": "array",
      "items": {"type": "string"},
      "minItems": 1,
      "maxItems": 5,
      "description": "Main points (1-5 items)"
    },
    "summary": {
      "type": "string",
      "maxLength": 200,
      "description": "Brief summary (max 200 chars)"
    }
  },
  "required": ["sentiment", "confidence", "key_points", "summary"],
  "additionalProperties": false
}
```

### Using Structured Output

```bash
uv run llm_runner.py \
  --input-file sentiment-input.json \
  --output-file sentiment-output.json \
  --schema-file sentiment-schema.json \
  --log-level INFO
```

### Supported Schema Features

✅ **String Constraints**: `enum`, `minLength`, `maxLength`, `pattern`  
✅ **Numeric Constraints**: `minimum`, `maximum`, `multipleOf`  
✅ **Array Constraints**: `minItems`, `maxItems`, `items` type  
✅ **Required Fields**: Enforced at generation time  
✅ **Type Validation**: `string`, `number`, `integer`, `boolean`, `array`  
✅ **Enum Validation**: Strict enum compliance  

### Example: Sentiment Analysis

**Input** (`sentiment-input.json`):
```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are a sentiment analysis assistant."
    },
    {
      "role": "user",
      "content": "Analyze: 'I love this new feature! It works perfectly but documentation could be better.'"
    }
  ]
}
```

**Output** (guaranteed schema compliance):
```json
{
  "success": true,
  "response": {
    "sentiment": "positive",
    "confidence": 0.85,
    "key_points": [
      "Love for new feature",
      "Works perfectly", 
      "Documentation needs improvement"
    ],
    "summary": "User loves the feature's functionality but wants better documentation."
  }
}
```

**🎯 Key Benefits:**
- **No Schema Violations**: 100% guaranteed compliance
- **Production Ready**: Eliminates validation errors in CI/CD
- **Dynamic**: Works with any JSON schema
- **Comprehensive**: Supports all standard JSON schema features

## Output Format

The script always outputs JSON with the following structure:

### Text Output (No Schema)
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

### Structured Output (With Schema)
```json
{
  "success": true,
  "response": {
    "field1": "value1",
    "field2": 42,
    "field3": ["item1", "item2"]
  },
  "metadata": {
    "runner": "llm_runner.py",
    "timestamp": "auto-generated"
  }
}
```

**Key Points:**
- `success`: Always `true` for successful executions
- `response`: Contains either text string or structured object based on schema
- `metadata`: Runner information and timestamp
- **Schema enforcement**: When using `--schema-file`, `response` is guaranteed to match the schema exactly

## CI/CD Integration

### GitHub Actions

```yaml
- name: Install UV
  run: curl -LsSf https://astral.sh/uv/install.sh | sh
  
- name: Generate PR Review with Schema Enforcement
  run: |
    uv run llm_runner.py \
      --input-file .github/pr-context.json \
      --output-file pr-review.json \
      --schema-file .github/pr-review-schema.json \
      --log-level INFO
  env:
    AZURE_OPENAI_ENDPOINT: ${{ secrets.AZURE_OPENAI_ENDPOINT }}
    AZURE_OPENAI_MODEL: ${{ secrets.AZURE_OPENAI_MODEL }}

- name: Process Structured Results
  run: |
    # Extract specific fields from guaranteed schema-compliant output
    RISK_LEVEL=$(jq -r '.response.risk_level' pr-review.json)
    ISSUES_COUNT=$(jq -r '.response.issues | length' pr-review.json)
    echo "Risk Level: $RISK_LEVEL"
    echo "Issues Found: $ISSUES_COUNT"
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
- `create_dynamic_model_from_schema()`: Extend JSON schema → Pydantic model conversion
- `_convert_json_schema_field()`: Add support for custom JSON schema types
- `execute_llm_task()`: Modify LLM execution logic
- Exception classes: Add custom error types (`SchemaValidationError`, etc.)

## Use Cases

### Automated Code Review with Structured Output
Generate detailed code reviews with **guaranteed schema compliance** for CI/CD integration:
```json
{
  "risk_level": "medium",
  "issues_found": 3,
  "security_concerns": ["potential XSS vulnerability"],
  "recommendations": ["add input validation", "use parameterized queries"],
  "approval_status": "requires_changes"
}
```

### Changelog Generation with Schema Enforcement
Automatically create changelog entries with consistent structure:
```json
{
  "version": "1.2.0",
  "release_date": "2024-01-15",
  "changes": {
    "features": ["new authentication system"],
    "bugfixes": ["fixed memory leak in parser"],
    "breaking_changes": []
  }
}
```

### Documentation Updates
Generate or update documentation based on code changes.

### Release Notes with Structured Metadata
Create formatted release notes with guaranteed schema compliance for automated processing.

### Security Analysis with Structured Results
Analyze code changes for potential security vulnerabilities with structured findings that can be processed by security tools and dashboards.

## Architecture

Built on **Microsoft Semantic Kernel** for:
- Enterprise-ready Azure OpenAI integration
- Future-proof model compatibility
- Extensible plugin system
- **100% Schema Enforcement**: KernelBaseModel integration with token-level constraints
- **Dynamic Model Creation**: Runtime JSON schema → Pydantic model conversion

## License

MIT License - See LICENSE file for details.

## Support

For issues and questions:
1. Check the examples in the `examples/` directory
2. Review the error logs (beautiful output with Rich!)
3. Validate your Azure authentication and permissions
4. Ensure your input JSON follows the required format 