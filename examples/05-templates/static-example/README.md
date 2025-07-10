# Static Template Example with Microsoft Semantic Kernel Format

This example demonstrates using **Microsoft Semantic Kernel-compatible** Handlebars templates without external variables - a completely self-contained template for code analysis.

## 📋 **Template Components**

This static example includes two files:

1. **`template.hbs`** - Microsoft-compatible Handlebars template with `<message>` tags (no variables needed)
2. **`schema.yaml`** - YAML schema definition for structured code analysis output

## 🔧 **Template Structure**

### **System Message**
Sets up the AI as a code quality expert:
```handlebars
<message role="system">
You are an expert software engineer with deep knowledge of code quality and best practices.
Your task is to analyze code for potential improvements, bugs, and adherence to coding standards.
Provide constructive feedback that helps developers improve their skills.
</message>
```

### **User Message**  
Contains static analysis request with embedded Python code:
```handlebars
<message role="user">
Please analyze the following code for:
1. Code quality and readability
2. Potential bugs or issues
3. Performance considerations
4. Best practice adherence
5. Suggestions for improvement

```python
def calculate_total(items):
    total = 0
    for item in items:
        if item.price > 0:
            total += item.price * item.quantity
    return total

def process_order(order):
    if order:
        total = calculate_total(order.items)
        if total > 100:
            discount = total * 0.1
            total = total - discount
        return total
    return 0
```

Please provide a structured analysis following the defined schema.
</message>
```

## 🎯 **Schema Validation**

Uses YAML schema for structured code analysis output:

```yaml
$schema: "http://json-schema.org/draft-07/schema#"
type: object
properties:
  code_quality_score:
    type: integer
    minimum: 1
    maximum: 10
    description: "Overall code quality score (1-10)"
  issues_found:
    type: array
    items:
      type: object
      properties:
        type:
          type: string
          enum: ["bug", "performance", "readability", "best_practice", "security"]
        severity:
          type: string
          enum: ["low", "medium", "high", "critical"]
        description:
          type: string
        line_number:
          type: integer
          minimum: 1
        suggestion:
          type: string
      required: ["type", "severity", "description", "suggestion"]
  improvements:
    type: array
    items:
      type: object
      properties:
        category:
          type: string
          enum: ["performance", "readability", "maintainability", "error_handling", "testing"]
        description:
          type: string
        implementation:
          type: string
      required: ["category", "description", "implementation"]
  overall_feedback:
    type: string
    description: "Summary feedback and recommendations"
required: ["code_quality_score", "issues_found", "improvements", "overall_feedback"]
```

## 🚀 **Usage**

Run with template and schema (no variables needed):

```bash
llm-ci-runner \
  --template-file examples/05-templates/static-example/template.hbs \
  --schema-file examples/05-templates/static-example/schema.yaml \
  --output-file code-analysis-result.json
```

**Note**: This example demonstrates that `--template-vars` is optional when templates don't use variables.

## 🔍 **Expected Output**

Generates structured code analysis:

```json
{
  "code_quality_score": 7,
  "issues_found": [
    {
      "type": "performance",
      "severity": "low",
      "description": "Loop could be optimized using sum() and generator expression",
      "line_number": 3,
      "suggestion": "Use: return sum(item.price * item.quantity for item in items if item.price > 0)"
    },
    {
      "type": "readability", 
      "severity": "medium",
      "description": "Magic number 100 should be a named constant",
      "line_number": 12,
      "suggestion": "Define DISCOUNT_THRESHOLD = 100 at module level"
    }
  ],
  "improvements": [
    {
      "category": "error_handling",
      "description": "Add error handling for missing attributes",
      "implementation": "Check if items have 'price' and 'quantity' attributes before accessing"
    },
    {
      "category": "testing",
      "description": "Add unit tests for edge cases",
      "implementation": "Test with empty items list, items with zero/negative prices, None values"
    }
  ],
  "overall_feedback": "Code is functional but could benefit from improved error handling, performance optimization, and better constant management. Consider using more Pythonic approaches for calculations."
}
```

## 💡 **Key Features**

- **Microsoft Semantic Kernel Compatible**: Uses standard `<message>` tag format
- **Self-Contained**: No external variables needed - completely static template
- **Code Analysis Focus**: Specialized for code quality and improvement suggestions
- **Structured Output**: 100% schema-enforced JSON response
- **Embedded Code**: Sample Python code included directly in template
- **Simple Setup**: No variables file required

## 🔧 **When to Use Static Templates**

Static templates are ideal for:
- **Fixed Analysis Scenarios**: When the content doesn't change
- **Demo Purposes**: Showing capabilities without variable complexity
- **Template Testing**: Validating template structure and schema
- **Educational Examples**: Teaching template concepts
- **Baseline Analysis**: Standard code review patterns

## 🆚 **Static vs Variable Templates**

| Static Template | Variable Template |
|----------------|-------------------|
| No external variables needed | Requires `template-vars.yaml` |
| Fixed content | Dynamic content |
| Simpler setup | More flexible |
| Good for demos | Good for production |
| Self-contained | Configurable |

This static template example demonstrates how Microsoft-compatible Handlebars templates can provide comprehensive code analysis without requiring external variable files, making them perfect for fixed-content scenarios. 