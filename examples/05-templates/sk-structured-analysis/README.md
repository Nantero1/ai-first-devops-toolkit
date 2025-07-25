# Semantic Kernel Structured Analysis Template

This example demonstrates a Semantic Kernel YAML template with embedded JSON schema for structured output. For a more detailed explanation, see [Microsoft Semantic Kernel YAML Template Documentation](https://learn.microsoft.com/en-us/semantic-kernel/concepts/prompts/yaml-schema#sample-yaml-prompt).

## Files

- `template.yaml` - SK YAML template with embedded JSON schema for structured responses
- `template-vars.yaml` - External template variables file with sample text

## Key Features

- **Embedded JSON Schema**: Response format defined directly in the template
- **Structured Output**: Guarantees JSON response with specific properties
- **Schema Validation**: Automatic validation of LLM responses against schema
- **Required Properties**: Enforces required fields like sentiment, confidence, summary
- **Type Safety**: Ensures correct data types (string, number, array, etc.)
- **No External Schema File**: Schema is embedded, `--schema-file` is forbidden

## Usage

```bash
# Run structured analysis with template variables
uv run python -m llm_ci_runner \
  --template-file examples/05-templates/sk-structured-analysis/template.yaml \
  --template-vars examples/05-templates/sk-structured-analysis/template-vars.yaml \
  --output-file analysis-result.json

# The --schema-file argument is NOT allowed with SK YAML templates
# This will cause an error:
# uv run python -m llm_ci_runner \
#   --template-file examples/05-templates/sk-structured-analysis/template.yaml \
#   --schema-file schema.json  # ❌ ERROR: SK YAML embeds schema
```

## Template Structure

The SK YAML template includes:
- **Embedded Schema**: JSON schema in `execution_settings.response_format.json_schema.schema`
- **Schema Properties**: Defines sentiment, confidence, key_themes, summary, word_count
- **Required Fields**: Enforces sentiment, confidence, and summary as mandatory
- **Type Constraints**: Ensures proper data types and value ranges
- **Additional Properties**: Set to false for strict schema compliance

## Expected Output Format

```json
{
  "sentiment": "positive",
  "confidence": 0.75,
  "key_themes": ["CI/CD", "deployment", "team concerns"],
  "summary": "Analysis of CI/CD pipeline implementation impact",
  "word_count": 85
}
```

## Integration Testing

This example is automatically discovered by acceptance tests and used for testing SK YAML templates with embedded schemas and structured output validation.
