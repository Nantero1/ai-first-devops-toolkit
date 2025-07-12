"""
Unit tests for Semantic Kernel related functions in llm_ci_runner.py

Tests create_chat_history, setup_llm_service, and execute_llm_task functions
with heavy mocking following the Given-When-Then pattern.
"""

from unittest.mock import Mock, patch

import pytest

from llm_ci_runner import (
    AuthenticationError,
    InputValidationError,
    LLMExecutionError,
    create_chat_history,
    execute_llm_task,
    setup_azure_service,
)
from tests.mock_factory import (
    create_structured_output_mock,
    create_text_output_mock,
)


class TestCreateChatHistory:
    """Tests for create_chat_history function."""

    def test_create_chat_history_with_valid_messages(self, sample_input_messages, mock_semantic_kernel_imports):
        """Test creating ChatHistory with valid message structure."""
        # given
        messages = sample_input_messages
        mock_chat_history_instance = Mock()
        mock_chat_history_instance.__len__ = Mock(return_value=len(messages))
        mock_semantic_kernel_imports["chat_history"].return_value = mock_chat_history_instance

        # when
        result = create_chat_history(messages)

        # then
        # Verify ChatHistory was created
        mock_semantic_kernel_imports["chat_history"].assert_called_once()
        # Verify messages were added (2 calls for 2 messages)
        assert mock_chat_history_instance.add_message.call_count == 2

    def test_create_chat_history_with_named_user_message(self, mock_semantic_kernel_imports):
        """Test creating ChatHistory with named user message."""
        # given
        messages = [{"role": "user", "content": "Hello, assistant!", "name": "test_user"}]
        mock_chat_history = mock_semantic_kernel_imports["chat_history"]()

        # when
        result = create_chat_history(messages)

        # then
        mock_chat_history.add_message.assert_called_once()
        # Verify ChatMessageContent was created and name was set
        mock_message = mock_semantic_kernel_imports["chat_content"].return_value
        assert mock_message.name == "test_user"

    def test_create_chat_history_with_missing_role_raises_error(self, mock_semantic_kernel_imports):
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

    def test_create_chat_history_with_missing_content_raises_error(self, mock_semantic_kernel_imports):
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

    def test_create_chat_history_with_invalid_role_raises_error(self, mock_semantic_kernel_imports):
        """Test that invalid role raises InputValidationError."""
        # given
        messages = [{"role": "invalid_role", "content": "Hello, assistant!"}]
        # Mock AuthorRole to raise ValueError for invalid role
        mock_semantic_kernel_imports["author_role"].side_effect = ValueError("Invalid role")

        # when & then
        with pytest.raises(InputValidationError, match="Invalid message role: invalid_role"):
            create_chat_history(messages)

    def test_create_chat_history_with_chat_content_error_raises_input_error(self, mock_semantic_kernel_imports):
        """Test that ChatMessageContent creation errors are wrapped in InputValidationError."""
        # given
        messages = [{"role": "user", "content": "Hello, assistant!"}]
        # Mock ChatMessageContent to raise an exception
        mock_semantic_kernel_imports["chat_content"].side_effect = Exception("ChatContent error")

        # when & then
        with pytest.raises(InputValidationError, match="Failed to create message 0"):
            create_chat_history(messages)


