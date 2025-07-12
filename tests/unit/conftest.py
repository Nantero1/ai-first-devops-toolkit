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
