# Static Template Example

This example demonstrates using **Handlebars templates without template variables** - showing that the `--template-vars` parameter is **optional**.

## 🎯 Key Feature Demonstrated

- **Optional Template Variables**: Templates can be completely static without requiring external variables
- **Simplified Usage**: No need for template variables when the template is self-contained
- **Static Content**: Perfect for standardized prompts that don't change

## Files

- `template.hbs` - Static Handlebars template (no variables needed)
- `schema.yaml` - YAML schema defining the expected output structure
- `README.md` - This documentation

## How It Works

### Static Template Approach

This template is **completely self-contained** and doesn't require any external variables:

```handlebars
{{#message role="system"}}
You are an expert software engineer with deep knowledge of code quality and best practices.
Your task is to analyze code for potential improvements, bugs, and adherence to coding standards.
{{/message}}

{{#message role="user"}}
Please analyze the following code for:
1. Code quality and readability
2. Potential bugs or issues
3. Performance considerations
4. Best practice adherence
5. Suggestions for improvement

[... static code example ...]
{{/message}}
```

**Notice**: No `{{variables}}` are used - the template contains all the content it needs.

## Usage

### Command (No Template Variables)

```bash
llm-ci-runner \
  --template-file examples/05-templates/static-example/template.hbs \
  --schema-file examples/05-templates/static-example/schema.yaml \
  --output-file code-analysis-result.yaml
```

**Key Point**: No `--template-vars` parameter needed!

### Alternative with JSON Schema

```bash
# Convert YAML schema to JSON if preferred
cat examples/05-templates/static-example/schema.yaml | yq eval -o json > schema.json

llm-ci-runner \
  --template-file examples/05-templates/static-example/template.hbs \
  --schema-file schema.json \
  --output-file code-analysis-result.json
```

## When to Use Static Templates

### ✅ **Perfect For**
- **Standardized Analysis**: Code reviews, security scans, quality checks
- **Fixed Prompts**: When the prompt content doesn't change between runs
- **Simple Workflows**: No dynamic content needed
- **Consistent Output**: Same analysis criteria every time

### 🔄 **Compare with Variable Templates**
- **Static Template**: Fixed content, no external data needed
- **Variable Template**: Dynamic content based on context (PR info, user data, etc.)

## Example Scenarios

### 1. Code Quality Analysis
```bash
# Analyze any code with the same criteria
llm-ci-runner --template-file code-quality-template.hbs --schema-file quality-schema.yaml
```

### 2. Security Review
```bash  
# Standard security checklist
llm-ci-runner --template-file security-review-template.hbs --schema-file security-schema.yaml
```

### 3. Documentation Review
```bash
# Consistent documentation standards
llm-ci-runner --template-file doc-review-template.hbs --schema-file doc-schema.yaml
```

## Expected Output

The command generates structured output following the YAML schema:

```yaml
success: true
response:
  quality_score: 7
  analysis:
    readability: "good"
    maintainability: "fair" 
    performance: "good"
  issues:
    - severity: "medium"
      description: "Missing input validation for items parameter"
      location: "calculate_total function"
    - severity: "low"
      description: "Magic number 0.1 should be a named constant"
      location: "process_order function"
  suggestions:
    - category: "best_practice"
      description: "Add input validation and type hints for better code safety"
      impact: "medium"
      code_example: "def calculate_total(items: List[Item]) -> float:"
    - category: "maintainability"
      description: "Extract discount rate to a named constant"
      impact: "low"
      code_example: "DISCOUNT_RATE = 0.1"
```

## Benefits of Static Templates

### 🎯 **Simplicity**
- No external configuration files needed
- Single template file contains everything
- Easier to version control and share

### 🔒 **Consistency**
- Same analysis criteria every time
- No risk of missing or incorrect variables
- Standardized output across all runs

### 🚀 **Performance**
- No variable loading or processing overhead
- Faster template rendering
- Simpler CI/CD integration

### 📋 **Maintenance**
- Template is self-documenting
- No variable dependencies to track
- Easier to understand and modify

## Integration with CI/CD

Perfect for automated quality gates:

```yaml
# GitHub Actions example
- name: Code Quality Analysis
  run: |
    llm-ci-runner \
      --template-file .github/templates/code-quality.hbs \
      --schema-file .github/schemas/quality.yaml \
      --output-file quality-report.yaml
      
- name: Check Quality Score
  run: |
    SCORE=$(yq eval '.response.quality_score' quality-report.yaml)
    if [ "$SCORE" -lt 7 ]; then
      echo "❌ Code quality score too low: $SCORE"
      exit 1
    fi
```

## What This Demonstrates

- 📝 **Optional Template Variables**: `--template-vars` is not required
- 🎯 **Static Content Templates**: Self-contained templates work perfectly
- ✅ **Schema Enforcement**: Still get 100% schema compliance
- 🔧 **Simplified Usage**: Fewer command-line parameters needed
- 🚀 **CI/CD Integration**: Perfect for standardized automated workflows 