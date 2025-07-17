# Release Notes Generation Example

Simple and direct release notes generation from commit history using LLM-powered analysis.

## Files
- `template.hbs` - Handlebars template for release notes generation
- `template-vars.yaml` - Example template variables for testing
- `README.md` - This documentation

## Purpose

This example demonstrates how to use the LLM CI Runner to automatically generate professional release notes from git commit history. The approach is simple and direct:

- **Direct text output**: No complex schema, just clean markdown
- **Manual instructions**: Optional additional context from user input
- **Professional formatting**: Consistent with project release notes standards
- **KISS principle**: Keep it simple and straightforward

## Template Variables

The template expects the following variables:

```yaml
version: "1.2.2"                    # Version being released
previous_version: "v1.2.1"          # Previous version tag
manual_instructions: "Optional..."   # Additional context (optional)
commit_history: "git log output"     # Commit history between tags
changed_files: "git diff output"     # Changed files list
commit_count: 3                      # Number of commits
```

## Usage

### Manual Testing
```bash
# Test the template with example data
llm-ci-runner \
  --template-file examples/05-templates/release-notes/template.hbs \
  --template-vars examples/05-templates/release-notes/template-vars.yaml \
  --output-file release-notes.md
```

### In GitHub Actions
```yaml
- name: Generate Release Notes
  run: |
    llm-ci-runner \
      --template-file examples/05-templates/release-notes/template.hbs \
      --template-vars template-vars.yaml \
      --output-file release-notes.md
  env:
    AZURE_OPENAI_ENDPOINT: ${{ secrets.AZURE_OPENAI_ENDPOINT }}
    AZURE_OPENAI_MODEL: ${{ secrets.AZURE_OPENAI_MODEL }}
```

## Template Features

### Simple and Direct
- **Direct markdown output**: No complex schema, just clean text
- **Manual instructions**: Optional additional context from user input
- **Professional formatting**: Consistent emoji usage and markdown structure
- **Conditional sections**: Only includes sections that have content

### Professional Formatting
- Consistent emoji usage for each section
- Proper markdown formatting
- Installation instructions
- Links to project resources

## Integration with Release Workflow

This template is designed to integrate with the GitHub Actions release workflow:

1. **Extract commit history** between tags
2. **Generate template variables** from git data
3. **Run LLM analysis** to generate release notes
4. **Use direct markdown output** in GitHub release creation

## Example Output

```markdown
# Release Notes v1.2.2

## 🔧 Improvements
- **Logging Configuration**: Enhanced logging configuration for Azure libraries with improved production experience
- **Documentation**: Standardized runner script naming across all documentation for consistency

## 📚 Documentation
- Updated all instances of `llm_ci_runner.py` to `llm-ci-runner` in README files and usage examples
- Enhanced logging configuration documentation with better visibility in production environments

---

**Breaking Changes**: None
**Migration**: No migration required
**Installation**: `pip install llm-ci-runner==1.2.2`

## 🔗 Links
- [Documentation](https://github.com/Nantero1/ai-first-devops-toolkit)
- [Issues](https://github.com/Nantero1/ai-first-devops-toolkit/issues)
- [Source Code](https://github.com/Nantero1/ai-first-devops-toolkit)

## Changelog

For detailed changes, see the [commit history](https://github.com/Nantero1/ai-first-devops-toolkit/compare/v1.2.1...v1.2.2).
```

## Benefits

- **Simple**: Direct markdown output, no complex schema
- **Automated**: No manual release notes writing required
- **Consistent**: Follows project standards and formatting
- **Professional**: Suitable for public releases
- **Flexible**: Supports manual additions when needed 