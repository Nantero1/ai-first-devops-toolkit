# Semantic Kernel Structured Analysis Template

This example demonstrates a **Semantic Kernel YAML template** with embedded JSON schema for structured output.
See [Microsoft Semantic Kernel YAML Template Documentation](https://learn.microsoft.com/en-us/semantic-kernel/concepts/prompts/yaml-schema#sample-yaml-prompt)
for more details.

## Files

- `template.yaml` – SK YAML template with embedded JSON schema and model settings
- `template-vars.yaml` – External template variables file with sample text

## Key Features

- **Embedded JSON Schema:** Response format is defined directly in the template YAML under `execution_settings`.
- **Model, Temperature, and Token Control:** You can specify `model_id`, `temperature`, and `max_tokens` directly in the
  template YAML under `execution_settings.azure_openai`. This will overwrite any environment or CLI configuration for
  the model and these parameters.
- **Forced Structured Output:** By setting `response_format.type: json_schema` and providing a schema, the LLM is forced
  to return schema-compliant structured JSON. Unstructured or free-text output is rejected.
- **No External Schema File:** The schema is embedded. Passing `--schema-file` is forbidden and will raise an error.
- **Strict Validation:** Only the fields and types defined in the schema are allowed; required fields are enforced and
  extra fields are rejected.

## Usage

```bash  
# Run structured analysis with template variables (model, temperature, tokens set in YAML)  
uv run python -m llm_ci_runner \  
  --template-file examples/05-templates/sem-ker-structured-analysis/template.yaml \  
  --template-vars examples/05-templates/sem-ker-structured-analysis/template-vars.yaml \  
  --output-file analysis-result.json  
   
# The --schema-file argument is NOT allowed with SK YAML templates.  
# This will cause an error:  
# uv run python -m llm_ci_runner \  
#   --template-file examples/05-templates/sem-ker-structured-analysis/template.yaml \  
#   --schema-file schema.json  # ❌ ERROR: SK YAML embeds schema  
```  

## Template Structure

The SK YAML template includes:

- **Model/Temperature/Max Tokens:**
  ```yaml  
  execution_settings:  
    azure_openai:  
      model_id: gpt-4.1-stable  
      temperature: 0.3  
      max_tokens: 800  
      response_format:  
        type: json_schema  
        json_schema:  
          schema: ...  
  ```  
- **Embedded Schema:** JSON schema in `execution_settings.response_format.json_schema.schema`
- **Schema Properties:** Defines fields like `sentiment`, `confidence`, `key_themes`, `summary`, `word_count`
- **Required Fields:** Enforces fields such as `sentiment`, `confidence`, and `summary`
- **Type Constraints:** Ensures correct types and value ranges
- **Strict Output:** `additionalProperties: false` for strict compliance

## Expected Output Format

```json  
{
  "sentiment": "positive",
  "confidence": 0.75,
  "key_themes": [
    "CI/CD",
    "deployment",
    "team concerns"
  ],
  "summary": "Analysis of CI/CD pipeline implementation impact",
  "word_count": 85
}  
```  

## Integration Testing

This example is automatically discovered by acceptance tests and used for validating SK YAML templates with embedded
schemas and strict structured output.