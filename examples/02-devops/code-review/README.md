# Code Review Automation Example

Automated code review with structured findings and quality gates.

## Files
- `input.json` - The prompt and code changes to review
- `schema.json` - JSON schema for structured code review output
- `README.md` - This documentation

## Usage
```bash
uv run llm_runner.py \
  --input-file examples/02-devops/code-review/input.json \
  --output-file code-review.json \
  --schema-file examples/02-devops/code-review/schema.json \
  --log-level INFO
```

## What This Demonstrates
- Automated code review with structured findings
- Security, performance, and maintainability analysis
- Quality gates and validation
- Specific issue categorization and severity levels
- Test coverage assessment

## Schema Features
- **Issue Categorization**: Security, performance, maintainability, style, bug, logic
- **Severity Levels**: Critical, high, medium, low
- **Line Number References**: Specific code location identification
- **Test Coverage Assessment**: Automated test adequacy evaluation
- **Recommendations**: Actionable improvement suggestions 