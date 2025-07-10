# Acceptance Testing Framework: LLM-as-Judge Quality Assessment

> **🎯 Purpose**: Validate LLM output quality using AI itself as the judge - a critical component of AI-First DevOps quality gates.

## Overview

This acceptance testing framework implements the **LLM-as-Judge pattern** to evaluate the quality of AI-generated outputs. Unlike traditional testing that only validates technical correctness (schema compliance, execution success), this framework assesses the **intellectual quality** of LLM responses using another AI model as the evaluator.

## Why LLM-as-Judge Testing?

### The Challenge of Non-Deterministic AI

Traditional software testing assumes deterministic behavior - the same input always produces the same output. However, **LLMs are inherently non-deterministic**:

- **Stochastic responses**: Same prompt can produce different outputs
- **Quality variance**: Responses can be technically correct but qualitatively poor
- **Context sensitivity**: Performance varies based on input complexity
- **Hallucination risk**: Factually incorrect but syntactically valid responses

### The AI-First DevOps Imperative

As outlined in [Building AI-First DevOps](https://technologyworkroom.blogspot.com/2025/06/building-ai-first-devops.html), AI-First development requires **quality gates for AI-generated code** and **continuous validation** of AI system behavior. Traditional testing approaches are insufficient for AI-powered systems.

> "AI systems behave chaotically, and it is important to monitor the AI system's behavior, performance, and quality. Another AI system must be able to detect anomalies and unexpected behavior in real-time and fix them automatically." - [Building AI-First DevOps](https://technologyworkroom.blogspot.com/2025/06/building-ai-first-devops.html)

## How LLM-as-Judge Works

### The Pattern

1. **Execute**: Run your LLM with a specific input
2. **Judge**: Use another LLM call to evaluate the response quality
3. **Score**: Assign numerical scores across multiple dimensions
4. **Gate**: Pass/fail based on quality thresholds

### Example: Sentiment Analysis Quality Assessment

```python
# Original LLM Response
{
  "sentiment": "positive",
  "confidence": 0.85,
  "key_points": ["clear communication", "professional tone"],
  "summary": "The text expresses positive sentiment with confidence."
}

# LLM-as-Judge Evaluation
{
  "relevance": 9,
  "accuracy": 8,
  "completeness": 7,
  "clarity": 9,
  "overall": 8,
  "pass": true,
  "strengths": ["Accurate sentiment detection", "Clear confidence scoring"],
  "weaknesses": ["Could include more specific examples"],
  "reasoning": "Response demonstrates good understanding of sentiment analysis..."
}
```

## Testing Modes

### 🚀 Smoke Test Mode (Fast & cheaper)
```bash
uv run pytest acceptance/ --smoke-test
```

**What it tests:**
- ✅ Execution reliability (does it run?)
- ✅ Schema compliance (follows JSON schema?)
- ✅ Basic output structure validation

**What it skips:**
- ❌ LLM-as-judge quality assessment
- ❌ Additional LLM API calls for quality assesement

**Use case:** Development iterations, CI/CD validation, cost-conscious testing

### 🎯 Full Quality Testing (Comprehensive)
```bash
uv run pytest acceptance/
```

**What it tests:**
- ✅ Everything from smoke testing
- ✅ LLM-as-judge quality assessment
- ✅ Custom scenario testing
- ✅ Extensibility demonstrations

**Use case:** Production quality gates, comprehensive validation, quality assurance

## Test Structure

### Auto-Discovered Examples
The framework automatically discovers and tests all examples in the `examples/` folder:

```
examples/
├── 01-basic/sentiment-analysis/     # ✅ Auto-tested (JSON mode)
├── 02-devops/code-review/           # ✅ Auto-tested (JSON mode)  
├── 03-security/vulnerability-analysis/ # ✅ Auto-tested (JSON mode)
├── 04-ai-first/autonomous-development-plan/ # ✅ Auto-tested (JSON mode)
└── 05-templates/
    ├── jinja2-example/              # ✅ Auto-tested (Jinja2 template)
    ├── static-example/               # ✅ Auto-tested (Handlebars template)
    └── pr-review-template/           # ✅ Auto-tested (Handlebars template)
```

**Discovery Priority:**
1. **JSON Examples** (Priority): Folders containing `input.json` files
2. **Template Examples** (Fallback): Folders containing `template.*` files (`.hbs`, `.jinja`, `.j2`)

**Template Support:**
- **Handlebars**: `.hbs` files with `{{ variable }}` syntax
- **Jinja2**: `.jinja` and `.j2` files with `{{ variable }}` and `{% control %}` syntax
- **Schema Validation**: Requires `schema.yaml` or `schema.json` for template examples
- **Template Variables**: Optional `template-vars.yaml` or `template-vars.json` files

### Comprehensive Test Flow
Each example undergoes a **single execution** with multiple validation phases:

```python
async def test_example_comprehensive():
    # Phase 1: Execute example ONCE
    result = execute_example()
    
    # Phase 2: Reliability validation (always)
    validate_execution_success()
    
    # Phase 3: Schema compliance (if schema exists)
    if schema_file:
        validate_schema_compliance()
    
    # Phase 4: Quality assessment (if not smoke test)
    if not smoke_test_mode:
        evaluate_with_llm_judge()  # Based on example type
```

### Intelligent Quality Assessment
Different examples are evaluated using **type-specific criteria**:

| Example Type | Quality Criteria | Min Score |
|--------------|------------------|-----------|
| **Sentiment Analysis** | Accuracy, confidence scores, key points | 7/10 |
| **Code Review** | Technical analysis, security, feedback | 8/10 |
| **Vulnerability Analysis** | Risk assessment, remediation steps | 8/10 |
| **PR Descriptions** | Clear summaries, impact analysis | 7/10 |
| **Changelog Generation** | Structured entries, categorization | 7/10 |
| **Autonomous Development** | Comprehensive planning, quality gates | 8/10 |
| **Template Examples** | Output quality, schema compliance, template features | 7/10 |

## Real-World Example: LLM-as-Judge in Action

![LLM-as-Judge Test Results](llm_as_a_judge.png)

*Above: An example where LLM-as-judge correctly identified quality issues despite schema compliance. The response was technically valid but qualitatively poor, demonstrating why traditional testing alone is insufficient for AI systems.*

## Integration with AI-First DevOps

### Quality Gates for AI-Generated Code
This framework implements the quality gates mentioned in [Building AI-First DevOps](https://technologyworkroom.blogspot.com/2025/06/building-ai-first-devops.html):

> "Good quality gates are a must, to build trust for the overall AI system."

### Continuous AI System Monitoring
The framework supports the continuous monitoring requirements for AI systems:

- **Real-time quality assessment**
- **Anomaly detection** in LLM behavior
- **Automated quality gates** for deployment
- **Performance tracking** over time

### Metrics for AI Systems
Following the metrics outlined in the AI-First DevOps guide:

- **Truthfulness**: LLM-as-judge evaluates factual accuracy
- **Relevance**: Response relevance to input query
- **Precision**: Quality of specific details provided
- **Recall**: Completeness of response coverage

## Best Practices

### 1. Use Smoke Tests for Development
```bash
# Fast feedback during development
uv run pytest acceptance/ --smoke-test
```

### 2. Full Testing for Quality Gates
```bash
# Comprehensive validation before deployment
uv run pytest acceptance/
```

### 3. Monitor Quality Trends
Track LLM-as-judge scores over time to identify:
- Performance degradation
- Model drift
- Quality improvements

### 4. Customize Evaluation Criteria
Extend `_get_evaluation_criteria()` for domain-specific quality assessment.

### 5. Set Appropriate Thresholds
Adjust minimum scores based on:
- Example complexity
- Business criticality
- Risk tolerance

## Extending the Framework

### Adding New Examples
1. **JSON Examples**: Create folder in `examples/` with `input.json`
2. **Template Examples**: Create folder in `examples/` with `template.*` file (`.hbs`, `.jinja`, `.j2`)
3. **Schema Validation**: Optionally add `schema.json` or `schema.yaml` for structured output
4. **Template Variables**: For template examples, optionally add `template-vars.yaml` or `template-vars.json`
5. Framework auto-discovers and tests all examples

### Custom Quality Criteria
```python
def _get_evaluation_criteria(self, example_name: str) -> str:
    if "your-domain" in example_name.lower():
        return """
        - Should demonstrate domain expertise
        - Should provide actionable insights
        - Should follow industry best practices
        """
```

### Custom Scenarios
Add new test classes in `TestCustomScenarios` for specialized validation.

## Environment Setup

### Required Environment Variables
```bash
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_MODEL="gpt-4.1-nano"
export AZURE_OPENAI_API_KEY="your-api-key"
```

### Authentication Options
- **RBAC (Recommended)**: Uses `DefaultAzureCredential` for Azure RBAC
- **API Key**: Set `AZURE_OPENAI_API_KEY` for direct authentication

## Troubleshooting

### Common Issues

**"Missing environment variables"**
- Set required Azure OpenAI environment variables
- Set env var `AZURE_OPENAI_API_KEY` to disable Azure RBAC and use simple API key authentication.

**"LLM-as-judge evaluation failed"**
- Try again, its undeterministic, what is you failure percentage?
- Review Prompts, be more specific
- Prompt engineering is an art...

**"Schema validation failed"**
- Check JSON schema syntax
- Verify required fields are present
- Review constraint definitions

### Debug Mode
```bash
# Enable detailed logging
uv run pytest acceptance/ --log-cli-level=DEBUG
```

## Conclusion

This acceptance testing framework represents a **fundamental shift** in how we validate AI-powered systems. By using AI to judge AI, we create a **self-improving quality system** that adapts to the non-deterministic nature of LLMs.

As [Building AI-First DevOps](https://technologyworkroom.blogspot.com/2025/06/building-ai-first-devops.html) emphasizes:

> "The companies that master this transition will define the next era of software (and business) innovation."

This framework is your foundation for building **trustworthy, high-quality AI systems** that can operate autonomously while maintaining the quality standards required for production deployment.

---

*For more information on AI-First DevOps principles, see [Building AI-First DevOps](https://technologyworkroom.blogspot.com/2025/06/building-ai-first-devops.html).* 