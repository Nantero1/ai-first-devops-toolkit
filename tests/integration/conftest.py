"""
Integration test fixtures and configuration for LLM Runner.

This file provides fixtures specific to integration testing with minimal mocking.
These tests focus on testing the interactions between components with
mocked external services (Azure OpenAI) but real internal logic.
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest
import respx
from httpx import Response


@pytest.fixture(autouse=True)
def mock_azure_service(monkeypatch):
    """
    Mock Azure environment variables for integration testing.

    This fixture sets up the integration test environment by:
    1. Setting required Azure OpenAI environment variables
    2. Providing realistic test endpoints and credentials

    The actual HTTP calls are mocked by the respx_mock fixture.
    """
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://test-openai.openai.azure.com")
    monkeypatch.setenv("AZURE_OPENAI_MODEL", "gpt-4o")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test-api-key-12345")
    monkeypatch.setenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")


@pytest.fixture
def respx_mock():
    """
    Mock HTTP requests to Azure OpenAI API using respx.

    This fixture provides proper HTTP-level mocking for Azure OpenAI
    requests, replacing the need for test helper classes in production code.
    """
    with respx.mock:
        yield respx


@pytest.fixture
def mock_azure_openai_responses(respx_mock):
    """
    Setup mock responses for Azure OpenAI API endpoints.

    This fixture configures realistic Azure OpenAI API responses for:
    - Chat completions (both text and structured output)
    - Authentication headers
    - Error responses
    """
    # Mock the chat completions endpoint
    base_url = "https://test-openai.openai.azure.com/openai/deployments/gpt-4o/chat/completions"

    def create_chat_response(request):
        """Create a dynamic chat response based on request settings."""
        try:
            request_data = json.loads(request.content)

            # Check if structured output is requested
            if "response_format" in request_data and request_data["response_format"]:
                # Structured output response
                mock_response = {
                    "sentiment": "neutral",
                    "confidence": 0.85,
                    "summary": "This is a mock response for testing purposes.",
                    "key_points": ["Mock response", "Testing mode active"],
                }
                content = json.dumps(mock_response)
            else:
                # Text output response
                content = (
                    "This is a mock response from the test Azure service. The integration test is working correctly."
                )

            # Create Azure OpenAI API response format
            response_data = {
                "id": "chatcmpl-test-123",
                "object": "chat.completion",
                "created": 1234567890,
                "model": "gpt-4o",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": content},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 50,
                    "completion_tokens": 20,
                    "total_tokens": 70,
                },
            }

            return Response(200, json=response_data, headers={"content-type": "application/json"})
        except Exception as e:
            # Return error response if something goes wrong
            return Response(
                500,
                json={
                    "error": {
                        "message": f"Mock error: {str(e)}",
                        "type": "internal_error",
                    }
                },
                headers={"content-type": "application/json"},
            )

    # Register the mock route
    respx_mock.post(base_url).mock(side_effect=create_chat_response)

    return respx_mock


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
    """
    Mock Azure service for integration tests with realistic behavior.

    This fixture provides a mock service for tests that need to directly
    manipulate the mock responses. Most tests should rely on the built-in
    test mode instead.
    """
    mock_service = AsyncMock()

    # Default response for get_chat_message_contents
    mock_service.get_chat_message_contents = AsyncMock()

    return mock_service


@pytest.fixture
def mock_openai_service(monkeypatch):
    """
    Mock OpenAI environment variables for integration testing.
    Sets required OpenAI env vars for integration tests.
    """
    monkeypatch.setenv("OPENAI_API_KEY", "non-an-api-key")
    monkeypatch.setenv("OPENAI_CHAT_MODEL_ID", "gpt-4-test")
    # Optionally: monkeypatch.setenv("OPENAI_ORG_ID", "org-test")
    # Optionally: monkeypatch.setenv("OPENAI_BASE_URL", "https://api.openai.com/v1")


@pytest.fixture
def integration_mock_openai_service():
    """
    Mock OpenAI service for integration tests with realistic behavior.
    Mirrors integration_mock_azure_service but for OpenAI.
    """
    mock_service = AsyncMock()
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