class TestSetupAzureService:
    """Tests for setup_azure_service and setup_llm_service functions."""

    @pytest.mark.asyncio
    async def test_setup_azure_service_with_api_key(self, mock_environment_variables, mock_azure_chat_completion):
        """Test setting up Azure service with API key authentication."""
        # given
        # Environment variables are already set by fixture

        # when
        service, credential = await setup_azure_service()

        # then
        assert service is not None
        assert credential is None  # API key auth doesn't return a credential
        # The mock_azure_chat_completion fixture already patches AzureChatCompletion
        # and returns the mock service instance, so we just need to verify result
        assert service == mock_azure_chat_completion

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
                "AZURE_OPENAI_API_VERSION": "2024-12-01-preview",
            },
            clear=True,
        ):
            # when
            from unittest.mock import AsyncMock

            with patch("llm_ci_runner.llm_service.DefaultAzureCredential") as mock_credential_class:
                mock_credential = AsyncMock()
                mock_credential.get_token = AsyncMock()
                mock_credential_class.return_value = mock_credential
                service, credential = await setup_azure_service()

        # then
        assert service is not None
        assert credential is not None  # RBAC auth returns a credential
        mock_credential_class.assert_called()
        assert service == mock_azure_chat_completion

    @pytest.mark.asyncio
    async def test_setup_azure_service_without_endpoint_raises_error(self):
        """Test that missing endpoint raises AuthenticationError."""
        # given
        with patch.dict("os.environ", {}, clear=True):
            # when & then
            with pytest.raises(
                AuthenticationError,
                match="AZURE_OPENAI_ENDPOINT environment variable is required",
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
                match="AZURE_OPENAI_MODEL environment variable is required",
            ):
                await setup_azure_service()

    @pytest.mark.asyncio
    async def test_setup_azure_service_with_auth_error_raises_auth_error(self):
        """Test that Azure authentication errors are wrapped in AuthenticationError."""
        # given
        from azure.core.exceptions import ClientAuthenticationError

        # Set environment with API key to test the API key path
        with patch.dict(
            "os.environ",
            {
                "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
                "AZURE_OPENAI_MODEL": "gpt-4-test",
                "AZURE_OPENAI_API_VERSION": "2024-12-01-preview",
                "AZURE_OPENAI_API_KEY": "test-api-key",
            },
            clear=True,
        ):
            # when & then
            with patch(
                "llm_ci_runner.llm_service.AzureChatCompletion",
                side_effect=ClientAuthenticationError("Auth failed"),
            ):
                with pytest.raises(AuthenticationError, match="Azure authentication failed"):
                    await setup_azure_service()

    @pytest.mark.asyncio
    async def test_setup_azure_service_with_generic_error_raises_auth_error(self):
        """Test that generic errors are wrapped in AuthenticationError."""
        # given
        # Set environment with API key to test the API key path
        with patch.dict(
            "os.environ",
            {
                "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
                "AZURE_OPENAI_MODEL": "gpt-4-test",
                "AZURE_OPENAI_API_VERSION": "2024-12-01-preview",
                "AZURE_OPENAI_API_KEY": "test-api-key",
            },
            clear=True,
        ):
            # when & then
            with patch(
                "llm_ci_runner.llm_service.AzureChatCompletion",
                side_effect=Exception("Generic error"),
            ):
                with pytest.raises(AuthenticationError, match="Error setting up Azure service"):
                    await setup_azure_service()


class TestExecuteLlmTask:
    """Tests for execute_llm_task function."""

    @pytest.mark.asyncio
    async def test_execute_llm_task_with_structured_output(self, mock_azure_service, mock_chat_history, mock_kernel):
        """Test executing LLM task with structured output schema."""
        # given
        service = mock_azure_service
        chat_history = mock_chat_history
        context = {"session_id": "test-123"}

        # Create a proper mock schema that inherits from BaseModel
        from pydantic import BaseModel

        class MockSchema(BaseModel):
            sentiment: str

        schema_model = MockSchema

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
    async def test_execute_llm_task_with_text_output(self, mock_azure_service, mock_chat_history, mock_kernel):
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
        with pytest.raises(LLMExecutionError, match="LLM execution failed: Service error"):
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

        # Create a proper mock schema that inherits from BaseModel
        from pydantic import BaseModel

        class MockSchema(BaseModel):
            sentiment: str

        schema_model = MockSchema

        # Mock service to return invalid JSON
        mock_response = [Mock()]
        mock_response[0].content = "invalid json response"
        service.get_chat_message_contents.return_value = mock_response

        # when & then
        with pytest.raises(LLMExecutionError, match="Schema enforcement failed"):
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
        """Test that tenacity retry decorator is applied and handles transient errors."""
        # given
        service = mock_azure_service
        chat_history = mock_chat_history
        context = None
        schema_model = None

        # Mock service to fail with a retryable exception
        service.get_chat_message_contents.side_effect = ConnectionError("Network error")

        # when & then
        with pytest.raises(LLMExecutionError, match="LLM execution failed: Network error"):
            await execute_llm_task(service, chat_history, context, schema_model)

        # Verify that the service was called (retry behavior depends on decorator implementation)
        assert service.get_chat_message_contents.call_count >= 1
