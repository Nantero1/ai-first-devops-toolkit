"""
Unit tests for Semantic Kernel related functions in llm_runner.py

Tests create_chat_history, setup_azure_service, and execute_llm_task functions
with heavy mocking following the Given-When-Then pattern.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path

from llm_runner import (
    create_chat_history,
    setup_azure_service,
    execute_llm_task,
    InputValidationError,
    AuthenticationError,
    LLMExecutionError,
)
from tests.mock_factory import (
    create_structured_output_mock,
    create_text_output_mock,
    create_error_response_mock,
)


class TestCreateChatHistory:
    """Tests for create_chat_history function."""

    def test_create_chat_history_with_valid_messages(
        self, sample_input_messages, mock_semantic_kernel_imports
    ):
        """Test creating ChatHistory with valid message structure."""
        # given
        messages = sample_input_messages
        mock_chat_history = mock_semantic_kernel_imports["chat_history"]()

        # when
        result = create_chat_history(messages)

        # then
        # Verify ChatHistory was created
        mock_semantic_kernel_imports["chat_history"].assert_called_once()
        # Verify messages were added (2 calls for 2 messages)
        assert mock_chat_history.add_message.call_count == 2

    def test_create_chat_history_with_named_user_message(
        self, mock_semantic_kernel_imports
    ):
        """Test creating ChatHistory with named user message."""
        # given
        messages = [
            {"role": "user", "content": "Hello, assistant!", "name": "test_user"}
        ]
        mock_chat_history = mock_semantic_kernel_imports["chat_history"]()

        # when
        result = create_chat_history(messages)

        # then
        mock_chat_history.add_message.assert_called_once()
        # Verify ChatMessageContent was created with name
        call_args = mock_semantic_kernel_imports["chat_content"].call_args
        assert call_args[1]["name"] == "test_user"

    def test_create_chat_history_with_missing_role_raises_error(
        self, mock_semantic_kernel_imports
    ):
        """Test that message without role raises InputValidationError."""
        # given
        messages = [
            {
                "content": "Hello, assistant!"
                # Missing "role" field
            }
        ]

        # when & then
        with pytest.raises(
            InputValidationError,
            match="Message 0 missing required 'role' or 'content' field",
        ):
            create_chat_history(messages)

    def test_create_chat_history_with_missing_content_raises_error(
        self, mock_semantic_kernel_imports
    ):
        """Test that message without content raises InputValidationError."""
        # given
        messages = [
            {
                "role": "user"
                # Missing "content" field
            }
        ]

        # when & then
        with pytest.raises(
            InputValidationError,
            match="Message 0 missing required 'role' or 'content' field",
        ):
            create_chat_history(messages)

    def test_create_chat_history_with_invalid_role_raises_error(
        self, mock_semantic_kernel_imports
    ):
        """Test that invalid role raises InputValidationError."""
        # given
        messages = [{"role": "invalid_role", "content": "Hello, assistant!"}]
        # Mock AuthorRole to raise ValueError for invalid role
        mock_semantic_kernel_imports["author_role"].side_effect = ValueError(
            "Invalid role"
        )

        # when & then
        with pytest.raises(
            InputValidationError, match="Invalid role 'invalid_role' in message 0"
        ):
            create_chat_history(messages)

    def test_create_chat_history_with_chat_content_error_raises_input_error(
        self, mock_semantic_kernel_imports
    ):
        """Test that ChatMessageContent creation errors are wrapped in InputValidationError."""
        # given
        messages = [{"role": "user", "content": "Hello, assistant!"}]
        # Mock ChatMessageContent to raise an exception
        mock_semantic_kernel_imports["chat_content"].side_effect = Exception(
            "ChatContent error"
        )

        # when & then
        with pytest.raises(InputValidationError, match="Error processing message 0"):
            create_chat_history(messages)


class TestSetupAzureService:
    """Tests for setup_azure_service function."""

    @pytest.mark.asyncio
    async def test_setup_azure_service_with_api_key(
        self, mock_environment_variables, mock_azure_chat_completion
    ):
        """Test setting up Azure service with API key authentication."""
        # given
        # Environment variables are already set by fixture

        # when
        result = await setup_azure_service()

        # then
        assert result is not None
        # Verify AzureChatCompletion was called with correct parameters
        mock_azure_chat_completion.assert_called_once()

    @pytest.mark.asyncio
    async def test_setup_azure_service_with_rbac_auth(self, mock_azure_chat_completion):
        """Test setting up Azure service with RBAC authentication."""
        # given
        # Set environment without API key to force RBAC
        with patch.dict(
            "os.environ",
            {
                "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
                "AZURE_OPENAI_MODEL": "gpt-4-test",
                "AZURE_OPENAI_API_VERSION": "2024-08-01-preview",
            },
            clear=True,
        ):

            # when
            with patch("llm_runner.DefaultAzureCredential") as mock_credential:
                result = await setup_azure_service()

        # then
        assert result is not None
        mock_credential.assert_called_once()
        mock_azure_chat_completion.assert_called_once()

    @pytest.mark.asyncio
    async def test_setup_azure_service_without_endpoint_raises_error(self):
        """Test that missing endpoint raises AuthenticationError."""
        # given
        with patch.dict("os.environ", {}, clear=True):

            # when & then
            with pytest.raises(
                AuthenticationError,
                match="AZURE_OPENAI_ENDPOINT environment variable not set",
            ):
                await setup_azure_service()

    @pytest.mark.asyncio
    async def test_setup_azure_service_without_model_raises_error(self):
        """Test that missing model raises AuthenticationError."""
        # given
        with patch.dict(
            "os.environ",
            {"AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/"},
            clear=True,
        ):

            # when & then
            with pytest.raises(
                AuthenticationError,
                match="AZURE_OPENAI_MODEL environment variable not set",
            ):
                await setup_azure_service()

    @pytest.mark.asyncio
    async def test_setup_azure_service_with_auth_error_raises_auth_error(
        self, mock_environment_variables
    ):
        """Test that Azure authentication errors are wrapped in AuthenticationError."""
        # given
        from azure.core.exceptions import ClientAuthenticationError

        # when & then
        with patch(
            "llm_runner.AzureChatCompletion",
            side_effect=ClientAuthenticationError("Auth failed"),
        ):
            with pytest.raises(
                AuthenticationError, match="Azure authentication failed"
            ):
                await setup_azure_service()

    @pytest.mark.asyncio
    async def test_setup_azure_service_with_generic_error_raises_auth_error(
        self, mock_environment_variables
    ):
        """Test that generic errors are wrapped in AuthenticationError."""
        # given
        # when & then
        with patch(
            "llm_runner.AzureChatCompletion", side_effect=Exception("Generic error")
        ):
            with pytest.raises(
                AuthenticationError, match="Error setting up Azure service"
            ):
                await setup_azure_service()


class TestExecuteLlmTask:
    """Tests for execute_llm_task function."""

    @pytest.mark.asyncio
    async def test_execute_llm_task_with_structured_output(
        self, mock_azure_service, mock_chat_history, mock_kernel
    ):
        """Test executing LLM task with structured output schema."""
        # given
        service = mock_azure_service
        chat_history = mock_chat_history
        context = {"session_id": "test-123"}
        schema_model = Mock()
        schema_model.__name__ = "TestSchema"

        # Mock the service response
        mock_response = create_structured_output_mock()
        service.get_chat_message_contents.return_value = mock_response

        # when
        result = await execute_llm_task(service, chat_history, context, schema_model)

        # then
        assert isinstance(result, dict)
        assert "sentiment" in result
        assert result["sentiment"] == "neutral"
        service.get_chat_message_contents.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_llm_task_with_text_output(
        self, mock_azure_service, mock_chat_history, mock_kernel
    ):
        """Test executing LLM task with text output."""
        # given
        service = mock_azure_service
        chat_history = mock_chat_history
        context = {"session_id": "test-123"}
        schema_model = None

        # Mock the service response
        mock_response = create_text_output_mock()
        service.get_chat_message_contents.return_value = mock_response

        # when
        result = await execute_llm_task(service, chat_history, context, schema_model)

        # then
        assert isinstance(result, str)
        assert "CI/CD stands for" in result
        service.get_chat_message_contents.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_llm_task_with_service_error_raises_llm_error(
        self, mock_azure_service, mock_chat_history, mock_kernel
    ):
        """Test that service errors are wrapped in LLMExecutionError."""
        # given
        service = mock_azure_service
        chat_history = mock_chat_history
        context = None
        schema_model = None

        # Mock service to raise an exception
        service.get_chat_message_contents.side_effect = Exception("Service error")

        # when & then
        with pytest.raises(
            LLMExecutionError, match="LLM execution failed: Service error"
        ):
            await execute_llm_task(service, chat_history, context, schema_model)

    @pytest.mark.asyncio
    async def test_execute_llm_task_with_invalid_json_in_structured_mode_raises_error(
        self, mock_azure_service, mock_chat_history, mock_kernel
    ):
        """Test that invalid JSON in structured mode raises LLMExecutionError."""
        # given
        service = mock_azure_service
        chat_history = mock_chat_history
        context = None
        schema_model = Mock()
        schema_model.__name__ = "TestSchema"

        # Mock service to return invalid JSON
        mock_response = [Mock()]
        mock_response[0].content = "invalid json response"
        service.get_chat_message_contents.return_value = mock_response

        # when & then
        with pytest.raises(
            LLMExecutionError, match="Schema enforcement failed - invalid JSON returned"
        ):
            await execute_llm_task(service, chat_history, context, schema_model)

    @pytest.mark.asyncio
    async def test_execute_llm_task_adds_context_to_kernel_arguments(
        self, mock_azure_service, mock_chat_history, mock_kernel
    ):
        """Test that context is properly added to kernel arguments."""
        # given
        service = mock_azure_service
        chat_history = mock_chat_history
        context = {"session_id": "test-123", "user_id": "user-456"}
        schema_model = None

        # Mock the service response
        mock_response = create_text_output_mock()
        service.get_chat_message_contents.return_value = mock_response

        # when
        result = await execute_llm_task(service, chat_history, context, schema_model)

        # then
        # Verify the service was called with the expected arguments
        service.get_chat_message_contents.assert_called_once()
        call_kwargs = service.get_chat_message_contents.call_args[1]
        assert "arguments" in call_kwargs

    @pytest.mark.asyncio
    async def test_execute_llm_task_with_retry_on_transient_error(
        self, mock_azure_service, mock_chat_history, mock_kernel
    ):
        """Test that tenacity retry works on transient errors."""
        # given
        service = mock_azure_service
        chat_history = mock_chat_history
        context = None
        schema_model = None

        # Mock service to fail first time, then succeed
        mock_response = create_text_output_mock()
        service.get_chat_message_contents.side_effect = [
            ConnectionError("Network error"),  # First call fails
            mock_response,  # Second call succeeds
        ]

        # when
        result = await execute_llm_task(service, chat_history, context, schema_model)

        # then
        assert isinstance(result, str)
        # Verify retry happened (called twice)
        assert service.get_chat_message_contents.call_count == 2
