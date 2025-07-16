"""
Unit tests for Semantic Kernel related functions in llm_ci_runner.py

Tests create_chat_history, setup_llm_service, and execute_llm_task functions
with heavy mocking following the Given-When-Then pattern.
"""

from unittest.mock import AsyncMock, Mock, patch

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


@pytest.fixture
def mock_chat_history():
    """Mock ChatHistory for unit tests."""
    mock_history = Mock()
    # Make the mock iterable by returning a list of mock messages
    mock_messages = [
        Mock(role="user", content="Hello"),
        Mock(role="assistant", content="Hi there!"),
    ]
    mock_history.__iter__ = Mock(return_value=iter(mock_messages))
    mock_history.messages = mock_messages
    return mock_history


@pytest.fixture
def mock_kernel():
    """Mock Semantic Kernel for unit tests."""
    mock_kernel = Mock()
    # Mock the get_service method to return a mock service
    mock_service = AsyncMock()
    mock_service.get_chat_message_contents = AsyncMock()
    mock_kernel.get_service = Mock(return_value=mock_service)
    return mock_kernel


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
    async def test_execute_llm_task_text_mode(self, mock_kernel):
        """Test executing LLM task in text mode (no schema)."""
        # given
        kernel = mock_kernel
        # Create realistic chat history that supports len() and iteration
        chat_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        schema_file = None
        mock_kernel.get_service.return_value.get_chat_message_contents.return_value = create_text_output_mock()

        # when
        result = await execute_llm_task(kernel, chat_history, schema_file)

        # then
        assert result["mode"] == "text"
        assert "output" in result
        assert result["schema_enforced"] == False

    @pytest.mark.asyncio
    async def test_execute_llm_task_structured_mode(self, mock_kernel):
        """Test executing LLM task in structured mode (with schema)."""
        # given
        kernel = mock_kernel
        # Create realistic chat history that supports len() and iteration
        chat_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        schema_file = "mock_schema_file"

        with patch("llm_ci_runner.llm_execution.load_schema_file") as mock_load_schema:
            mock_schema_model = Mock()
            mock_schema_model.__name__ = "TestSchema"  # Add __name__ attribute
            mock_schema_dict = {
                "type": "object",
                "properties": {"test": {"type": "string"}},
            }
            mock_load_schema.return_value = (mock_schema_model, mock_schema_dict)
            mock_kernel.get_service.return_value.get_chat_message_contents.return_value = (
                create_structured_output_mock()
            )

            # when
            result = await execute_llm_task(kernel, chat_history, schema_file)

            # then
            assert result["mode"] == "structured"
            assert "output" in result
            assert result["schema_enforced"] == True

    @pytest.mark.asyncio
    async def test_execute_llm_task_service_error_raises_llm_error(self, mock_kernel, mock_chat_history):
        """Test that service errors are wrapped in LLMExecutionError."""
        # given
        kernel = mock_kernel
        chat_history = mock_chat_history
        schema_file = None

        # Mock Semantic Kernel to fail
        mock_kernel.get_service.return_value.get_chat_message_contents.side_effect = Exception("Service error")

        # Mock Azure endpoint to trigger Azure SDK path
        with patch.dict(
            "os.environ",
            {"AZURE_OPENAI_ENDPOINT": "https://test.azure.com"},
            clear=True,
        ):
            # when & then
            with pytest.raises(LLMExecutionError, match="Schema enforcement failed with Azure SDK"):
                await execute_llm_task(kernel, chat_history, schema_file)

    @pytest.mark.asyncio
    async def test_execute_llm_task_no_endpoint_raises_error(self, mock_kernel, mock_chat_history):
        """Test that missing endpoint configuration raises LLMExecutionError."""
        # given
        kernel = mock_kernel
        chat_history = mock_chat_history
        schema_file = None

        # Mock Semantic Kernel to fail
        mock_kernel.get_service.return_value.get_chat_message_contents.side_effect = Exception("SK failed")

        # Mock no Azure endpoint and no OpenAI API key
        with patch.dict("os.environ", {}, clear=True):
            # when & then
            with pytest.raises(LLMExecutionError, match="Schema enforcement failed with OpenAI SDK"):
                await execute_llm_task(kernel, chat_history, schema_file)


