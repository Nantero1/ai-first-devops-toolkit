"""
Unit test fixtures and configuration for LLM Runner.

This file provides fixtures specific to unit testing with heavy mocking
of external dependencies like Azure services and file operations.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest


@pytest.fixture
def mock_console(monkeypatch):
    """Mock Rich console for unit tests."""
    mock_console = Mock()
    monkeypatch.setattr("llm_ci_runner.CONSOLE", mock_console)
    return mock_console


@pytest.fixture
def mock_logger(monkeypatch):
    """Mock logger for unit tests."""
    mock_logger = Mock()
    # Mock the logger in io_operations module where it's actually used
    monkeypatch.setattr("llm_ci_runner.io_operations.LOGGER", mock_logger)
    return mock_logger


@pytest.fixture
def mock_azure_credential():
    """Mock Azure credential for authentication tests."""
    mock_credential = AsyncMock()
    mock_credential.get_token = AsyncMock()
    return mock_credential


@pytest.fixture
def mock_azure_chat_completion():
    """Mock Azure ChatCompletion service."""
    with patch("llm_ci_runner.llm_service.AzureChatCompletion") as mock_class:
        mock_service = AsyncMock()
        mock_class.return_value = mock_service
        yield mock_service


@pytest.fixture
def mock_kernel():
    """Mock Semantic Kernel for unit tests."""
    with patch("llm_ci_runner.llm_execution.Kernel") as mock_kernel_class:
        mock_kernel = Mock()
        mock_kernel_class.return_value = mock_kernel
        yield mock_kernel


@pytest.fixture
def mock_chat_history():
    """Mock ChatHistory for unit tests."""
    with patch("llm_ci_runner.io_operations.ChatHistory") as mock_chat_history_class:
        mock_history = Mock()
        # Configure messages attribute to support len()
        mock_history.messages = []
        mock_chat_history_class.return_value = mock_history
        yield mock_history


@pytest.fixture
def mock_file_operations():
    """Mock file operations for unit tests."""
    with (
        patch("builtins.open", create=True) as mock_open,
        patch("pathlib.Path.exists") as mock_exists,
        patch("pathlib.Path.mkdir") as mock_mkdir,
    ):
        mock_exists.return_value = True
        yield {"open": mock_open, "exists": mock_exists, "mkdir": mock_mkdir}


@pytest.fixture
def mock_environment_variables(monkeypatch):
    """Mock environment variables for unit tests."""
    env_vars = {
        "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
        "AZURE_OPENAI_MODEL": "gpt-4-test",
        "AZURE_OPENAI_API_VERSION": "2024-12-01-preview",
        "AZURE_OPENAI_API_KEY": "test-api-key",
    }

    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    return env_vars


@pytest.fixture
def mock_semantic_kernel_imports():
    """Mock all Semantic Kernel imports for unit tests."""
    with (
        patch("llm_ci_runner.llm_execution.Kernel") as mock_kernel,
        patch("llm_ci_runner.io_operations.ChatHistory") as mock_chat_history,
        patch("llm_ci_runner.io_operations.ChatMessageContent") as mock_chat_content,
        patch("llm_ci_runner.io_operations.AuthorRole") as mock_author_role,
        patch("llm_ci_runner.llm_execution.OpenAIChatPromptExecutionSettings") as mock_settings,
    ):
        yield {
            "kernel": mock_kernel,
            "chat_history": mock_chat_history,
            "chat_content": mock_chat_content,
            "author_role": mock_author_role,
            "settings": mock_settings,
        }


# AUTOUSE FIXTURES - Automatically applied to ALL unit tests
@pytest.fixture(autouse=True)
def mock_external_apis(request):
    """Autouse fixture to mock all external API calls in unit tests."""
    # Skip mocking for tests that specifically test client creation errors or SDK fallback behavior
    skip_conditions = [
        "client_creation" in request.node.name.lower(),
        "missing_" in request.node.name.lower(),
        "sdk_fallback" in request.node.name.lower(),
        "fallback" in request.node.name.lower(),
    ]

    if any(skip_conditions):
        yield None
        return

    # Mock Azure OpenAI client
    mock_azure_response = Mock()
    mock_azure_response.choices = [Mock()]
    mock_azure_response.choices[0].message = Mock()
    mock_azure_response.choices[0].message.content = '{"test": "result"}'

    # Mock OpenAI client
    mock_openai_response = Mock()
    mock_openai_response.choices = [Mock()]
    mock_openai_response.choices[0].message = Mock()
    mock_openai_response.choices[0].message.content = '{"test": "result"}'

    with (
        patch("llm_ci_runner.llm_execution.AsyncAzureOpenAI") as mock_azure_client,
        patch("llm_ci_runner.llm_execution.AsyncOpenAI") as mock_openai_client,
        patch("llm_ci_runner.llm_execution._create_azure_client") as mock_create_azure,
        patch("llm_ci_runner.llm_execution._create_openai_client") as mock_create_openai,
    ):
        # Configure Azure client
        mock_azure_instance = AsyncMock()
        mock_azure_instance.beta.chat.completions.parse = AsyncMock(return_value=mock_azure_response)
        mock_azure_instance.chat.completions.create = AsyncMock(return_value=mock_azure_response)
        mock_create_azure.return_value = mock_azure_instance
        mock_azure_client.return_value = mock_azure_instance

        # Configure OpenAI client
        mock_openai_instance = AsyncMock()
        mock_openai_instance.beta.chat.completions.parse = AsyncMock(return_value=mock_openai_response)
        mock_openai_instance.chat.completions.create = AsyncMock(return_value=mock_openai_response)
        mock_create_openai.return_value = mock_openai_instance
        mock_openai_client.return_value = mock_openai_instance

        yield {
            "azure_client": mock_azure_instance,
            "openai_client": mock_openai_instance,
        }


# Removed unnecessary mock_realistic_chat_history_behavior fixture
# Tests can create simple chat_history data directly: [{"role": "user", "content": "Hello"}]


@pytest.fixture(autouse=True)
def clear_azure_environment_for_openai_tests(request, monkeypatch):
    """Autouse fixture to clear Azure env vars for OpenAI-specific tests."""
    # Only clear Azure env vars if test name contains 'openai'
    if "openai" in request.node.name.lower():
        monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
        monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
        # Set OpenAI env vars
        monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
        monkeypatch.setenv("OPENAI_CHAT_MODEL_ID", "gpt-4")
