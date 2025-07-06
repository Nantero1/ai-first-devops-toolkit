# AI-First DevOps Toolkit: LLM-Powered CI/CD Automation

> **🚀 The Future of DevOps is AI-First**  
> This toolkit represents a step toward [AI-First DevOps](https://technologyworkroom.blogspot.com/2025/06/building-ai-first-devops.html) - where intelligent automation handles the entire development lifecycle. Built for teams ready to embrace the exponential productivity gains of AI-powered development. Please read the blog post for more details on the motivation.

## TLDR: What This Tool Does

**Purpose**: Zero-friction LLM integration for CI/CD pipelines with **100% guaranteed schema compliance**. This is your foundation for AI-first development practices. Basically it takes your input and runs it through your Azure hosted OpenAI LLM, and then returns a JSON output in your desired format.

**Perfect For**:
- 🤖 **AI-Generated Code Reviews**: Automated PR analysis with structured findings
- 📝 **Intelligent Documentation**: Generate changelogs, release notes, and docs automatically  
- 🔍 **Security Analysis**: AI-powered vulnerability detection with structured reports
- 🎯 **Quality Gates**: Enforce standards through AI-driven validation
- 🚀 **Autonomous Development**: Enable AI agents to make decisions in your pipelines
- 🎯 **JIRA Ticket Updates**: Update JIRA tickets based on LLM output
- 🔗 **Unlimited Integration Possibilities**: Chain it multiple times and use as intelligent glue in your tool stack

---

## The AI-First Development Revolution

This toolkit embodies the principles outlined in [Building AI-First DevOps](https://technologyworkroom.blogspot.com/2025/06/building-ai-first-devops.html):

| Traditional DevOps | AI-First DevOps (This Tool) |
|-------------------|----------------------------|
| Manual code reviews | 🤖 AI-powered reviews with structured findings |
| Human-written documentation | 📝 AI-generated docs with guaranteed consistency |
| Reactive security scanning | 🔍 Proactive AI security analysis |
| Manual quality gates | 🎯 AI-driven validation with schema enforcement |
| Linear productivity | 📈 Exponential gains through intelligent automation |

**The Result**: Teams that master AI-first tools like this achieve unprecedented velocity while maintaining enterprise-grade reliability.

## Features

- 🎯 **100% Schema Enforcement**: Token-level constraint enforcement with guaranteed compliance
- 🚀 **Zero-Friction CLI**: Single script, minimal configuration for CI/CD integration
- 🔐 **Enterprise Security**: Azure RBAC via DefaultAzureCredential
- 📋 **Dynamic Schema Support**: Runtime conversion of JSON schemas to Pydantic models
- 🎨 **Beautiful Logging**: Rich console output with timestamps and colors
- 📁 **File-based I/O**: CI/CD friendly with JSON input/output
- 🔧 **Simple & Extensible**: Easy to understand and modify for your specific needs

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
export AZURE_OPENAI_MODEL="gpt-4.1-mini"  # or any other GPT
export AZURE_OPENAI_API_VERSION="2024-12-01-preview"  # Optional
```

If you don't specify an API key, it will run `DefaultAzureCredential` to use RBAC (Role Based Access Control) for authentication (best practice). See [Microsoft Docs](https://learn.microsoft.com/en-us/python/api/azure-identity/azure.identity.defaultazurecredential?view=azure-python) for more details.

Otherwise, you can specify the API key in the environment variable `AZURE_OPENAI_API_KEY`.

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

This format is the same as the one used by the Azure OpenAI API and is passed 1:1 to the `context` of kernel.

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

Basically all [Pydantic](https://docs.pydantic.dev/latest/concepts/schema_validation/) schema features are supported.

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

## CI/CD Pipeline

Our project uses GitHub Actions with UV for fast, reliable CI/CD:

### Automated Checks

Every push and pull request triggers:

- **🧹 Linting**: Ruff code formatting and style checks
- **🔍 Type Checking**: MyPy static type analysis  
- **🧪 Unit Tests**: 69 tests with 100% coverage (unit tests only)
- **🔒 Security**: Dependency vulnerability scanning and secret detection

### Pipeline Features

- **⚡ Fast**: UV caching and parallel job execution
- **🔒 Secure**: Locked dependencies with `uv sync --frozen`
- **📊 Detailed**: JUnit XML test reports with artifact uploads
- **🛡️ Safe**: Auto-mocked API keys prevent accidental real calls

### Local Development

```bash
# Run the same checks locally
uv sync --group dev
uv run ruff check .
uv run ruff format .
uv run mypy llm_runner.py
uv run pytest tests/unit/ -v
```

## Development

### Running Tests

We maintain a comprehensive test suite with **100% coverage** across all functionality:

```bash
# Install development dependencies
uv sync --group dev

# Run all unit tests (69 tests with 100% success rate!)
uv run pytest tests/unit/ -v

# Run integration tests
uv run pytest tests/integration/ -v

# Run acceptance tests (includes LLM-as-judge evaluation)
uv run pytest acceptance/ -v

# Run all tests
uv run pytest tests/ acceptance/ -v

# Run with coverage report
uv run pytest tests/ --cov=llm_runner --cov-report=html

# Run specific test categories
uv run pytest tests/unit/test_schema_functions.py -v          # Schema handling
uv run pytest tests/unit/test_semantic_kernel_functions.py -v # Kernel integration  
uv run pytest tests/unit/test_input_output_functions.py -v    # File I/O
uv run pytest tests/integration/test_examples_integration.py -v # End-to-end examples
```

#### Test Structure

Our test suite follows industry best practices:

- **📁 tests/unit/**: 69 unit tests with heavy mocking (100% pass rate)
  - `test_schema_functions.py`: JSON schema → Pydantic model conversion
  - `test_semantic_kernel_functions.py`: Azure OpenAI integration & ChatHistory
  - `test_input_output_functions.py`: File I/O, CLI parsing, output generation
  - `test_setup_and_utility_functions.py`: Logging, main function, error handling

- **📁 tests/integration/**: End-to-end pipeline testing with realistic mocks
  - `test_examples_integration.py`: All example files with mocked LLM responses
  - `test_cli_interface.py`: Command-line interface testing via subprocess

- **📁 acceptance/**: Production-quality evaluation
  - `llm_as_judge_acceptance_test.py`: LLM-as-judge pattern for response quality

#### Mock Strategy

We use **realistic mocks** based on actual API responses:
- `tests/mock_factory.py`: Factory functions for ChatMessageContent mocks
- Captured from real Azure OpenAI API calls during development
- Includes proper inner_content structure, metadata, and usage statistics

#### Test Features

✅ **Given-When-Then Pattern**: All tests follow this clear structure  
✅ **Realistic Mocks**: Based on actual API response structures  
✅ **Comprehensive Coverage**: Every function and error path tested  
✅ **Retry Logic Testing**: Tenacity decorator behavior validation  
✅ **Schema Enforcement**: KernelBaseModel integration testing  
✅ **CLI Interface**: Subprocess testing for actual command-line behavior  

```bash
# Run with different log levels for debugging
uv run llm_runner.py --input-file examples/simple-example.json --output-file test-output.json --log-level DEBUG

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

## The AI-First Development Journey

This toolkit is your first step toward [AI-First DevOps](https://technologyworkroom.blogspot.com/2025/06/building-ai-first-devops.html). As you integrate AI into your development workflows, you'll experience:

1. **🚀 Exponential Productivity**: AI handles routine tasks while you focus on architecture
2. **🎯 Guaranteed Quality**: Schema enforcement eliminates validation errors
3. **🤖 Autonomous Operations**: AI agents make decisions in your pipelines
4. **📈 Continuous Improvement**: Every interaction improves your AI system

**The future belongs to teams that master AI-first principles.** This toolkit gives you the foundation to start that journey today.

## License

MIT License - See LICENSE file for details.

## Support

For issues and questions:
1. Check the examples in the `examples/` directory
2. Review the error logs (beautiful output with Rich!)
3. Validate your Azure authentication and permissions
4. Ensure your input JSON follows the required format

---

*Ready to embrace the AI-First future? Start with this toolkit and build your path to exponential productivity. Learn more about the AI-First DevOps revolution in [Building AI-First DevOps](https://technologyworkroom.blogspot.com/2025/06/building-ai-first-devops.html).* 