class TestExecuteTextMode:
    """Tests for _execute_text_mode function."""

    @pytest.mark.asyncio
    async def test_execute_text_mode_with_azure_service(self, mock_kernel):
        """Test _execute_text_mode with azure_openai service."""
        # given
        from llm_ci_runner.llm_execution import _execute_text_mode

        kernel = mock_kernel
        chat_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        # Mock azure_openai service
        mock_azure_service = AsyncMock()
        mock_azure_service.get_chat_message_contents.return_value = create_text_output_mock()
        mock_kernel.get_service.return_value = mock_azure_service

        # when
        result = await _execute_text_mode(kernel, chat_history)

        # then
        assert result["mode"] == "text"
        assert "output" in result
        assert result["schema_enforced"] == False
        mock_kernel.get_service.assert_called_with("azure_openai")

    @pytest.mark.asyncio
    async def test_execute_text_mode_fallback_to_openai_service(self, mock_kernel):
        """Test _execute_text_mode fallback to openai service."""
        # given
        from llm_ci_runner.llm_execution import _execute_text_mode

        kernel = mock_kernel
        chat_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        # Mock openai service (azure_openai not found)
        mock_openai_service = AsyncMock()
        mock_openai_service.get_chat_message_contents.return_value = create_text_output_mock()

        def mock_get_service(service_id):
            if service_id == "azure_openai":
                return None
            elif service_id == "openai":
                return mock_openai_service
            return None

        mock_kernel.get_service.side_effect = mock_get_service

        # when
        result = await _execute_text_mode(kernel, chat_history)

        # then
        assert result["mode"] == "text"
        assert "output" in result
        assert result["schema_enforced"] == False
        mock_kernel.get_service.assert_any_call("azure_openai")
        mock_kernel.get_service.assert_any_call("openai")

    @pytest.mark.asyncio
    async def test_execute_text_mode_no_service_raises_error(self, mock_kernel):
        """Test _execute_text_mode raises error when no service found."""
        # given
        from llm_ci_runner.llm_execution import _execute_text_mode

        kernel = mock_kernel
        chat_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        # Mock no services available
        mock_kernel.get_service.return_value = None

        # when & then
        with pytest.raises(Exception, match="No chat completion service found"):
            await _execute_text_mode(kernel, chat_history)

    @pytest.mark.asyncio
    async def test_execute_text_mode_empty_result_returns_empty_content(self, mock_kernel):
        """Test _execute_text_mode with empty result returns empty content."""
        # given
        from llm_ci_runner.llm_execution import _execute_text_mode

        kernel = mock_kernel
        chat_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        # Mock azure_openai service with empty result
        mock_azure_service = AsyncMock()
        mock_azure_service.get_chat_message_contents.return_value = []
        mock_kernel.get_service.return_value = mock_azure_service

        # when
        result = await _execute_text_mode(kernel, chat_history)

        # then
        assert result["mode"] == "text"
        assert result["output"] == ""
        assert result["schema_enforced"] == False


class TestClientCreationValidation:
    """Tests for client creation validation."""

    @pytest.mark.asyncio
    async def test_create_azure_client_missing_endpoint_raises_error(self):
        """Test Azure client creation without endpoint."""
        # given
        from llm_ci_runner.llm_execution import _create_azure_client

        with patch.dict("os.environ", {}, clear=True):
            # when & then
            with pytest.raises(ValueError, match="AZURE_OPENAI_ENDPOINT is required for Azure SDK"):
                await _create_azure_client()

    @pytest.mark.asyncio
    async def test_create_openai_client_missing_key_raises_error(self):
        """Test OpenAI client creation without API key."""
        # given
        from llm_ci_runner.llm_execution import _create_openai_client

        with patch.dict("os.environ", {}, clear=True):
            # when & then
            with pytest.raises(ValueError, match="OPENAI_API_KEY is required for OpenAI SDK"):
                await _create_openai_client()


class TestChatHistoryConversion:
    """Tests for chat history conversion edge cases."""

    def test_convert_chat_history_with_object_attributes(self):
        """Test chat history conversion with object attributes."""
        # given
        from llm_ci_runner.llm_execution import _convert_chat_history_to_openai_format

        mock_msg = Mock()
        mock_msg.role = "user"
        mock_msg.content = "Hello"
        chat_history = [mock_msg]

        # when
        result = _convert_chat_history_to_openai_format(chat_history)

        # then
        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert result[0]["content"] == "Hello"

    def test_convert_chat_history_empty_messages_logs_warning(self):
        """Test conversion with empty message list logs warning."""
        # given
        from llm_ci_runner.llm_execution import _convert_chat_history_to_openai_format

        chat_history = []

        # when
        result = _convert_chat_history_to_openai_format(chat_history)

        # then
        assert result == []


class TestSchemaLoadingErrors:
    """Tests for schema loading error handling."""

    @pytest.mark.asyncio
    async def test_execute_llm_task_schema_loading_error_continues(self, mock_kernel):
        """Test schema loading error handling continues execution."""
        # given
        kernel = mock_kernel
        # Create realistic chat history that supports len() and iteration
        chat_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        schema_file = "invalid_schema.json"

        mock_kernel.get_service.return_value.get_chat_message_contents.return_value = create_text_output_mock()

        with patch("llm_ci_runner.llm_execution.load_schema_file") as mock_load_schema:
            mock_load_schema.side_effect = Exception("Schema loading failed")

            # when
            result = await execute_llm_task(kernel, chat_history, schema_file)

            # then
            assert result["mode"] == "text"
            assert "output" in result
            assert result["schema_enforced"] == False


