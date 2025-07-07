# Real-World CI/CD Examples with LLM Runner

This document demonstrates practical AI-first DevOps workflows using the LLM Runner in real CI/CD scenarios. Each example shows how to integrate AI-powered automation into your development pipeline.

## Prerequisites

1. **Install UV** (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. **Set Environment Variables**:
```bash
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_MODEL="gpt-4.1-nano"
```

## Real-World CI/CD Scenarios

### 1. Automated PR Description Updates

**Scenario**: Generate comprehensive PR descriptions based on commit messages and code changes.

#### Step 1: Extract Git Information
```bash
# Get the last commit message and diff
git log -1 --pretty=format:"%s" > commit_message.txt
git diff HEAD~1 > code_changes.diff

# For PR context (if in a PR)
if [ -n "$PR_NUMBER" ]; then
  git diff origin/main...HEAD > pr_changes.diff
fi
```

#### Step 2: Create Input Context
```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are an expert DevOps engineer. Generate comprehensive PR descriptions that include: summary of changes, impact analysis, testing notes, and deployment considerations."
    },
    {
      "role": "user",
      "content": "Generate a PR description based on:\n\nCOMMIT MESSAGE:\n$(cat commit_message.txt)\n\nCODE CHANGES:\n$(cat code_changes.diff)\n\nFocus on: what changed, why it changed, impact on users, testing requirements, and deployment notes."
    }
  ]
}
```

#### Step 3: Execute with Structured Output
```bash
# Create PR description with schema enforcement
uv run --frozen llm_ci_runner.py \
  --input-file examples/02-devops/pr-description/input.json \
  --output-file pr-description.json \
  --schema-file examples/02-devops/pr-description/schema.json \
  --log-level INFO

# Extract the description for GitHub
PR_DESCRIPTION=$(jq -r '.response.description' pr-description.json)
echo "$PR_DESCRIPTION" > pr_description.md
```

#### Step 4: GitHub Actions Integration
```yaml
name: Auto-Generate PR Description

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  generate-pr-description:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
      with:
        fetch-depth: 0  # Get full history for diff
    
    - name: Install UV
      run: curl -LsSf https://astral.sh/uv/install.sh | sh
    
    - name: Extract Git Context
      run: |
        git log -1 --pretty=format:"%s" > commit_message.txt
        git diff origin/main...HEAD > pr_changes.diff
    
    - name: Generate PR Description
      run: |
        uv run --frozen llm_ci_runner.py \
          --input-file examples/02-devops/pr-description/input.json \
          --output-file pr-description.json \
          --schema-file examples/02-devops/pr-description/schema.json
      env:
        AZURE_OPENAI_ENDPOINT: ${{ secrets.AZURE_OPENAI_ENDPOINT }}
        AZURE_OPENAI_MODEL: ${{ secrets.AZURE_OPENAI_MODEL }}
    
    - name: Update PR Description
      uses: actions/github-script@v7
      with:
        script: |
          const description = require('fs').readFileSync('pr-description.json', 'utf8');
          const content = JSON.parse(description).response.description;
          await github.rest.pulls.update({
            owner: context.repo.owner,
            repo: context.repo.repo,
            pull_number: context.issue.number,
            body: content
          });
```

### 2. Security Analysis with LLM-as-Judge

**Scenario**: Analyze code changes for security vulnerabilities with guaranteed schema compliance and quality validation.

#### Step 1: Create Security Analysis Schema
```json
{
  "type": "object",
  "properties": {
    "security_rating": {
      "type": "string",
      "enum": ["secure", "low_risk", "medium_risk", "high_risk", "critical"],
      "description": "Overall security assessment"
    },
    "vulnerabilities": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "type": {
            "type": "string",
            "enum": ["sql_injection", "xss", "path_traversal", "command_injection", "authentication", "authorization", "data_exposure", "other"]
          },
          "severity": {
            "type": "string",
            "enum": ["critical", "high", "medium", "low"]
          },
          "description": {"type": "string"},
          "line_number": {"type": "integer"},
          "fix_suggestion": {"type": "string"}
        },
        "required": ["type", "severity", "description", "fix_suggestion"]
      }
    },
    "recommendations": {
      "type": "array",
      "items": {"type": "string"}
    },
    "compliance_issues": {
      "type": "array",
      "items": {"type": "string"}
    }
  },
  "required": ["security_rating", "vulnerabilities", "recommendations"]
}
```

#### Step 2: Security Analysis Pipeline
```bash
#!/bin/bash
# security-analysis.sh

# Get the diff for analysis
git diff HEAD~1 > code_changes.diff

# Create security analysis input
cat > security-input.json << EOF
{
  "messages": [
    {
      "role": "system",
      "content": "You are a security expert. Analyze code changes for security vulnerabilities, focusing on OWASP Top 10, common attack vectors, and secure coding practices."
    },
    {
      "role": "user",
      "content": "Analyze these code changes for security vulnerabilities:\n\n$(cat code_changes.diff)\n\nProvide detailed security assessment with specific vulnerabilities, severity levels, and fix recommendations."
    }
  ]
}
EOF

# Run security analysis with schema enforcement
uv run --frozen llm_ci_runner.py \
  --input-file examples/03-security/vulnerability-analysis/input.json \
  --output-file security-analysis.json \
  --schema-file examples/03-security/vulnerability-analysis/schema.json \
  --log-level INFO

# Extract results
SECURITY_RATING=$(jq -r '.response.security_rating' security-analysis.json)
VULNERABILITY_COUNT=$(jq -r '.response.vulnerabilities | length' security-analysis.json)

echo "Security Rating: $SECURITY_RATING"
echo "Vulnerabilities Found: $VULNERABILITY_COUNT"

# Fail pipeline if critical vulnerabilities found
if [ "$SECURITY_RATING" = "critical" ]; then
  echo "❌ Critical security vulnerabilities detected!"
  exit 1
fi
```

#### Step 3: LLM-as-Judge Quality Validation
```bash
#!/bin/bash
# validate-security-analysis.sh

# Create judgment input for quality validation
cat > judgment-input.json << EOF
{
  "messages": [
    {
      "role": "system",
      "content": "You are an expert security reviewer. Evaluate the quality and accuracy of security analysis reports."
    },
    {
      "role": "user",
      "content": "Evaluate this security analysis report:\n\n$(cat security-analysis.json)\n\nCriteria: accuracy of vulnerability detection, appropriateness of severity ratings, quality of fix suggestions, completeness of analysis."
    }
  ]
}
EOF

# Run LLM-as-judge evaluation
uv run --frozen llm_ci_runner.py \
  --input-file judgment-input.json \
  --output-file judgment-result.json \
  --schema-file acceptance/judgment_schema.json \
  --log-level INFO

# Check if analysis passes quality standards
PASSES_QUALITY=$(jq -r '.response.pass' judgment-result.json)
OVERALL_SCORE=$(jq -r '.response.overall' judgment-result.json)

if [ "$PASSES_QUALITY" = "false" ]; then
  echo "❌ Security analysis failed quality validation (Score: $OVERALL_SCORE/10)"
  exit 1
fi

echo "✅ Security analysis passed quality validation (Score: $OVERALL_SCORE/10)"
```

#### Step 4: Complete Security Pipeline
```yaml
name: Security Analysis Pipeline

on: [push, pull_request]

jobs:
  security-analysis:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
      with:
        fetch-depth: 0
    
    - name: Install UV
      run: curl -LsSf https://astral.sh/uv/install.sh | sh
    
    - name: Run Security Analysis
      run: |
        chmod +x .github/scripts/security-analysis.sh
        .github/scripts/security-analysis.sh
      env:
        AZURE_OPENAI_ENDPOINT: ${{ secrets.AZURE_OPENAI_ENDPOINT }}
        AZURE_OPENAI_MODEL: ${{ secrets.AZURE_OPENAI_MODEL }}
    
    - name: Validate Analysis Quality
      run: |
        chmod +x .github/scripts/validate-security-analysis.sh
        .github/scripts/validate-security-analysis.sh
      env:
        AZURE_OPENAI_ENDPOINT: ${{ secrets.AZURE_OPENAI_ENDPOINT }}
        AZURE_OPENAI_MODEL: ${{ secrets.AZURE_OPENAI_MODEL }}
    
    - name: Upload Security Report
      uses: actions/upload-artifact@v4
      with:
        name: security-analysis-report
        path: security-analysis.json
```

### 3. Automated Changelog Generation

**Scenario**: Generate comprehensive changelogs from commit history with structured output.

#### Step 1: Extract Commit History
```bash
# Get commits since last tag
git log $(git describe --tags --abbrev=0)..HEAD --pretty=format:"%h|%s|%an|%ad" --date=short > commits.txt

# Get files changed
git diff --name-only $(git describe --tags --abbrev=0)..HEAD > changed_files.txt
```

#### Step 2: Changelog Generation
```bash
# Create changelog input
cat > changelog-input.json << EOF
{
  "messages": [
    {
      "role": "system",
      "content": "You are a technical writer. Generate professional changelog entries from commit history, categorizing changes by type and impact."
    },
    {
      "role": "user",
      "content": "Generate a changelog for version $(git describe --tags --abbrev=0 | sed 's/v//') to $(git rev-parse --short HEAD):\n\nCOMMITS:\n$(cat commits.txt)\n\nCHANGED FILES:\n$(cat changed_files.txt)\n\nCategorize as: features, bugfixes, breaking_changes, improvements, documentation."
    }
  ]
}
EOF

# Generate changelog with schema
uv run --frozen llm_ci_runner.py \
  --input-file examples/02-devops/changelog-generation/input.json \
  --output-file changelog.json \
  --schema-file examples/02-devops/changelog-generation/schema.json \
  --log-level INFO

# Create markdown changelog
jq -r '.response.markdown_content' changelog.json > CHANGELOG.md
```

### 4. Code Review Automation

**Scenario**: Automated code review with structured findings and quality gates.

#### Step 1: Code Review Pipeline
```bash
#!/bin/bash
# code-review.sh

# Get PR diff
git diff origin/main...HEAD > pr_diff.txt

# Create review input
cat > review-input.json << EOF
{
  "messages": [
    {
      "role": "system",
      "content": "You are a senior software engineer conducting code reviews. Focus on code quality, best practices, security, performance, and maintainability."
    },
    {
      "role": "user",
      "content": "Review this pull request:\n\n$(cat pr_diff.txt)\n\nProvide detailed feedback with specific issues, suggestions, and overall assessment."
    }
  ]
}
EOF

# Run code review
uv run --frozen llm_ci_runner.py \
  --input-file examples/02-devops/code-review/input.json \
  --output-file code-review.json \
  --schema-file examples/02-devops/code-review/schema.json \
  --log-level INFO

# Extract review results
OVERALL_RATING=$(jq -r '.response.overall_rating' code-review.json)
ISSUES_COUNT=$(jq -r '.response.issues | length' code-review.json)

echo "Code Review Rating: $OVERALL_RATING"
echo "Issues Found: $ISSUES_COUNT"

# Quality gate
if [ "$OVERALL_RATING" = "poor" ]; then
  echo "❌ Code review failed - too many issues"
  exit 1
fi
```

#### Step 2: GitHub Actions Integration
```yaml
name: Automated Code Review

on: [pull_request]

jobs:
  code-review:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
      with:
        fetch-depth: 0
    
    - name: Install UV
      run: curl -LsSf https://astral.sh/uv/install.sh | sh
    
    - name: Run Code Review
      run: |
        chmod +x .github/scripts/code-review.sh
        .github/scripts/code-review.sh
      env:
        AZURE_OPENAI_ENDPOINT: ${{ secrets.AZURE_OPENAI_ENDPOINT }}
        AZURE_OPENAI_MODEL: ${{ secrets.AZURE_OPENAI_MODEL }}
    
    - name: Post Review Comment
      uses: actions/github-script@v7
      with:
        script: |
          const review = require('fs').readFileSync('code-review.json', 'utf8');
          const data = JSON.parse(review).response;
          
          let comment = `## 🤖 AI Code Review\n\n`;
          comment += `**Overall Rating:** ${data.overall_rating}\n\n`;
          comment += `**Summary:** ${data.summary}\n\n`;
          
          if (data.issues.length > 0) {
            comment += `**Issues Found:**\n`;
            data.issues.forEach(issue => {
              comment += `- **${issue.severity.toUpperCase()}** (${issue.category}): ${issue.description}\n`;
              if (issue.suggestion) {
                comment += `  - Suggestion: ${issue.suggestion}\n`;
              }
            });
          }
          
          await github.rest.issues.createComment({
            issue_number: context.issue.number,
            owner: context.repo.owner,
            repo: context.repo.repo,
            body: comment
          });
```

## Advanced Patterns

### 1. Multi-Stage AI Pipeline
```bash
#!/bin/bash
# multi-stage-pipeline.sh

# Stage 1: Code Analysis
uv run --frozen llm_ci_runner.py \
  --input-file examples/02-devops/code-review/input.json \
  --output-file stage1-output.json \
  --schema-file examples/02-devops/code-review/schema.json

# Stage 2: Quality Validation (LLM-as-Judge)
uv run --frozen llm_ci_runner.py \
  --input-file stage2-input.json \
  --output-file stage2-output.json \
  --schema-file acceptance/judgment_schema.json

# Stage 3: Action Generation
uv run --frozen llm_ci_runner.py \
  --input-file examples/02-devops/pr-description/input.json \
  --output-file stage3-output.json \
  --schema-file examples/02-devops/pr-description/schema.json

# Process final results
FINAL_ACTIONS=$(jq -r '.response.actions[]' stage3-output.json)
for action in $FINAL_ACTIONS; do
  echo "Executing: $action"
  # Execute action based on type
done
```

### 2. Conditional Workflows
```yaml
name: Smart CI/CD Pipeline

on: [push, pull_request]

jobs:
  analyze-changes:
    runs-on: ubuntu-latest
    outputs:
      needs-security-review: ${{ steps.analysis.outputs.security }}
      needs-performance-review: ${{ steps.analysis.outputs.performance }}
    steps:
    - name: Analyze Changes
      id: analysis
      run: |
        # Determine what type of review is needed
        uv run --frozen llm_ci_runner.py \
          --input-file examples/01-basic/simple-chat/input.json \
          --output-file change-analysis.json \
          --schema-file examples/01-basic/simple-chat/schema.json
        
        SECURITY_NEEDED=$(jq -r '.response.needs_security_review' change-analysis.json)
        PERFORMANCE_NEEDED=$(jq -r '.response.needs_performance_review' change-analysis.json)
        
        echo "security=$SECURITY_NEEDED" >> $GITHUB_OUTPUT
        echo "performance=$PERFORMANCE_NEEDED" >> $GITHUB_OUTPUT

  security-review:
    needs: analyze-changes
    if: needs.analyze-changes.outputs.needs-security-review == 'true'
    runs-on: ubuntu-latest
    steps:
    - name: Security Review
      run: |
        uv run --frozen llm_ci_runner.py \
          --input-file examples/03-security/vulnerability-analysis/input.json \
          --output-file security-result.json \
          --schema-file examples/03-security/vulnerability-analysis/schema.json

  performance-review:
    needs: analyze-changes
    if: needs.analyze-changes.outputs.needs-performance-review == 'true'
    runs-on: ubuntu-latest
    steps:
    - name: Performance Review
      run: |
        uv run --frozen llm_ci_runner.py \
          --input-file examples/04-ai-first/autonomous-development-plan/input.json \
          --output-file performance-result.json \
          --schema-file examples/04-ai-first/autonomous-development-plan/schema.json
```

## Best Practices

### 1. Schema Design
- **Be Specific**: Define exact constraints for your use case
- **Include Validation**: Use enums, ranges, and required fields
- **Plan for Evolution**: Design schemas that can be extended

### 2. Error Handling
```bash
# Always check return codes
if ! uv run --frozen llm_ci_runner.py --input-file input.json --output-file output.json; then
  echo "❌ LLM execution failed"
  exit 1
fi

# Validate output structure
if ! jq -e '.response' output.json > /dev/null; then
  echo "❌ Invalid output structure"
  exit 1
fi
```

### 3. Cost Optimization
- **Cache Results**: Store and reuse analysis results
- **Batch Processing**: Combine multiple analyses
- **Selective Execution**: Only run when necessary

### 4. Quality Gates
- **LLM-as-Judge**: Always validate AI output quality
- **Schema Compliance**: Ensure 100% schema enforcement
- **Human Oversight**: Review critical decisions

## Troubleshooting

### Common Issues
```bash
# UV not found in CI/CD
export PATH="$HOME/.local/bin:$PATH"

# Schema validation failures
uv run --frozen llm_ci_runner.py --input-file input.json --output-file output.json --log-level DEBUG

# Timeout issues
timeout 300 uv run --frozen llm_ci_runner.py --input-file input.json --output-file output.json
```

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
uv run --frozen llm_ci_runner.py --input-file input.json --output-file output.json --log-level DEBUG
```

This comprehensive guide shows how to implement AI-first DevOps practices in real-world scenarios. Each example demonstrates the power of combining structured outputs, LLM-as-judge validation, and CI/CD integration for exponential productivity gains. 