# Changelog Generation Example

Automated changelog generation from commit history with structured output.

## Files
- `input.json` - The prompt and commit history context
- `schema.json` - JSON schema for structured changelog output
- `README.md` - This documentation

## Example:

When you use this example, here is what happens step by step:

**Input:**
```json
{
    "messages": [
        {
            "role": "system",
            "content": "You are a technical writer. Generate professional changelog entries from commit history, categorizing changes by type and impact."
        },
        {
            "role": "user",
            "content": 
                "Generate a changelog for version 2.1.0 with the following commits:"
                ""
                "- feat: Add user authentication system with OAuth2 support"
                "- fix: Resolve SQL injection vulnerability in login endpoint"
                "- docs: Update API documentation with new endpoints"
                "- feat: Implement real-time notifications using WebSockets"
                "- fix: Handle edge case in password validation"
                "- breaking: Remove deprecated /api/v1 endpoints"
                "- feat: Add comprehensive logging and monitoring"
                "- perf: Optimize database queries for user search"
                "- docs: Add deployment guide for production environments"
                "- feat: Implement automated backup system"
                ""
                "Categorize as: features, bugfixes, breaking_changes, improvements, documentation, deprecations."
        }
    ],
    "context": {
        "session_id": "changelog-gen-001",
        "metadata": {
            "task_type": "changelog_generation",
            "domain": "documentation",
            "version": "2.1.0",
            "release_date": "2025-01-07"
        }
    }
}
```

**Schema**
- **Change Categorization**: Features, bugfixes, improvements, breaking changes
- **Version Management**: Semantic versioning support
- **Date Validation**: ISO date format enforcement
- **Content Generation**: Structured markdown output
- **Contributor Tracking**: Author attribution 

**Command:**
```bash
llm-ci-runner \
  --input-file examples/02-devops/changelog-generation/input.json \
  --output-file changelog.json \
  --schema-file examples/02-devops/changelog-generation/schema.json
```

**Output:**
```json
{
  "success": true,
  "response": {
    "version": "2.1.0",
    "release_date": "2023-10-05",
    "changes": {
      "features": [
        "Add user authentication system with OAuth2 support",
        "Implement real-time notifications using WebSockets",
        "Add comprehensive logging and monitoring",
        "Implement automated backup system"
      ],
      "bugfixes": [
        "Resolve SQL injection vulnerability in login endpoint",
        "Handle edge case in password validation"
      ],
      "improvements": [
        "Optimize database queries for user search"
      ],
      "breaking_changes": [
        "Remove deprecated /api/v1 endpoints"
      ],
      "documentation": [
        "Update API documentation with new endpoints",
        "Add deployment guide for production environments"
      ],
      "deprecations": []
    },
    "markdown_content": "## Version 2.1.0 - 2023-10-05\n\n### Features\n- User authentication system with OAuth2 support\n- Real-time notifications using WebSockets\n- Comprehensive logging and monitoring\n- Automated backup system\n\n### Bug Fixes\n- SQL injection vulnerability in login endpoint has been resolved\n- Edge case in password validation handled\n\n### Improvements\n- Database queries for user search optimized\n\n### Breaking Changes\n- Deprecated /api/v1 endpoints have been removed\n\n### Documentation\n- Updated API documentation with new endpoints\n- Added deployment guide for production environments\n\n---\n\nThis release introduces several new features, performance improvements, security fixes, and documentation updates to enhance the overall system.",
    "summary": "This release introduces new authentication, real-time communication, enhanced security, and better documentation.",
    "contributors": [
      "Jane Doe",
      "John Smith"
    ]
  },
  "metadata": {
    "runner": "llm-ci-runner",
    "timestamp": "auto-generated"
  }
}
```

## What This Demonstrates
- Automated changelog generation from git commit history
- Structured categorization of changes (features, bugfixes, breaking changes)
- Version and release date management
- Contributor tracking
- Markdown content generation