class TestResponseProcessing:
    """Tests for response processing edge cases."""

    def test_process_structured_response_json_error_fallback(self):
        """Test JSON parsing error fallback to text mode."""
        # given
        from llm_ci_runner.llm_execution import _process_structured_response

        mock_schema_model = Mock()
        mock_schema_model.__name__ = "TestSchema"
        mock_schema_dict = {"type": "object"}
        invalid_json_response = "This is not valid JSON"

        # when
        result = _process_structured_response(invalid_json_response, mock_schema_model, mock_schema_dict, "json")

        # then
        assert result["mode"] == "text"
        assert result["output"] == invalid_json_response
        assert result["schema_enforced"] == False

    def test_process_structured_response_no_schema_returns_text(self):
        """Test structured response processing without schema returns text mode."""
        # given
        from llm_ci_runner.llm_execution import _process_structured_response

        response = "Some response"

        # when
        result = _process_structured_response(response, None, None, "text")

        # then
        assert result["mode"] == "text"
        assert result["output"] == response
        assert result["schema_enforced"] == False


class TestSdkExecutionFallback:
    """Tests for SDK execution fallback scenarios."""

    @pytest.mark.asyncio
    async def test_execute_llm_task_azure_sdk_fallback_structured(self, mock_kernel, mock_chat_history):
        """Test Azure SDK fallback with structured output."""
        # given
        kernel = mock_kernel
        chat_history = mock_chat_history
        schema_file = "test_schema.json"

        # Mock Semantic Kernel failure
        mock_kernel.get_service.return_value.get_chat_message_contents.side_effect = Exception("SK failed")

        # Mock schema loading
        with patch("llm_ci_runner.llm_execution.load_schema_file") as mock_load_schema:
            mock_schema_model = Mock()
            mock_schema_model.__name__ = "TestSchema"
            mock_schema_dict = {
                "type": "object",
                "properties": {"test": {"type": "string"}},
            }
            mock_load_schema.return_value = (mock_schema_model, mock_schema_dict)

            # Mock Azure environment and client
            with patch.dict(
                "os.environ",
                {
                    "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com",
                    "AZURE_OPENAI_MODEL": "gpt-4",
                    "AZURE_OPENAI_API_KEY": "test-key",
                },
            ):
                with patch("llm_ci_runner.llm_execution.AsyncAzureOpenAI") as mock_azure_client:
                    # Mock successful Azure SDK response
                    mock_response = Mock()
                    mock_response.choices = [Mock()]
                    mock_response.choices[0].message = Mock()
                    mock_response.choices[0].message.content = '{"test": "value"}'

                    mock_client_instance = AsyncMock()
                    mock_client_instance.beta.chat.completions.parse.return_value = mock_response
                    mock_azure_client.return_value = mock_client_instance

                    # when
                    result = await execute_llm_task(kernel, chat_history, schema_file)

                    # then
                    assert result["mode"] == "structured"
                    assert "output" in result
                    assert result["schema_enforced"] == True

    @pytest.mark.asyncio
    async def test_execute_llm_task_openai_sdk_fallback_structured(self, mock_kernel, mock_chat_history):
        """Test OpenAI SDK fallback with structured output."""
        # given
        kernel = mock_kernel
        chat_history = mock_chat_history
        schema_file = "test_schema.json"

        # Mock Semantic Kernel failure
        mock_kernel.get_service.return_value.get_chat_message_contents.side_effect = Exception("SK failed")

        # Mock schema loading
        with patch("llm_ci_runner.llm_execution.load_schema_file") as mock_load_schema:
            mock_schema_model = Mock()
            mock_schema_model.__name__ = "TestSchema"
            mock_schema_dict = {
                "type": "object",
                "properties": {"test": {"type": "string"}},
            }
            mock_load_schema.return_value = (mock_schema_model, mock_schema_dict)

            # Mock OpenAI environment (no Azure endpoint)
            with patch.dict(
                "os.environ",
                {"OPENAI_API_KEY": "test-openai-key", "OPENAI_CHAT_MODEL_ID": "gpt-4"},
                clear=True,
            ):
                with patch("llm_ci_runner.llm_execution.AsyncOpenAI") as mock_openai_client:
                    # Mock successful OpenAI SDK response
                    mock_response = Mock()
                    mock_response.choices = [Mock()]
                    mock_response.choices[0].message = Mock()
                    mock_response.choices[0].message.content = '{"test": "value"}'

                    mock_client_instance = AsyncMock()
                    mock_client_instance.beta.chat.completions.parse.return_value = mock_response
                    mock_openai_client.return_value = mock_client_instance

                    # when
                    result = await execute_llm_task(kernel, chat_history, schema_file)

                    # then
                    assert result["mode"] == "structured"
                    assert "output" in result
                    assert result["schema_enforced"] == True

    @pytest.mark.asyncio
    async def test_execute_llm_task_azure_sdk_fallback_text_mode(self, mock_kernel, mock_chat_history):
        """Test Azure SDK fallback with text mode (no schema)."""
        # given
        kernel = mock_kernel
        chat_history = mock_chat_history
        schema_file = None

        # Mock Semantic Kernel failure
        mock_kernel.get_service.return_value.get_chat_message_contents.side_effect = Exception("SK failed")

        # Mock Azure environment and client
        with patch.dict(
            "os.environ",
            {
                "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com",
                "AZURE_OPENAI_MODEL": "gpt-4",
                "AZURE_OPENAI_API_KEY": "test-key",
            },
        ):
            with patch("llm_ci_runner.llm_execution.AsyncAzureOpenAI") as mock_azure_client:
                # Mock successful Azure SDK text response
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message = Mock()
                mock_response.choices[0].message.content = "This is a text response"

                mock_client_instance = AsyncMock()
                mock_client_instance.chat.completions.create.return_value = mock_response
                mock_azure_client.return_value = mock_client_instance

                # when
                result = await execute_llm_task(kernel, chat_history, schema_file)

                # then
                assert result["mode"] == "text"
                assert result["output"] == "This is a text response"
                assert result["schema_enforced"] == False

    @pytest.mark.asyncio
    async def test_execute_llm_task_openai_sdk_fallback_text_mode(self, mock_kernel, mock_chat_history):
        """Test OpenAI SDK fallback with text mode (no schema)."""
        # given
        kernel = mock_kernel
        chat_history = mock_chat_history
        schema_file = None

        # Mock Semantic Kernel failure
        mock_kernel.get_service.return_value.get_chat_message_contents.side_effect = Exception("SK failed")

        # Mock OpenAI environment (no Azure)
        with patch.dict(
            "os.environ",
            {"OPENAI_API_KEY": "test-openai-key", "OPENAI_CHAT_MODEL_ID": "gpt-4"},
            clear=True,
        ):
            with patch("llm_ci_runner.llm_execution.AsyncOpenAI") as mock_openai_client:
                # Mock successful OpenAI SDK text response
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message = Mock()
                mock_response.choices[0].message.content = "This is a text response"

                mock_client_instance = AsyncMock()
                mock_client_instance.chat.completions.create.return_value = mock_response
                mock_openai_client.return_value = mock_client_instance

                # when
                result = await execute_llm_task(kernel, chat_history, schema_file)

                # then
                assert result["mode"] == "text"
                assert result["output"] == "This is a text response"
                assert result["schema_enforced"] == False

    @pytest.mark.asyncio
    async def test_execute_llm_task_azure_sdk_missing_model_raises_error(self, mock_kernel, mock_chat_history):
        """Test Azure SDK with missing model raises error."""
        # given
        kernel = mock_kernel
        chat_history = mock_chat_history
        schema_file = None

        # Mock Semantic Kernel failure
        mock_kernel.get_service.return_value.get_chat_message_contents.side_effect = Exception("SK failed")

        # Mock Azure environment without model (but with all other required env vars)
        with patch.dict(
            "os.environ",
            {
                "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com",
                "AZURE_OPENAI_API_KEY": "test-key",
                "OPENAI_API_VERSION": "2024-12-01-preview",
            },
            clear=True,
        ):
            with patch("llm_ci_runner.llm_execution.AsyncAzureOpenAI") as mock_azure_client:
                # when & then
                with pytest.raises(
                    LLMExecutionError,
                    match="AZURE_OPENAI_MODEL is required for Azure SDK",
                ):
                    await execute_llm_task(kernel, chat_history, schema_file)

    @pytest.mark.asyncio
    async def test_execute_llm_task_openai_sdk_missing_model_raises_error(self, mock_kernel, mock_chat_history):
        """Test OpenAI SDK with missing model raises error."""
        # given
        kernel = mock_kernel
        chat_history = mock_chat_history
        schema_file = None

        # Mock Semantic Kernel failure
        mock_kernel.get_service.return_value.get_chat_message_contents.side_effect = Exception("SK failed")

        # Mock OpenAI environment without model
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-openai-key"}, clear=True):
            # when & then
            with pytest.raises(
                LLMExecutionError,
                match="OPENAI_CHAT_MODEL_ID is required for OpenAI SDK",
            ):
                await execute_llm_task(kernel, chat_history, schema_file)
