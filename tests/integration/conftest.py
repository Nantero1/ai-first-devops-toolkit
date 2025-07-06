"""
Integration test fixtures and configuration for LLM Runner.

This file provides fixtures specific to integration testing with minimal mocking.
These tests focus on testing the interactions between components with
mocked external services (Azure OpenAI) but real internal logic.
"""

from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest


@pytest.fixture
def mock_llm_response_structured():
    """Mock LLM response for structured output testing."""
    mock_content = Mock()
    mock_content.content = '{"sentiment":"neutral","confidence":0.85,"summary":"CI/CD automates software integration and deployment processes for improved efficiency."}'
    mock_content.role = "assistant"
    return [mock_content]


@pytest.fixture
def mock_llm_response_text():
    """Mock LLM response for text output testing."""
    mock_content = Mock()
    mock_content.content = "CI/CD stands for Continuous Integration and Continuous Deployment. It's a set of practices that automates the building, testing, and deployment of software, enabling teams to deliver code changes more frequently and reliably."
    mock_content.role = "assistant"
    return [mock_content]


@pytest.fixture
def mock_llm_response_pr_review():
    """Mock LLM response for PR review testing."""
    mock_content = Mock()
    mock_content.content = """## Code Review Summary

**Security Issues Fixed:**
✅ SQL injection vulnerability resolved by using parameterized queries
✅ Input validation added for user_id parameter

**Code Quality:**
- Good use of parameterized queries
- Proper error handling with ValueError for invalid input
- Consistent coding style

**Recommendations:**
- Consider adding logging for security events
- Add unit tests for the new validation logic

**Overall Assessment:** This PR successfully addresses the SQL injection vulnerability and adds appropriate input validation. The changes follow security best practices."""
    mock_content.role = "assistant"
    return [mock_content]


@pytest.fixture
def integration_mock_azure_service():
    """Mock Azure service for integration tests with realistic behavior."""
    mock_service = AsyncMock()

    # Default response for get_chat_message_contents
    mock_service.get_chat_message_contents = AsyncMock()

    return mock_service


@pytest.fixture
def example_files_paths():
    """Paths to example files for integration testing."""
    return {
        "simple": Path("examples/simple-example.json"),
        "pr_review": Path("examples/pr-review-example.json"),
        "minimal": Path("examples/minimal-example.json"),
        "structured_output": Path("examples/structured-output-example.json"),
        "code_review_schema": Path("examples/code_review_schema.json"),
    }


@pytest.fixture
def integration_environment_check():
    """Check if integration test environment is properly set up."""
    # For integration tests, we still mock the actual Azure service
    # but test the full pipeline with real file operations and logic
    return {
        "mock_azure": True,
        "real_files": True,
        "real_json_parsing": True,
        "real_schema_validation": True,
    }


@pytest.fixture
def temp_integration_workspace(tmp_path):
    """Create a temporary workspace for integration tests."""
    workspace = tmp_path / "integration_test_workspace"
    workspace.mkdir()

    # Create subdirectories
    (workspace / "input").mkdir()
    (workspace / "output").mkdir()
    (workspace / "schemas").mkdir()

    return workspace
