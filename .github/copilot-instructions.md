# GitHub Copilot Instructions

This file provides comprehensive guidance to AI to assist with development tasks in this Python project. Follow these instructions for all code generation, documentation, and testing activities.

## 🐍 Python Development Standards

### Code Style & Structure
- **Base Standard**: Google Python Style Guide with PEP 8 compliance
- **Line Length**: 120 characters maximum
- **Purpose Documentation**: Every file and class must explain its purpose with detailed docstrings
- **Readability First**: Code is read more often than written - prioritize clarity
- **Linting**: Use `ruff check` and `ruff format` for code quality and formatting
- **Type Checking**: Use `mypy` for static type checking to catch type-related issues early

### Import Organization
```python
from __future__ import annotations

# Standard library
import os
from typing import Dict, List, Optional

# Third-party
import requests
from pydantic import BaseModel, Field

# Project imports
from mixins.mixin_secrets import SecretsMixin
from our_utils.our_logger import get_formatted_logger
```

### Class Documentation Pattern
```python
class PaymentProcessor:
    """Processes payments through multiple payment gateways.
    
    Provides unified interface for Stripe, PayPal, and Square payments.
    Handles validation, error handling, and transaction logging with
    automatic retry logic for failed transactions.
    
    Attributes:
        retry_attempts: Number of retries for failed transactions.
        supported_currencies: List of supported currency codes.
    """
```

### Error Handling Patterns
- Use specific exception types with descriptive messages
- Implement fallback mechanisms - avoid crashes when possible
- Log errors but continue with sane defaults
- Use `ToolException` for external service errors

```python
from langchain_core.tools import ToolException

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

### Domain Models with Pydantic
```python
from pydantic import BaseModel, Field
from datetime import datetime

class User(BaseModel):
    """Domain aggregate for user data and business logic."""
    
    id: str = Field(..., description="Unique user identifier")
    preferences: Dict[str, Any] = Field(
        default_factory=dict, 
        description="User preferences and settings"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="User creation timestamp"
    )
    
    def has_active_subscription(self) -> bool:
        """Check if user has an active subscription."""
        return self.subscription is not None and self.subscription.is_active
```

## 🧪 Testing Standards

### Test Structure & Organization
- **Directory Structure**: Mirror source code structure in `tests/unit/` and `tests/integration/`
- **File Naming**: Prefix with `test_` and mirror source structure
- **Given-When-Then Pattern**: Mandatory for all tests

### Test Template
```python
class TestMyComponent:
    """Tests for MyComponent class."""
    
    def test_basic_functionality(self, component):
        """Test basic component functionality."""
        # given
        input_data = "test input"
        
        # when
        result = component.process(input_data)
        
        # then
        assert result == "expected output"
    
    @pytest.mark.parametrize("input_data, expected", [
        pytest.param("input1", "output1", id="scenario1"),
        pytest.param("input2", "output2", id="scenario2"),
    ])
    def test_multiple_scenarios(self, input_data, expected):
        """Test multiple scenarios with different inputs."""
        # given
        component = ComponentUnderTest()
        
        # when
        result = component.process(input_data)
        
        # then
        assert result == expected
```

### Async Testing
```python
@pytest.mark.asyncio
async def test_async_functionality(self):
    """Test async operations."""
    # given
    mock_service = AsyncMock()
    mock_service.process.return_value = "async_result"
    
    # when
    result = await component.async_method()
    
    # then
    assert result == "async_result"
    mock_service.process.assert_called_once()
```

### Testing Best Practices
- Use Given-When-Then structure for all tests
- Group related tests in classes
- Use descriptive test names explaining what is being tested
- Leverage autouse fixtures - don't manually mock what's auto-mocked
- Test both success and error paths
- Use parametrization for multiple scenarios
- Keep tests focused with one assertion per test concept

## 📝 Documentation Standards

### Inline Code Documentation
- **Keep all existing comments** - only remove if wrong, not helpful, or outdated
- **Quantum-detailed documentation** - explain why code is needed and its purpose in the bigger picture
- **Context-aware explanations** - show how components fit into the larger system
- **Cross-referencing** - link related documentation
- **Real-time updates** - maintain documentation as code changes

### Documentation Categories
1. **Inline Code Documentation**: Complex code blocks must include:
   - Feature context explaining component's role
   - Dependency listings that auto-update
   - Usage examples that stay current
   - Performance considerations
   - Security implications

2. **Feature Documentation**: Each feature requires:
   - Feature overview
   - Detailed implementation explanations
   - Comprehensive dependency mapping
   - Current usage examples
   - Security consideration notes

### Comment Style
- Use `#` followed by a space
- Write complete sentences with proper capitalization
- Keep comments up-to-date with code changes
- Comment only when code is not self-explanatory

