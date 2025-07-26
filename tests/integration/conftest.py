"""
Integration test fixtures and configuration for LLM Runner.

This file provides fixtures specific to integration testing with minimal mocking.
These tests focus on testing the interactions between components with
mocked external HTTP APIs (Azure OpenAI) but real internal logic.
"""

import json
from pathlib import Path

import pytest
import respx
from httpx import Response

from tests.integration.integration_helpers import IntegrationTestHelper


def _get_base_mock_config():
    """
    Get base configuration for mock responses shared between services.
    Only service-specific differences should be overridden.
    """
    return {
        "model": "gpt-4",
        "response_id": "chatcmpl-test-123",
        "structured_sentiment": "neutral",
        "structured_confidence": 0.85,
        "structured_summary": "This is a mock response for testing purposes.",
        "structured_key_points": ["Mock response", "Testing mode active"],
        "usage": {
            "prompt_tokens": 50,
            "completion_tokens": 20,
            "total_tokens": 70,
        },
    }


def _create_mock_chat_response(request, service_config):
    """
    Create a dynamic chat response based on request settings and service configuration.

    Args:
        request: The HTTP request object containing the chat completion request
        service_config: Dict containing service-specific configuration like model, id_prefix, etc.

    Returns:
        Response: HTTP response object with appropriate chat completion data
    """
    try:
        request_data = json.loads(request.content)

        # Check if structured output is requested
        if "response_format" in request_data and request_data["response_format"]:
            # Structured output response
            mock_response = {
                "sentiment": service_config["structured_sentiment"],
                "confidence": service_config["structured_confidence"],
                "summary": service_config["structured_summary"],
                "key_points": service_config["structured_key_points"],
            }
            content = json.dumps(mock_response)
        else:
            # Text output response
            content = service_config["text_response"]

        # Create chat completion API response format
        response_data = {
            "id": service_config["response_id"],
            "object": "chat.completion",
            "created": 1234567890,
            "model": service_config["model"],
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": service_config["usage"]["prompt_tokens"],
                "completion_tokens": service_config["usage"]["completion_tokens"],
                "total_tokens": service_config["usage"]["total_tokens"],
            },
        }

        return Response(200, json=response_data, headers={"content-type": "application/json"})
    except Exception as e:
        # Return error response if something goes wrong
        error_response = {
            "error": {
                "message": f"{service_config['error_prefix']}: {str(e)}",
                "type": "internal_error",
            }
        }

        # Add error code for OpenAI (they include it in their error format)
        if "error_code" in service_config:
            error_response["error"]["code"] = service_config["error_code"]

        return Response(
            500,
            json=error_response,
            headers={"content-type": "application/json"},
        )


def _setup_chat_completion_mock(respx_mock, base_url, service_config):
    """
    Setup mock for chat completion endpoint with given configuration.

    Args:
        respx_mock: The respx mock object
        base_url: The URL to mock
        service_config: Service-specific configuration dict

    Returns:
        The respx_mock object for chaining
    """

    def create_response(request):
        return _create_mock_chat_response(request, service_config)

    respx_mock.post(base_url).mock(side_effect=create_response)
    return respx_mock


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
    base_url = "https://test-openai.openai.azure.com/openai/deployments/gpt-4o/chat/completions"

    azure_config = _get_base_mock_config()
    azure_config.update(
        {
            "text_response": "This is a mock response from the test Azure service. The integration test is working correctly.",
            "error_prefix": "Mock error",
        }
    )

    return _setup_chat_completion_mock(respx_mock, base_url, azure_config)


@pytest.fixture
def mock_openai_responses(respx_mock):
    """
    Setup mock responses for official OpenAI API endpoints.

    This fixture configures realistic OpenAI API responses for:
    - Chat completions (both text and structured output)
    - Authentication headers
    - Error responses
    """
    base_url = "https://api.openai.com/v1/chat/completions"

    openai_config = _get_base_mock_config()
    openai_config.update(
        {
            "text_response": "This is a mock response from the OpenAI service. The integration test is working correctly.",
            "error_prefix": "OpenAI mock error",
            "error_code": "internal_server_error",  # OpenAI-specific field
        }
    )

    return _setup_chat_completion_mock(respx_mock, base_url, openai_config)


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


@pytest.fixture
def integration_helper(temp_integration_workspace):
    """
    Provide IntegrationTestHelper instance for reducing test code duplication.

    This fixture creates a helper instance that provides common functionality
    for file creation, CLI argument building, and result validation across
    integration tests.
    """
    return IntegrationTestHelper(temp_integration_workspace)
