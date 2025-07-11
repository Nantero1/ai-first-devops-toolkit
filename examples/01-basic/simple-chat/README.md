# Simple Chat Example

A basic example demonstrating text-only LLM interaction without structured output.

## Files
- `input.json` - The prompt and messages
- `README.md` - This documentation

## Example:

When you use this example, here is what happens step by step:

**Input:**
```json
{
    "messages": [
        {
            "role": "system",
            "content": "You are a helpful assistant that provides concise and informative responses."
        },
        {
            "role": "user",
            "content": "Explain what CI/CD means in software development in one paragraph.",
            "name": "developer"
        }
    ],
    "context": {
        "session_id": "simple-example-001",
        "metadata": {
            "task_type": "explanation",
            "domain": "software_development"
        }
    }
}
```

**Schema:** This example uses free-form text output without schema enforcement.

**Command:**
```bash
llm-ci-runner \
  --input-file examples/01-basic/simple-chat/input.json
```

![Simple chat example](./output.png)

**Output:**
```json
{
  "success": true,
  "response": "CI/CD stands for Continuous Integration and Continuous Deployment (or Continuous Delivery), which are key practices in modern software development. Continuous Integration involves automatically integrating code changes from multiple developers into a shared repository multiple times a day, with automated testing to identify issues early. Continuous Deployment (or Delivery) ensures that these thoroughly tested code changes are automatically deployed to production or made ready for deployment, enabling faster release cycles, increased reliability, and more efficient software delivery. Together, CI/CD streamline the development process, improve code quality, and accelerate time-to-market.",
  "metadata": {
    "runner": "llm-ci-runner",
    "timestamp": "auto-generated"
  }
}
```

## What This Demonstrates
- Basic text-only LLM interaction
- Simple system and user message structure
- No schema enforcement (free-form text output) 