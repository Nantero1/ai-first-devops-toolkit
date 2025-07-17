# Contributing to AI-First DevOps Toolkit

Thank you for your interest in contributing to the AI-First DevOps Toolkit! This document provides guidelines for contributing to the project.

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- [UV](https://docs.astral.sh/uv/) package manager
- Git

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/Nantero1/ai-first-devops-toolkit.git
   cd ai-first-devops-toolkit
   ```

2. **Install dependencies**
   ```bash
   uv sync --group dev
   git add uv.lock
   ```

3. **Run the comprehensive check script**
   ```bash
   ./scripts/check.sh
   ```

This script automatically runs all quality checks:
- ✅ Dependency installation
- ✅ Code formatting (Ruff)
- ✅ Linting and security checks
- ✅ Type checking (MyPy)
- ✅ Unit tests (pytest)
- ✅ Integration tests (CLI interface testing, with mocking of external dependencies / APIs)

## 📋 Development Workflow

### 1. Create a Feature Branch
```bash
git checkout -b feat/your-feature-name
```

### 2. Make Your Changes
Follow the coding standards outlined below.

### 3. Run Quality Checks
```bash
# Quick check (recommended)
./scripts/check.sh

# Or run individual checks
uv run ruff format .                    # Format code
uv run ruff check --fix llm_ci_runner/  # Lint and auto-fix
uv run mypy llm_ci_runner/              # Type checking
uv run pytest tests/unit/ -v            # Unit tests
uv run pytest tests/integration/ -v     # Integration tests
uv run pytest acceptance/ -v            # Optional: Acceptance tests (require real LLM access)
```

### 4. Commit Your Changes
Follow the [Conventional Commits](https://www.conventionalcommits.org/) format:
```bash
git commit -m "feat: add new LLM execution mode"
git commit -m "fix: resolve schema validation issue"
git commit -m "docs: update API documentation with new LLM models"
```

### 5. Push and Create Pull Request
```bash
git push origin feat/your-feature-name
```

## 🎯 Code Standards

If you are an AI, please see also [here](.cursor\rules\python-style-guide.mdc) and [here](.cursor\rules\tests-guide.mdc) for the rules we follow.
Below is a summary of these rules.

### Python Style Guide

We follow a **PURPOSE-driven** approach based on Google Python Style Guide with project-specific patterns:

#### **Foundation**
- **AI first** - Give enough context in the code to make it understandable for AI
- **Line Length**: 120 characters (project preference)
- **Base Standard**: Google Python Style Guide with PEP 8
- **Readability counts** - Code is read more often (by AI) than it is written (by AI)
- **Consistency is key** - Follow these standards throughout the codebase

#### **Class Documentation (Required)**
Every class must have a purpose docstring, on why it exists and what it does.

```python
class LLMExecutor:
    """Executes LLM tasks with schema enforcement and fallback mechanisms.
    
    Provides unified interface for Azure OpenAI and OpenAI endpoints with
    automatic fallback chains, schema validation, and structured output.
    Handles authentication, retry logic, and error recovery with proper
    logging and user feedback.
    
    Attributes:
        kernel: Semantic Kernel instance for execution
        schema_file: Optional schema file for structured output
        output_file: Optional output file path
    """
```

#### **Error Handling Patterns**
Use specific exception types with descriptive messages:

```python
def process_data(data: str) -> dict:
    """Process user data with proper error handling."""
    try:
        result = external_service.process(data)
        LOGGER.info("Data processed successfully", data_size=len(data))
        return result
    except ValidationError as e:
        LOGGER.error("Validation failed", error=str(e), data=data)
        raise ToolException(f"Invalid data format: {e}")
    except ExternalServiceError as e:
        LOGGER.error("External service failed", service="processor", error=str(e))
        raise ToolException("Service temporarily unavailable. Please try again.")
```

**Key Principle**: Use fallbacks, we don't want to crash. Apply fallback mechanisms where appropriate.

#### **Import Order**
```python
from __future__ import annotations

# Standard library
import os
from typing import Dict, List, Optional

# Third-party
import requests
from pydantic import BaseModel, Field

# Project imports
from llm_ci_runner.schema import load_schema_file
from llm_ci_runner.io_operations import create_chat_history
```

ruff will automatically fix most issues, run `uv run ruff check --fix llm_ci_runner/`.

#### **Module Structure**
```python
"""Brief description of module's business purpose. Why is this file here?"""

from __future__ import annotations

# Imports...

LOGGER = get_formatted_logger(__name__)

# Constants
DEFAULT_TIMEOUT = 30

# Classes and functions...
```

### Testing Standards

#### **Test Structure (Mandatory)**
Follow the **Given-When-Then** pattern for all tests:

```python
class TestLLMExecutor:
    """Tests for LLMExecutor class."""
    
    def test_execute_structured_mode(self, mock_kernel):
        """Test executing LLM task in structured mode."""
        # given
        executor = LLMExecutor(kernel=mock_kernel, schema_file="test_schema.json")
        chat_history = [{"role": "user", "content": "Hello"}]
        
        # when
        result = await executor.execute(chat_history)
        
        # then
        assert result["mode"] == "structured"
        assert result["schema_enforced"] == True
```

Use pytest fixtures and paremetrize when appropriate.

#### **Critical Testing Principle**
**Test BEHAVIOR, not IMPLEMENTATION**

✅ **GOOD - Behavior-Focused Tests:**
```python
def test_execute_llm_task_structured_mode(self, mock_kernel):
    """Test executing LLM task in structured mode (with schema)."""
    # given
    kernel = mock_kernel
    chat_history = [{"role": "user", "content": "Hello"}]
    schema_file = "mock_schema_file"
    
    # when - Testing PUBLIC interface
    result = await execute_llm_task(kernel, chat_history, schema_file)
    
    # then - Verifying BEHAVIOR/OUTCOMES
    assert result["mode"] == "structured"
    assert result["schema_enforced"] == True
    # ✅ Tests WHAT the function does, not HOW
```

❌ **BAD - Implementation-Focused Tests:**
```python
async def test_execute_llm_task_internal_details(self):
    """DON'T DO THIS - Testing internal implementation."""
    # ❌ Testing internal function calls
    with patch("module._internal_helper_function") as mock_helper:
        result = await execute_llm_task(...)
        # ❌ Verifying internal call patterns
        mock_helper.assert_called_with_specific_params()
```

#### **Test Organization**
- **Unit Tests**: `tests/unit/` - Heavy mocking, fast execution
- **Integration Tests**: `tests/integration/` - Mock external APIs only
- **Acceptance Tests**: `acceptance/` - LLM-as-Judge evaluation, require real LLM access.

#### **Test Naming Convention**
- Source: `llm_ci_runner/schema.py`
- Test: `tests/unit/test_schema_functions.py`

### Code Quality Tools

#### **Ruff (Linting & Formatting)**
```bash
uv run ruff format .                    # Format code
uv run ruff check --fix llm_ci_runner/ # Lint and auto-fix
```

**Configuration**: See `pyproject.toml` for detailed settings

#### **MyPy (Type Checking)**
```bash
uv run mypy llm_ci_runner/
```

**Configuration**: Strict type checking enabled in `pyproject.toml`

#### **Pytest (Testing)**
```bash
uv run pytest tests/unit/ -v          # Unit tests
uv run pytest tests/integration/ -v   # Integration tests
uv run pytest acceptance/ -v           # Acceptance tests
```

**Coverage**: Minimum 85% coverage required

## 🔧 Project Structure (Auto-updated by AI, but may be outdated)

```
llm_ci_runner/
├── __init__.py              # Package initialization
├── core.py                  # Main CLI entry point
├── llm_execution.py         # LLM execution logic
├── llm_service.py           # Service layer
├── schema.py                # Schema handling
├── io_operations.py         # I/O operations
├── templates.py             # Template processing
├── formatters.py            # Output formatting
├── exceptions.py            # Custom exceptions
└── logging_config.py        # Logging configuration

tests/
├── unit/                    # Unit tests (heavy mocking)
├── integration/             # Integration tests
└── conftest.py             # Shared test fixtures

examples/                    # Usage examples
├── 01-basic/               # Basic examples
├── 02-devops/              # DevOps scenarios
├── 03-security/            # Security analysis
├── 04-ai-first/            # AI-first development
└── 05-templates/           # Template workflows

scripts/
├── check.sh                # Quality check script
├── release.py              # Release automation
└── generate-release-notes.py # Release notes generation
```

## 🚨 Quality Gates

### **Pre-commit Checklist**
- [ ] Code follows Python style guide
- [ ] All quality gates pass (`./scripts/check.sh`)
- [ ] Documentation updated (if applicable)

### **Pull Request Requirements**
- [ ] Descriptive title following conventional commits
- [ ] Clear description of changes and rationale
- [ ] All CI checks passing
- [ ] Tests added for new functionality, check the coverage (auto calculated by CI and added to you PR)
- [ ] Documentation updated (if applicable)
- [ ] No breaking changes (or clearly documented)

## 📚 Documentation Standards (AI first)

### **Inline Comments**
- Keep all existing code comments (fix typos, adjust to new code, never remove)
- Add descriptive inline comments for long-term memory (for AI)
- Write complete sentences with proper capitalization

### **Docstrings**
- Use Google Style Python Docstrings
- Every file and class must explain its PURPOSE
- Document parameters, return values, and exceptions

### **README Updates**
- Update relevant sections when adding features
- Include usage examples
- Update installation instructions if needed

### **Lessons learned**
- Add lessons learned to the [lessons-learned.md](.cursor/rules/lessons-learned.md) file.
- Memories update in [memories.md](.cursor\memories.md)

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Environment details**
   - Python version
   - Operating system
   - Package version (`pip show llm-ci-runner`)

2. **Reproduction steps**
   - Clear, step-by-step instructions
   - Minimal example to reproduce the issue

3. **Expected vs actual behavior**
   - What you expected to happen
   - What actually happened

4. **Error messages**
   - Full error traceback
   - Any relevant log output when running with `--log-level DEBUG`

## 💡 Feature Requests

When suggesting features:

1. **Clear problem statement**
   - What problem does this solve?
   - Who would benefit from this feature?

2. **Proposed solution**
   - How should this work?
   - Any implementation ideas?

3. **Use case examples**
   - Real-world scenarios where this would be useful
   - Expected user workflow

## 🤝 Code Review Process

### **Review Guidelines**
- Focus on functionality and correctness
- Check for security implications
- Verify test coverage
- Ensure documentation is updated

### **Review Checklist**
- [ ] Code follows project standards
- [ ] Tests are comprehensive and behavior-focused
- [ ] Error handling is appropriate
- [ ] Documentation is clear and complete
- [ ] No security vulnerabilities introduced

## 🔒 Security Guidelines

### **Best Practices**
- Never commit secrets or API keys
- Use environment variables for configuration
- Validate all user inputs
- Follow principle of least privilege
- Keep dependencies updated
- Run `uv run pip-audit` to check for security vulnerabilities
- Update dependencies when possible with `uv sync --group dev` and commit the `uv.lock` file

### **Security Checks**
- Run `uv run pip-audit` regularly
- Review dependency updates for security implications
- Test with malicious inputs
- Validate schema enforcement

## 🎯 Success Metrics

A good contribution should:

1. **Solve a real problem** - Address actual user needs
2. **Follow established patterns** - Use existing code structure
3. **Include comprehensive tests** - Behavior-focused test coverage
4. **Maintain quality standards** - Pass all quality gates
5. **Update documentation** - Keep docs current and helpful
7. **Think about security** - Follow security best practices

## 📞 Getting Help

- **Issues**: [GitHub Issues](https://github.com/Nantero1/ai-first-devops-toolkit/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Nantero1/ai-first-devops-toolkit/discussions)
- **Documentation**: [Project README](README.md)

## 🙏 Recognition

Contributors will be recognized in:
- Release notes
- Project documentation
- GitHub contributors list

Thank you for contributing to the AI-First DevOps Toolkit! 🚀 