"""
Unit tests for Azure service authentication functions.

Tests get_azure_token_with_credential and azure_token_provider functions
with heavy mocking following the Given-When-Then pattern.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from llm_ci_runner import (
    AuthenticationError,
    azure_token_provider,
    get_azure_token_with_credential,
    setup_azure_service,
    setup_llm_service,
    setup_openai_service,
)


class TestGetAzureTokenWithCredential:
    """Tests for get_azure_token_with_credential function."""

    @pytest.mark.asyncio
    async def test_get_azure_token_with_provided_credential(self):
        """Test getting token with provided credential."""
        # given
        mock_credential = AsyncMock()
        mock_token = Mock()
        mock_token.token = "test-token-123"
        mock_credential.get_token = AsyncMock(return_value=mock_token)

        # when
        result = await get_azure_token_with_credential(mock_credential)

        # then
        assert result == "test-token-123"
        mock_credential.get_token.assert_called_once_with("https://cognitiveservices.azure.com/.default")

    @pytest.mark.asyncio
    async def test_get_azure_token_with_default_credential(self):
        """Test getting token with default credential (None provided)."""
        # given
        mock_token = Mock()
        mock_token.token = "default-token-456"

        with patch("llm_ci_runner.llm_service.DefaultAzureCredential") as mock_credential_class:
            mock_credential = AsyncMock()
            mock_credential.get_token = AsyncMock(return_value=mock_token)
            mock_credential_class.return_value = mock_credential

            # when
            result = await get_azure_token_with_credential(None)

            # then
            assert result == "default-token-456"
            mock_credential_class.assert_called_once()
            mock_credential.get_token.assert_called_once_with("https://cognitiveservices.azure.com/.default")

    @pytest.mark.asyncio
    async def test_get_azure_token_with_no_credential_parameter(self):
        """Test getting token without passing credential parameter."""
        # given
        mock_token = Mock()
        mock_token.token = "no-param-token-789"

        with patch("llm_ci_runner.llm_service.DefaultAzureCredential") as mock_credential_class:
            mock_credential = AsyncMock()
            mock_credential.get_token = AsyncMock(return_value=mock_token)
            mock_credential_class.return_value = mock_credential

            # when
            result = await get_azure_token_with_credential()

            # then
            assert result == "no-param-token-789"
            mock_credential_class.assert_called_once()
            mock_credential.get_token.assert_called_once_with("https://cognitiveservices.azure.com/.default")

    @pytest.mark.asyncio
    async def test_get_azure_token_with_credential_exception_raises_auth_error(self):
        """Test that credential exceptions are wrapped in AuthenticationError."""
        # given
        mock_credential = AsyncMock()
        mock_credential.get_token = AsyncMock(side_effect=Exception("Credential error"))

        # when & then
        with pytest.raises(
            AuthenticationError,
            match="Failed to authenticate with Azure: Credential error",
        ):
            await get_azure_token_with_credential(mock_credential)

    @pytest.mark.asyncio
    async def test_get_azure_token_with_default_credential_creation_failure(self):
        """Test that DefaultAzureCredential creation failures are wrapped in AuthenticationError."""
        # given
        with patch("llm_ci_runner.llm_service.DefaultAzureCredential") as mock_credential_class:
            mock_credential_class.side_effect = Exception("Credential creation failed")

            # when & then
            with pytest.raises(
                AuthenticationError,
                match="Failed to authenticate with Azure: Credential creation failed",
            ):
                await get_azure_token_with_credential()

    @pytest.mark.asyncio
    async def test_get_azure_token_logs_error_on_failure(self):
        """Test that authentication errors are logged properly."""
        # given
        mock_credential = AsyncMock()
        mock_credential.get_token = AsyncMock(side_effect=Exception("Token error"))

        # when
        with patch("llm_ci_runner.llm_service.LOGGER") as mock_logger:
            with pytest.raises(AuthenticationError):
                await get_azure_token_with_credential(mock_credential)

            # then
            mock_logger.error.assert_called_once()
            # Check that the error message was logged
            logged_message = mock_logger.error.call_args[0][0]
            assert "❌ Authentication failed" in logged_message
            assert "Token error" in logged_message


class TestAzureTokenProvider:
    """Tests for azure_token_provider function."""

    @pytest.mark.asyncio
    async def test_azure_token_provider_with_scopes_parameter(self):
        """Test azure_token_provider with scopes parameter (should be ignored)."""
        # given
        with patch("llm_ci_runner.llm_service.get_azure_token_with_credential") as mock_get_token:
            mock_get_token.return_value = "scoped-token-123"

            # when
            result = await azure_token_provider(scopes=["scope1", "scope2"])

            # then
            assert result == "scoped-token-123"
            mock_get_token.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_azure_token_provider_with_none_scopes(self):
        """Test azure_token_provider with None scopes parameter."""
        # given
        with patch("llm_ci_runner.llm_service.get_azure_token_with_credential") as mock_get_token:
            mock_get_token.return_value = "none-scopes-token-456"

            # when
            result = await azure_token_provider(scopes=None)

            # then
            assert result == "none-scopes-token-456"
            mock_get_token.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_azure_token_provider_without_scopes_parameter(self):
        """Test azure_token_provider without scopes parameter."""
        # given
        with patch("llm_ci_runner.llm_service.get_azure_token_with_credential") as mock_get_token:
            mock_get_token.return_value = "default-provider-token-789"

            # when
            result = await azure_token_provider()

            # then
            assert result == "default-provider-token-789"
            mock_get_token.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_azure_token_provider_propagates_auth_error(self):
        """Test that azure_token_provider propagates AuthenticationError from underlying function."""
        # given
        with patch("llm_ci_runner.llm_service.get_azure_token_with_credential") as mock_get_token:
            mock_get_token.side_effect = AuthenticationError("Underlying auth error")

            # when & then
            with pytest.raises(AuthenticationError, match="Underlying auth error"):
                await azure_token_provider()

    @pytest.mark.asyncio
    async def test_azure_token_provider_has_retry_decorator(self):
        """Test that azure_token_provider has retry logic applied."""
        # given
        # This test verifies that the retry decorator is working by checking
        # that the function has retry attributes

        # when
        # Check if the function has retry-related attributes
        function_attrs = dir(azure_token_provider)

        # then
        # The retry decorator adds certain attributes to the function
        assert hasattr(azure_token_provider, "__wrapped__")
        # The retry decorator from tenacity typically adds a retry attribute
        assert any("retry" in attr.lower() for attr in function_attrs)


class TestSetupAzureService:
    """Tests for setup_azure_service (Azure) and setup_llm_service (Azure/OpenAI) functions."""

    @pytest.mark.asyncio
    async def test_setup_azure_service_rbac_client_auth_error(self):
        """Test that RBAC ClientAuthenticationError is handled properly."""
        # given
        from azure.core.exceptions import ClientAuthenticationError

        with patch.dict(
            "os.environ",
            {
                "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
                "AZURE_OPENAI_MODEL": "gpt-4-test",
                "AZURE_OPENAI_API_VERSION": "2024-12-01-preview",
            },
            clear=True,
        ):
            with patch("llm_ci_runner.llm_service.AzureChatCompletion") as mock_chat_completion:
                with patch("llm_ci_runner.llm_service.DefaultAzureCredential") as mock_credential_class:
                    # Setup DefaultAzureCredential to raise ClientAuthenticationError
                    mock_credential = AsyncMock()
                    mock_credential.get_token = AsyncMock(side_effect=ClientAuthenticationError("RBAC auth failed"))
                    mock_credential_class.return_value = mock_credential

                    # when & then
                    with pytest.raises(
                        AuthenticationError,
                        match="Azure authentication failed. Please check your credentials",
                    ):
                        await setup_azure_service()

    @pytest.mark.asyncio
    async def test_setup_azure_service_rbac_generic_error(self):
        """Test that RBAC generic errors are handled properly."""
        # given
        with patch.dict(
            "os.environ",
            {
                "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
                "AZURE_OPENAI_MODEL": "gpt-4-test",
                "AZURE_OPENAI_API_VERSION": "2024-12-01-preview",
            },
            clear=True,
        ):
            with patch("llm_ci_runner.llm_service.AzureChatCompletion") as mock_chat_completion:
                with patch("llm_ci_runner.llm_service.DefaultAzureCredential") as mock_credential_class:
                    # Setup DefaultAzureCredential to raise generic error
                    mock_credential = AsyncMock()
                    mock_credential.get_token = AsyncMock(side_effect=Exception("Generic RBAC error"))
                    mock_credential_class.return_value = mock_credential

                    # when & then
                    with pytest.raises(AuthenticationError, match="Failed to setup Azure service"):
                        await setup_azure_service()


class TestSetupOpenAIService:
    """Tests for setup_openai_service and OpenAI fallback logic."""

    @pytest.mark.asyncio
    async def test_setup_openai_service_success(self):
        """Test successful OpenAI service setup with required env vars."""
        # given
        with patch.dict(
            "os.environ",
            {"OPENAI_API_KEY": "non-an-api-key", "OPENAI_CHAT_MODEL_ID": "gpt-4-test"},
            clear=True,
        ):
            with patch("llm_ci_runner.llm_service.OpenAIChatCompletion") as mock_openai:
                mock_service = AsyncMock()
                mock_openai.return_value = mock_service

                # when
                service, credential = await setup_openai_service()

                # then
                assert service is mock_service
                assert credential is None
                mock_openai.assert_called_once_with(
                    ai_model_id="gpt-4-test",
                    api_key="non-an-api-key",
                    service_id="openai",
                    org_id=None,
                )

    @pytest.mark.asyncio
    async def test_setup_llm_service_openai_fallback(self):
        """Test OpenAI fallback when Azure vars are missing."""
        # given
        with patch.dict(
            "os.environ",
            {"OPENAI_API_KEY": "non-an-api-key", "OPENAI_CHAT_MODEL_ID": "gpt-4-test"},
            clear=True,
        ):
            with patch("llm_ci_runner.llm_service.OpenAIChatCompletion") as mock_openai:
                mock_service = AsyncMock()
                mock_openai.return_value = mock_service

                # when
                service, credential = await setup_llm_service()

                # then
                assert service is mock_service
                assert credential is None

    @pytest.mark.asyncio
    async def test_setup_llm_service_azure_priority(self):
        """Test Azure takes priority when both configs are present."""
        # given
        with patch.dict(
            "os.environ",
            {
                "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
                "AZURE_OPENAI_MODEL": "gpt-4-test",
                "OPENAI_API_KEY": "non-an-api-key",
                "OPENAI_CHAT_MODEL_ID": "gpt-4-test",
            },
            clear=True,
        ):
            with patch("llm_ci_runner.llm_service.AzureChatCompletion") as mock_azure:
                mock_service = AsyncMock()
                mock_azure.return_value = mock_service
                with patch("llm_ci_runner.llm_service.DefaultAzureCredential") as mock_cred:
                    mock_cred.return_value = AsyncMock()
                    # when
                    service, credential = await setup_llm_service()
                    # then
                    assert service is mock_service

    @pytest.mark.asyncio
    async def test_setup_llm_service_no_config(self):
        """Test error when neither Azure nor OpenAI config is present."""
        # given
        with patch.dict("os.environ", {}, clear=True):
            # when/then
            with pytest.raises(AuthenticationError, match="No valid LLM service configuration found"):
                await setup_llm_service()

    @pytest.mark.asyncio
    async def test_setup_openai_service_missing_env_vars(self):
        """Test error when OpenAI env vars are incomplete."""
        # given
        with patch.dict("os.environ", {"OPENAI_API_KEY": "non-an-api-key"}, clear=True):
            # when/then
            with pytest.raises(
                AuthenticationError,
                match="OPENAI_CHAT_MODEL_ID environment variable is required",
            ):
                await setup_openai_service()