## 🔄 Git Commit Standards

### Conventional Commits Format
- **Types**: `feat`, `fix`, `build`, `chore`, `ci`, `docs`, `style`, `test`, `perf`, `refactor`
- **Title**: Keep under 60 characters, use present tense
- **Focus on Purpose**: Explain why the change was made, not just what was changed
- **Body**: Include detailed explanation for complex changes

### Commit Message Examples
```bash
# Basic commit
git commit -m "fix: enhance user registration validation to prevent invalid data entry"

# Commit with body
git commit -m "feat(auth): introduce two-factor authentication to strengthen account security

- implement sms and email options for 2fa to provide flexibility
- update user model to store 2fa preferences, ensuring personalized security settings
- create new api endpoints for 2fa setup and verification, facilitating easy integration"

# Commit with resolved issues
git commit -m "docs: expand troubleshooting steps for arm64 architecture on macOS to aid developers

- clarify the instruction to replace debuggerPath in launch.json, reducing setup confusion
- add steps to verify compatibility of cmake, clang, and clang++ with arm64 architecture, ensuring smooth development
- provide example output for architecture verification commands, aiding in quick identification of issues"
```

## 🏗️ Project Architecture

### Module Structure
```python
"""Brief description of module's business purpose."""

from __future__ import annotations

# Imports...

LOGGER = get_formatted_logger(__name__)

# Constants
DEFAULT_TIMEOUT = 30

# Classes and functions...
```

### Key Development Principles
1. **PURPOSE-Driven**: Every file and class explains its business purpose
2. **Validation-Heavy**: Extensive Pydantic validation with examples
3. **Error-Specific**: Descriptive error messages with proper exception types
4. **Test-Structured**: Given-When-Then pattern with comprehensive coverage
5. **Async-Aware**: Proper async/sync patterns using utilities
6. **Fallback-Mechanisms**: Log errors but try not to crash, use sane fallbacks
7. **Performance-conscious**: Use efficient coding patterns
8. **Security-aware**: Consider security implications in all implementations
9. **Type-Safe**: Use mypy for static type checking and catch issues early
10. **Lint-Clean**: Ensure ruff passes for code quality and consistency

## 🚀 Development Workflow

### Code Generation Guidelines
- Always include descriptive inline comments for long-term memory
- Use Pydantic models for type safety
- Follow established patterns from existing codebase
- Implement comprehensive error handling with fallbacks
- Add unit tests for new functionality
- Update documentation as code changes

### Quality Assurance
- Verify all imports are properly organized
- Ensure error handling covers edge cases
- Validate that tests follow Given-When-Then pattern
- Check that documentation explains purpose and context
- Confirm code follows PEP 8 and project style guidelines
- **Pre-commit Checks**: Run `ruff check` and `ruff format` before committing
- **Type Safety**: Ensure `mypy` passes with no type errors
- **CI Compliance**: All code must pass the CI pipeline (linting, type checking, tests)

### Performance Considerations
- Use efficient data structures and algorithms
- Implement caching where appropriate
- Consider memory usage and garbage collection
- Profile code for bottlenecks in critical paths
- Use async patterns for I/O operations

## 🔒 Security Guidelines

### Input Validation
- Validate all user inputs with Pydantic models
- Sanitize data before processing
- Use parameterized queries for database operations
- Implement rate limiting for API endpoints

### Error Handling
- Don't expose sensitive information in error messages
- Log security events appropriately
- Use secure defaults for configuration
- Implement proper authentication and authorization

### Code Security
- Avoid hardcoded secrets in code
- Use environment variables for configuration
- Implement proper session management
- Follow OWASP security guidelines

# Command Output Handling

Whenever you run a command in the terminal, pipe the output to a file, output.txt, that you can read from. Make sure to overwrite each time so that it doesn't grow too big. There is a bug in the current version of Copilot that causes it to not read the output of commands correctly. This workaround allows you to read the output from the temporary file instead. 

# Progress and task tracking

Always update .cursor/scratchpad.md to keep track of your progress and tasks. This file serves as a scratchpad for ongoing work, ideas, and reminders. Use it to document what you have done, what needs to be done, and any issues you encounter. Make sure to read the file before starting a new task to understand the current state of the project.

---

*This file serves as the primary source of truth for GitHub Copilot assistance. Follow these guidelines for all code generation, documentation, and testing activities to maintain consistency and quality across the project.* 