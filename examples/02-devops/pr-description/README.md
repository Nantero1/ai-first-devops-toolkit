# PR Description Generation Example

Automated PR description generation with structured output for CI/CD integration.

## Files
- `input.json` - The prompt and PR context
- `schema.json` - JSON schema for structured PR descriptions
- `input.yaml` - Same content as input.json but in YAML format (more readable)
- `schema.yaml` - Same schema as schema.json but in YAML format (more readable)
- `README.md` - This documentation

## Example:

When you use this example, here is what happens step by step:

**Input:**
```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are an expert DevOps engineer. Generate comprehensive PR descriptions that"
                 "include:summary of changes, impact analysis, testing notes, and deployment"
                 "considerations."
    },
    {
      "role": "user",
      "content": "Please review this pull request for security issues and code quality:\n\n"
                 "```diff\n"
                 "--- a/auth/login.py\n"
                 "+++ b/auth/login.py\n"
                 "@@ -10,7 +10,7 @@\n"
                 "def authenticate_user(username, password):\n"
                 "    if not username or not password:\n"
                 "        return False\n"
                 "\n"
                 "-   query = f'SELECT * FROM users WHERE username = '{username}''\n"
                 "+   query = 'SELECT * FROM users WHERE username = %s'\n"
                 "    cursor.execute(query, (username,))\n"
                 "\n"
                 "@@ -25,6 +25,8 @@\n"
                 "def create_session(user_id):\n"
                 "    session_token = secrets.token_urlsafe(32)\n"
                 "    expiry = datetime.now() + timedelta(hours=24)\n"
                 "\n"
                 "    if not user_id or user_id <= 0:\n"
                 "        raise ValueError('Invalid user_id')\n"
                 "\n"
                 "    query = 'INSERT INTO sessions (user_id, token, expiry) VALUES (%s, %s, %s)'\n"
                 "    cursor.execute(query, (user_id, session_token, expiry))\n"
                 "    conn.commit()\n"
                 "```\n\n"
                 "Focus on:\n"
                 "- SQL injection vulnerabilities\n"
                 "- Input validation\n"
                 "- Error handling\n"
                 "- Security best practices"
    }
  ],
  "context": {
    "session_id": "pr-review-auth-fix-123",
    "metadata": {
      "repository": "secure-app",
      "pr_number": 456,
      "branch": "fix/sql-injection",
      "files_changed": [
        "auth/login.py"
      ],
      "review_type": "security_focused"
    }
  }
}
```

**Schema:** The system enforces a JSON schema that defines the PR description structure:
- `description`: Full markdown PR description
- `summary`: Brief summary (max 200 chars)
- `change_type`: One of ["feature", "bugfix", "refactor", "docs", "style", "test", "chore"]
- `impact`: One of ["low", "medium", "high", "critical"]
- `testing_notes`: Array of testing requirements
- `deployment_notes`: Array of deployment considerations
- `breaking_changes`: Array of breaking changes
- `related_issues`: Array of related issue numbers

**Command (JSON):**
```bash
llm-ci-runner \
  --input-file examples/02-devops/pr-description/input.json \
  --output-file pr-description.json \
  --schema-file examples/02-devops/pr-description/schema.json \
  --log-level INFO
```

**Command (YAML):**
```bash
llm-ci-runner \
  --input-file examples/02-devops/pr-description/input.yaml \
  --output-file pr-description.yaml \
  --schema-file examples/02-devops/pr-description/schema.yaml \
  --log-level INFO
```
![Structured output of the PR review example](./output.png)

**Output:**
```json
{
  "success": true,
  "response": {
    "description":
     "### Summary\n"
     "This PR addresses potential security issues and improves code quality in the login module.\n\n"
     "### Changes\n"
     "- Parameterized SQL queries to prevent SQL injection.\n"
     "- Added validation for `user_id` in `create_session` to ensure data integrity.\n"
     "- Minor formatting and error handling improvements.\n\n"
     "### Impact\n"
     "- Enhances security by preventing SQL injection.\n"
     "- Improves robustness of session creation.\n"
     "- Slightly increases input validation coverage.\n\n"
     "### Testing Notes\n"
     "- Verify that SQL injection attempts in `authenticate_user` are ineffective.\n"
     "- Test `create_session` with invalid `user_id` inputs (e.g., None, negative values) and ensure proper error handling.\n"
     "- Run existing unit tests; add new tests for invalid `user_id` cases if necessary.\n\n"
     "### Deployment Notes\n"
     "- No downtime expected.\n"
     "- Ensure database schema is compatible with the changes.\n"
     "- Confirm application redeployment after merging integration.\n\n"
     "### Breaking Changes\n"
     "- None.\n\n"
     "### Related Issues\n"
     "- N/A",
    "summary": "Improve security by parameterizing SQL queries and validating `user_id` in session creation.",
    "change_type": "bugfix",
    "impact": "high",
    "testing_notes": [
      "Attempt SQL injection in `authenticate_user` and verify it is blocked.",
      "Test `create_session` with invalid `user_id` inputs (None, negative, zero).",
      "Run existing unit tests; add new tests for invalid input cases."
    ],
    "deployment_notes": [
      "No significant downtime expected.",
      "Ensure database schema is compatible.",
      "Redeploy application after merge."
    ],
    "breaking_changes": [],
    "related_issues": []
  },
  "metadata": {
    "runner": "llm-ci-runner",
    "timestamp": "auto-generated"
  }
}
```

## What This Demonstrates
- Automated PR description generation from code changes
- Structured output with comprehensive PR metadata
- CI/CD integration ready
- Impact assessment and testing requirements
- Breaking changes detection
- **YAML Support**: Use YAML for more readable input/schema files
- **Format Flexibility**: Choose JSON or YAML based on your preference
