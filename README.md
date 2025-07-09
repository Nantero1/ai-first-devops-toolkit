# Docker Image for LLM-powered CI/CD pipeline steps

[![Generic badge](https://img.shields.io/badge/Miniconda-4.1.1_rhel8-green.svg)](https://teambank.jfrog.io/ui/packages/docker:%2F%2Fminiconda?name=miniconda&type=packages)
[![Build Status](https://dev.azure.com/teambankag/CDOS/_apis/build/status%2Fbase-images%2Fdocker-image-llm-runtime?repoName=docker-image-llm-runtime&branchName=main)](https://dev.azure.com/teambankag/CDOS/_build/latest?definitionId=3770&repoName=docker-image-llm-runtime&branchName=main)
[![Generic badge](https://img.shields.io/badge/Cloud_allowed-Yes-green)](https://wiki.teambank.de/confluence/x/bR9zHw)

### Available platforms
![Platform linux/amd64](https://img.shields.io/badge/linux/amd64-ready-green)
![Platform linux/arm64](https://img.shields.io/badge/linux/arm64-ready-green)

## This repo is a fork of [ai-first-devops-toolkit](https://github.com/Nantero1/ai-first-devops-toolkit) and the resulting pypi package [llm-ci-runner repository](https://pypi.org/project/llm-ci-runner/).

Is is built uppon version `1.0.4` and currently used to run AI-powered CI/CD pipeline steps. For usage refer to the [pipeline templates](https://dev.azure.com/teambankag/CDOS/_git/azure-devops-pipeline).

You can use this Docker image directly as a container in your Azure DevOps pipeline jobs to enable AI-powered automation steps. When your pipeline runs inside this image, all the required dependencies for LLM-based automation are pre-installed and ready to use.

**Example: Using this image in Azure DevOps pipeline**

```yaml
jobs:
  - job: ai_automation
    displayName: "Run AI Automation with LLM Runtime"
    container: 
      image: teambank.jfrog.io/cdos-marketplace-docker/llm-runtime:latest
    steps:
      - script: |
          uv run llm_ci_runner.py \
            --input-file examples/02-devops/pr-description/input.json \
            --schema-file examples/02-devops/pr-description/schema.json \
            --output-file pr-analysis.json
          pr_description=$(cat pr-analysis.json | jq '.response.description')
          echo vso[task.setvariable variable=pr_description]$pr_description
        displayName: "Run LLM CI Runner for PR Analysis"
# if not set sane defaults are used at the moment
#        env:
#          AZURE_OPENAI_ENDPOINT: $(AZURE_OPENAI_ENDPOINT)
#          AZURE_OPENAI_MODEL: $(AZURE_OPENAI_MODEL)
#          AZURE_OPENAI_API_VERSION: $(AZURE_OPENAI_API_VERSION)

```

This approach allows you to:
- Run AI-powered code review, changelog generation, security analysis, and more as part of your CI/CD pipeline
- Guarantee schema-compliant outputs for downstream automation
- Leverage Azure RBAC or API key authentication for secure access to Azure OpenAI
- Use all features of the `llm-ci-runner` CLI and Python module out-of-the-box

See the [pipeline templates](https://dev.azure.com/teambankag/CDOS/_git/azure-devops-pipeline) for more details on how this image is used to automate CI/CD workflows.

Below is the original README.md:

---

# AI-First DevOps Toolkit: LLM-Powered CI/CD Automation

[![PyPI version](https://badge.fury.io/py/llm-ci-runner.svg)](https://badge.fury.io/py/llm-ci-runner)

> **🚀 The Future of DevOps is AI-First**  
> This toolkit represents a step toward [AI-First DevOps](https://technologyworkroom.blogspot.com/2025/06/building-ai-first-devops.html) - where intelligent automation handles the entire development lifecycle. Built for teams ready to embrace the exponential productivity gains of AI-powered development. Please read [the blog post](https://technologyworkroom.blogspot.com/2025/06/building-ai-first-devops.html) for more details on the motivation.

## TLDR: What This Tool Does

**Purpose**: Zero-friction LLM integration for CI/CD pipelines with **100% guaranteed schema compliance**. This is your foundation for AI-first integration practices.

**Perfect For**:
- 🤖 **AI-Generated Code Reviews**: Automated PR analysis with structured findings
- 📝 **Intelligent Documentation**: Generate changelogs, release notes, and docs automatically  
- 🔍 **Security Analysis**: AI-powered vulnerability detection with structured reports
- 🎯 **Quality Gates**: Enforce standards through AI-driven validation
- 🚀 **Autonomous Development**: Enable AI agents to make decisions in your pipelines
- 🎯 **JIRA Ticket Updates**: Update JIRA tickets based on LLM output
- 🔗 **Unlimited Integration Possibilities**: Chain it multiple times and use as glue code in your tool stack
---

### Simple structured output example

```bash
# Install and use immediately
pip install llm-ci-runner
llm-ci-runner --input-file examples/02-devops/pr-description/input.json --schema-file examples/02-devops/pr-description/schema.json
```
![Structured output of the PR review example](https://github.com/Nantero1/ai-first-devops-toolkit/raw/main/examples/02-devops/pr-description/output.png)

## The AI-First Development Revolution

This toolkit embodies the principles outlined in [Building AI-First DevOps](https://technologyworkroom.blogspot.com/2025/06/building-ai-first-devops.html):

| Traditional DevOps | AI-First DevOps (This Tool) |
|-------------------|----------------------------|
| Manual code reviews | 🤖 AI-powered reviews with structured findings |
| Human-written documentation | 📝 AI-generated docs with guaranteed consistency |
| Reactive security scanning | 🔍 Proactive AI security analysis |
| Manual quality gates | 🎯 AI-driven validation with schema enforcement |
| Linear productivity | 📈 Exponential gains through intelligent automation |

## Features

- 🎯 **100% Schema Enforcement**: Your pipeline never gets invalid data. Token-level schema enforcement with guaranteed compliance
- 🔄 **Resilient execution**: Retries with exponential back-off and jitter plus a clear exception hierarchy keep transient cloud faults from breaking your CI.
- 🚀 **Zero-Friction CLI**: Single script, minimal configuration for pipeline integration and automation
- 🔐 **Enterprise Security**: Azure RBAC via DefaultAzureCredential with fallback to API Key
- 📋 **CI-friendly CLI**: Stateless command that reads JSON, writes JSON, and exits with proper codes
- 🎨 **Beautiful Logging**: Rich console output with timestamps and colors
- 📁 **File-based I/O**: CI/CD friendly with JSON input/output
- 🔧 **Simple & Extensible**: Easy to understand and modify for your specific needs
- 🤖 **Semantic Kernel foundation**: async, service-oriented design ready for skills, memories, orchestration, and future model upgrades
- 📚 **Documentation**: Comprehensive documentation for all features and usage examples. Use your semantic kernel skills to extend the functionality.
- 🧑‍⚖️ **Acceptance Tests**: pytest framework with the LLM-as-Judge pattern for quality gates. Test your scripts before you run them in production.
- 💰 **Coming soon**: token usage and cost estimation appended to each result for budgeting and optimisation

## Installation

```bash
pip install llm-ci-runner
```

That's it! No complex setup, no dependency management - just install and use. Perfect for CI/CD pipelines and local development.

## Quick Start

### 1. Install from PyPI

```bash
pip install llm-ci-runner
```

### 2. Set Environment Variables

```bash
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_MODEL="gpt-4.1-nano"  # or any other GPT deployment name
export AZURE_OPENAI_API_VERSION="2024-12-01-preview"  # Optional
```

**Authentication Options:**
- **RBAC (Recommended)**: Uses `DefaultAzureCredential` for Azure RBAC authentication - no API key needed! See [Microsoft Docs](https://learn.microsoft.com/en-us/python/api/azure-identity/azure.identity.defaultazurecredential?view=azure-python) for setup.
- **API Key**: Set `AZURE_OPENAI_API_KEY` environment variable if not using RBAC.

### 3. Basic Usage

```bash
# Simple chat example
llm-ci-runner --input-file examples/01-basic/simple-chat/input.json

# With structured output schema
llm-ci-runner \
  --input-file examples/01-basic/sentiment-analysis/input.json \
  --schema-file examples/01-basic/sentiment-analysis/schema.json

# Custom output file
llm-ci-runner \
  --input-file examples/02-devops/pr-description/input.json \
  --schema-file examples/02-devops/pr-description/schema.json \
  --output-file pr-analysis.json
```

### 4. Development Setup (Optional)

For contributors or advanced users who want to modify the source:

```bash
# Install UV if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and install for development
git clone https://github.com/Nantero1/ai-first-devops-toolkit.git
cd ai-first-devops-toolkit
uv sync

# Run from source
uv run llm_ci_runner.py --input-file examples/01-basic/simple-chat/input.json
```

## Real-World Examples

You can explore the **[examples directory](https://github.com/Nantero1/ai-first-devops-toolkit/tree/main/examples)** for a complete collection of self-contained examples organized by category.

For comprehensive real-world CI/CD scenarios, see **[examples/uv-usage-example.md](https://github.com/Nantero1/ai-first-devops-toolkit/blob/main/examples/uv-usage-example.md)** which includes:

- 🔄 **Automated PR Description Updates**: Generate comprehensive PR descriptions from commit messages and code changes
- 🔒 **Security Analysis with LLM-as-Judge**: Analyze code changes for vulnerabilities with guaranteed schema compliance
- 📋 **Automated Changelog Generation**: Create structured changelogs from commit history
- 🤖 **Code Review Automation**: Automated reviews with structured findings and quality gates
- 🔗 **Multi-Stage AI Pipelines**: Chain multiple AI operations for complex workflows

## Input Format

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant."
    },
    {
      "role": "user", 
      "content": "Your task description here"
    }
  ],
  "context": {
    "session_id": "optional-session-id",
    "metadata": {
      "any": "additional context"
    }
  }
}
```

## Structured Outputs with 100% Schema Enforcement

When you provide a `--schema-file`, the runner guarantees perfect schema compliance:

```bash
llm-ci-runner \
  --input-file examples/01-basic/sentiment-analysis/input.json \
  --schema-file examples/01-basic/sentiment-analysis/schema.json
```

**Note**: Output defaults to `result.json`. Use `--output-file custom-name.json` for custom output files.

**Supported Schema Features**:
✅ String constraints (enum, minLength, maxLength, pattern)  
✅ Numeric constraints (minimum, maximum, multipleOf)  
✅ Array constraints (minItems, maxItems, items type)  
✅ Required fields enforced at generation time  
✅ Type validation (string, number, integer, boolean, array)  

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Setup Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.12'

- name: Install LLM CI Runner
  run: pip install llm-ci-runner

- name: Generate PR Review with Schema Enforcement
  run: |
    llm-ci-runner \
      --input-file examples/02-devops/pr-description/input.json \
      --schema-file examples/02-devops/pr-description/schema.json \
      --output-file pr-analysis.json \
      --log-level WARNING
  env:
    AZURE_OPENAI_ENDPOINT: ${{ secrets.AZURE_OPENAI_ENDPOINT }}
    AZURE_OPENAI_MODEL: ${{ secrets.AZURE_OPENAI_MODEL }}

- name: Use the structured output
  run: |
    # The output is now in pr-analysis.json with guaranteed schema compliance
    cat pr-analysis.json | jq '.summary'
```

**For Development/Source Usage:**
```yaml
- name: Generate PR Review (from source)
  run: |
    uv run --frozen llm_ci_runner.py \
      --input-file examples/02-devops/pr-description/input.json \
      --schema-file examples/02-devops/pr-description/schema.json
  env:
    AZURE_OPENAI_ENDPOINT: ${{ secrets.AZURE_OPENAI_ENDPOINT }}
    AZURE_OPENAI_MODEL: ${{ secrets.AZURE_OPENAI_MODEL }}
```

For complete CI/CD examples, see **[examples/uv-usage-example.md](https://github.com/Nantero1/ai-first-devops-toolkit/blob/main/examples/uv-usage-example.md)**.

## Authentication

Uses Azure's `DefaultAzureCredential` supporting:
- Environment variables (local development)
- Managed Identity (recommended for Azure CI/CD)
- Azure CLI (local development)
- Service Principal (non-Azure CI/CD)

## Testing

We maintain comprehensive test coverage with **100% success rate**:

```bash
# For package users - install test dependencies
pip install llm-ci-runner[dev]

# For development - install from source with test dependencies
uv sync --group dev

# Run specific test categories
pytest tests/unit/ -v          # 70 unit tests
pytest tests/integration/ -v   # End-to-end examples
pytest acceptance/ -v          # LLM-as-judge evaluation

# Or with uv for development
uv run pytest tests/unit/ -v
uv run pytest tests/integration/ -v
uv run pytest acceptance/ -v
```

## Releasing

### Manual Release Process

1. **Test locally first**:
   ```bash
   python scripts/release.py 1.0.0
   ```

2. **Trigger GitHub Actions release**:
   - Go to Actions → Manual Release
   - Click "Run workflow"
   - Enter version (e.g., `1.0.0`)
   - Add release notes (optional)
   - Choose whether to publish to PyPI
   - Click "Run workflow"

The workflow will:
- ✅ Run all tests
- ✅ Update version in `pyproject.toml`
- ✅ Build the package
- ✅ Create Git tag and push
- ✅ Create GitHub release
- ✅ Publish to PyPI (if selected)
- ✅ Verify package installation

### Package Naming Convention

- **Package name**: `llm-ci-runner` (kebab-case for PyPI)
- **Module name**: `llm_ci_runner.py` (snake_case for Python)
- **CLI command**: `llm-ci-runner` (kebab-case for CLI)

## Use Cases

### Automated Code Review with Structured Output
Generate detailed code reviews with **guaranteed schema compliance** for CI/CD integration.

### Security Analysis with Structured Results
Analyze code changes for potential security vulnerabilities with structured findings.

### Documentation Updates
Generate or update documentation based on code changes.

### Release Notes with Structured Metadata
Create formatted release notes with guaranteed schema compliance.

For detailed examples of each use case, see **[examples directory](https://github.com/Nantero1/ai-first-devops-toolkit/tree/main/examples)**.

## Architecture

Built on **Microsoft Semantic Kernel** for:
- Enterprise-ready Azure OpenAI integration
- Future-proof model compatibility
- **100% Schema Enforcement**: KernelBaseModel integration with token-level constraints
- **Dynamic Model Creation**: Runtime JSON schema → Pydantic model conversion
- **RBAC**: Azure RBAC via DefaultAzureCredential

## The AI-First Development Journey

This toolkit is your first step toward [AI-First DevOps](https://technologyworkroom.blogspot.com/2025/06/building-ai-first-devops.html). As you integrate AI into your development workflows, you'll experience:

1. **🚀 Exponential Productivity**: AI handles routine tasks while you focus on architecture
2. **🎯 Guaranteed Quality**: Schema enforcement eliminates validation errors
3. **🤖 Autonomous Operations**: AI agents make decisions in your pipelines
4. **📈 Continuous Improvement**: Every interaction improves your AI system

**The future belongs to teams that master AI-first principles.** This toolkit gives you the foundation to start that journey today.

## License

MIT License - See [LICENSE](https://github.com/Nantero1/ai-first-devops-toolkit/blob/main/LICENSE) file for details. Copyright (c) 2025, Benjamin Linnik.

## Support

**🐛 Found a bug? 💡 Have a question? 📚 Need help?**

**GitHub is your primary destination for all support:**

- **📋 Issues & Bug Reports**: [Create an issue](https://github.com/Nantero1/ai-first-devops-toolkit/issues)
- **📖 Documentation**: [Browse examples](https://github.com/Nantero1/ai-first-devops-toolkit/tree/main/examples)
- **🔧 Source Code**: [View source](https://github.com/Nantero1/ai-first-devops-toolkit)

**Before opening an issue, please:**
1. ✅ Check the [examples directory](https://github.com/Nantero1/ai-first-devops-toolkit/tree/main/examples) for solutions
2. ✅ Review the error logs (beautiful output with Rich!)
3. ✅ Validate your Azure authentication and permissions
4. ✅ Ensure your input JSON follows the required format
5. ✅ Search existing [issues](https://github.com/Nantero1/ai-first-devops-toolkit/issues) for similar problems

**Quick Links:**
- 🚀 [Getting Started Guide](https://github.com/Nantero1/ai-first-devops-toolkit#quick-start)
- 📚 [Complete Examples](https://github.com/Nantero1/ai-first-devops-toolkit/tree/main/examples)
- 🔧 [CI/CD Integration](https://github.com/Nantero1/ai-first-devops-toolkit#cicd-integration)
- 🎯 [Use Cases](https://github.com/Nantero1/ai-first-devops-toolkit#use-cases)

---

*Ready to embrace the AI-First future? Start with this toolkit and build your path to exponential productivity. Learn more about the AI-First DevOps revolution in [Building AI-First DevOps](https://technologyworkroom.blogspot.com/2025/06/building-ai-first-devops.html).*