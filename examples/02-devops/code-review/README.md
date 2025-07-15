# Code Review Automation Example

Automated code review with structured findings and quality gates.

## Files
- `input.json` - The prompt and code changes to review
- `schema.json` - JSON schema for structured code review output
- `README.md` - This documentation

## Example:

When you use this example, here is what happens step by step:

**Input:**
```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are a senior software engineer conducting code reviews.\n"
                 "Focus on code quality, best practices, security, performance, and maintainability."
    },
    {
      "role": "user",
      "content": "Review this code for quality, security, and best practices:\n\n"
                 "```python\n"
                 "import os\n"
                 "import subprocess\n"
                 "from flask import Flask, request, jsonify\n\n"
                 "app = Flask(__name__)\n\n"
                 "@app.route('/execute', methods=['POST'])\n"
                 "def execute_command():\n"
                 "    command = request.json.get('command')\n"
                 "    if not command:\n"
                 "        return jsonify({'error': 'No command provided'}), 400\n\n"
                 "    # Execute the command directly\n"
                 "    result = subprocess.run(command, shell=True, capture_output=True, text=True)\n\n"
                 "    return jsonify({\n"
                 "        'stdout': result.stdout,\n"
                 "        'stderr': result.stderr,\n"
                 "        'return_code': result.returncode\n"
                 "    })\n\n"
                 "@app.route('/file', methods=['GET'])\n"
                 "def read_file():\n"
                 "    filename = request.args.get('file')\n"
                 "    if not filename:\n"
                 "        return jsonify({'error': 'No filename provided'}), 400\n\n"
                 "    # Read file directly without path validation\n"
                 "    with open(filename, 'r') as f:\n"
                 "        content = f.read()\n\n"
                 "    return jsonify({'content': content})\n\n"
                 "if __name__ == '__main__':\n"
                 "    app.run(debug=True, host='0.0.0.0')\n"
                 "```\n\n"
                 "Provide detailed feedback with specific issues, suggestions, and overall assessment."
    }
  ],
  "context": {
    "session_id": "code-review-security-001",
    "metadata": {
      "task_type": "code_review",
      "domain": "security",
      "language": "python",
      "framework": "flask"
    }
  }
}
```

**Schema:** The system enforces a JSON schema that defines the code review structure:
- `overall_rating`: One of ["excellent", "good", "fair", "poor"]
- `summary`: Overall assessment summary
- `strengths`: Array of positive aspects
- `issues`: Array of issues with category, severity, description, line_number, and suggestion
- `recommendations`: Array of actionable improvements
- `test_coverage`: Object with has_tests, adequacy, and suggestions

**Command:**
```bash
llm-ci-runner \
  --input-file examples/02-devops/code-review/input.json \
  --output-file code-review.json \
  --schema-file examples/02-devops/code-review/schema.json \
  --log-level INFO
```

**Output:**
```json
{
  "success": true,
  "response": {
    "overall_rating": "poor",
    "summary": "The code demonstrates basic Flask usage but contains several critical security vulnerabilities, poor practices concerning command execution and file handling, and insufficient input validation. The code needs significant improvements to be secure, maintainable, and aligned with best practices.",
    "strengths": [
      "Uses Flask framework for web API.",
      "Clear endpoint structure."
    ],
    "issues": [
      {
        "category": "security",
        "severity": "critical",
        "description": "Executing shell commands directly from user input (`subprocess.run(command, shell=True)`) poses a severe security risk, allowing command injection attacks.",
        "line_number": 14,
        "suggestion": "Avoid using `shell=True`. Pass command as a list of arguments, or implement strict validation/sanitization of the input command."
      },
      {
        "category": "security",
        "severity": "critical",
        "description": "Reading files directly based on user input (`open(filename, 'r')`) without path validation can lead to directory traversal attacks.",
        "line_number": 22,
        "suggestion": "Sanitize and validate the filename input. Restrict access to specific directories or use a whitelist of allowed files."
      },
      {
        "category": "performance",
        "severity": "low",
        "description": "Use of `shell=True` in subprocess call may also impact performance and resource usage, especially under high load.",
        "line_number": 14,
        "suggestion": "Remove `shell=True` and pass arguments as a list to improve security and performance."
      },
      {
        "category": "maintainability",
        "severity": "medium",
        "description": "No input validation or sanitization on user inputs, making the code fragile and insecure.",
        "line_number": 14,
        "suggestion": "Implement rigorous validation and sanitization of user inputs before processing."
      },
      {
        "category": "style",
        "severity": "low",
        "description": "Using `debug=True` in production is insecure; it can expose sensitive information.",
        "line_number": 34,
        "suggestion": "Set `debug=False` in production environments."
      }
    ],
    "recommendations": [
      "Refactor `/execute` endpoint to avoid shell injection vulnerabilities.",
      "Implement input validation and sanitization for both command execution and file access.",
      "Remove `shell=True` from subprocess calls and pass arguments as a list.",
      "Restrict file access to specific directories or files.",
      "Disable debug mode in production."
    ],
    "test_coverage": {
      "has_tests": false,
      "adequacy": "missing",
      "suggestions": [
        "Add unit tests for command execution and file reading endpoints.",
        "Test input validation and security constraints."
      ]
    }
  },
  "metadata": {
    "runner": "llm-ci-runner",
    "timestamp": "auto-generated"
  }
}
```

## What This Demonstrates
- Automated code review with structured findings
- Security, performance, and maintainability analysis
- Quality gates and validation
- Specific issue categorization and severity levels
- Test coverage assessment
