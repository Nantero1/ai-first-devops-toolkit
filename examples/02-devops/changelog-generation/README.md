# Changelog Generation Example

Automated changelog generation from commit history with structured output.

## Files
- `input.json` - The prompt and commit history context
- `schema.json` - JSON schema for structured changelog output
- `README.md` - This documentation

## Usage
```bash
uv run llm_runner.py \
  --input-file examples/02-devops/changelog-generation/input.json \
  --output-file changelog.json \
  --schema-file examples/02-devops/changelog-generation/schema.json \
  --log-level INFO
```

## What This Demonstrates
- Automated changelog generation from git commit history
- Structured categorization of changes (features, bugfixes, breaking changes)
- Version and release date management
- Contributor tracking
- Markdown content generation

## Schema Features
- **Change Categorization**: Features, bugfixes, improvements, breaking changes
- **Version Management**: Semantic versioning support
- **Date Validation**: ISO date format enforcement
- **Content Generation**: Structured markdown output
- **Contributor Tracking**: Author attribution 