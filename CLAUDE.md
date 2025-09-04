# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Essential Development Commands

```bash
# Primary workflow - runs format, lint, security, type-check, tests
./scripts/check.sh

# Individual commands
uv sync --group dev --upgrade           # Install/update dependencies
uv run ruff format .                    # Format code
uv run ruff check --fix llm_ci_runner/  # Lint and auto-fix
uv run mypy llm_ci_runner/              # Type checking
uv run pip-audit                        # Security scan
uv run pytest tests/                    # Unit tests (70+ tests)
uv run pytest acceptance/ -s -v --smoke-test  # Acceptance tests

# Build and publish
uv build                                # Build package
uv run twine upload dist/*              # Publish to PyPI

# Coverage (85% minimum required)
pytest tests/ --cov=llm_ci_runner --cov-report=html
```

## High-Level Architecture

### Core Design
- **Library-first**: Python library with CLI wrapper for both programmatic and command-line usage
- **Template-driven**: Three engines (Handlebars, Jinja2, Semantic Kernel YAML)
- **Schema-enforced**: 100% JSON Schema compliance via runtime Pydantic models
- **Enterprise auth**: Azure RBAC (DefaultAzureCredential) with API key fallback

### Key Components

```
llm_ci_runner/
├── core.py           # Main orchestration, CLI entry, unified interface
├── templates.py      # Multi-format template processing
├── llm_service.py    # Semantic Kernel integration, auth setup
├── llm_execution.py  # LLM task execution with validation
├── schema.py         # JSON Schema to Pydantic conversion
├── io_operations.py  # File I/O, argument parsing
├── formatters.py     # Output formatting (JSON/YAML/Markdown)
├── retry.py          # Network resilience (exponential backoff)
└── exceptions.py     # Error hierarchy
```

### Data Flow
1. **Input**: Load JSON/YAML or template files
2. **Template Resolution**: Process .hbs/.j2/.yaml templates
3. **Auth**: Azure OpenAI (RBAC/key) or OpenAI fallback
4. **Execution**: LLM with optional schema validation
5. **Output**: Formatted results to file/console

## Template System

### Semantic Kernel YAML (Preferred for complex cases)
```yaml
template: "Analyze: {{$text}}"
input_variables:
  - name: text
execution_settings:
  azure_openai:
    model_id: "gpt-4"  # Dynamic model selection
    temperature: 0.1
    response_format:
      type: json_schema
      json_schema:
        schema: {...}  # Embedded schema
```

### Handlebars/Jinja2
- External schema files
- YAML variable files
- Simple prompt generation

### Variable Resolution Priority
1. `template_vars` dict
2. `template_vars` string (file path)
3. `template_vars_file` parameter
4. Empty dict fallback

## Library vs CLI Usage

### Library (Python)
```python
from llm_ci_runner.core import run_llm_task

# String template
response = await run_llm_task(
    template_content="Analyze: {{input}}",
    template_format="handlebars",
    template_vars={"input": data},
    schema={"type": "object", ...}
)

# File template
response = await run_llm_task(
    template_file="template.yaml",
    template_vars_file="vars.yaml",
    schema_file="schema.json"
)
```

### CLI
```bash
llm-ci-runner \
  --template-file template.yaml \
  --template-vars vars.yaml \
  --schema-file schema.json \
  --output-file result.json
```

## Development Patterns

### Cursor Rules Integration
- **Plan Mode**: Requirements gathering, 95%+ confidence before execution
- **Agent Mode**: Code modifications with system changes
- **Documentation**: Update `.cursor/memories.md` and lessons learned `.cursor/rules/lessons-learned.mdc` when asked

### Code Style
- Google Python Style Guide + PEP 8, 120 char lines
- Every class must document its PURPOSE
- Given-When-Then test structure (mandatory)
- Keep all comments, never remove
- Use specific exceptions with fallbacks

### Testing Pattern
```python
def test_functionality(self):
    """Test description."""
    # given
    input_data = "test"
    
    # when
    result = component.process(input_data)
    
    # then
    assert result == "expected"
```

### Exception Hierarchy
```
LLMRunnerError
├── InputValidationError
├── AuthenticationError
├── LLMExecutionError
└── SchemaValidationError
```

## Authentication

### Azure OpenAI (Priority)
```bash
AZURE_OPENAI_ENDPOINT="https://resource.openai.azure.com/"
AZURE_OPENAI_MODEL="gpt-4"              # Default deployment
AZURE_OPENAI_API_KEY="key"              # Optional (uses RBAC if not set)
```

### OpenAI (Fallback)
```bash
OPENAI_API_KEY="sk-..."
OPENAI_CHAT_MODEL_ID="gpt-4"
```

## CI/CD Integration

### GitHub Actions Pipeline
- Parallel jobs: lint, type-check, test, security
- 85% coverage requirement
- Automatic PyPI publishing on release
- LLM-as-judge acceptance tests

### Quality Gates
1. All tests pass
2. 85%+ coverage
3. No type errors (mypy strict)
4. No vulnerabilities (pip-audit)
5. Code formatted (ruff)

## Important Context

### Semantic Kernel Foundation
- `KernelBaseModel` for schema enforcement
- `KernelFunctionFromPrompt` for YAML templates
- Automatic credential cleanup
- Async throughout with proper error handling

### Recent Decisions
- json-schema-to-pydantic for schema conversion
- py-cov-action for coverage reporting
- Smoke test mode for faster CI
- Auto-discovery for example tests

### Performance
- Retry with exponential backoff and jitter
- Connection pooling for Azure
- Async I/O operations
- Minimal dependency startup

## Common Tasks

### Add Template Format
1. Extend `templates.py`
2. Update `process_template()`
3. Add example in `examples/05-templates/`
4. Auto-discovered by tests

### Create Example
1. Create folder in `examples/XX-category/`
2. Add `input.json`, `schema.json`, `README.md`
3. Tests auto-generated via discovery

### Debug LLM Issues
- Check Azure auth: `az account show`
- Enable debug logging in `logging_config.py`
- Validate schemas: `pytest tests/test_schema.py`

## Key Development Principles

1. **Maintain backward compatibility** - Stable API with many users
2. **Template-first philosophy** - Templates primary, direct messages secondary
3. **Schema enforcement** - Never bypass validation
4. **Use existing patterns** - Check memories.md and examples first
5. **Test everything** - Comprehensive coverage required
6. **Document PURPOSE** - Why it exists, not just what it does