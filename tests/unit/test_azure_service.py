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

        with patch("llm_ci_runner.azure_service.DefaultAzureCredential") as mock_credential_class:
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

        with patch("llm_ci_runner.azure_service.DefaultAzureCredential") as mock_credential_class:
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
        with patch("llm_ci_runner.azure_service.DefaultAzureCredential") as mock_credential_class:
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
        with patch("llm_ci_runner.azure_service.LOGGER") as mock_logger:
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
        with patch("llm_ci_runner.azure_service.get_azure_token_with_credential") as mock_get_token:
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
        with patch("llm_ci_runner.azure_service.get_azure_token_with_credential") as mock_get_token:
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
        with patch("llm_ci_runner.azure_service.get_azure_token_with_credential") as mock_get_token:
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
        with patch("llm_ci_runner.azure_service.get_azure_token_with_credential") as mock_get_token:
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


class TestSetupAzureServiceErrorPaths:
    """Tests for error paths in setup_azure_service function."""

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
            with patch("llm_ci_runner.azure_service.AzureChatCompletion") as mock_chat_completion:
                with patch("llm_ci_runner.azure_service.DefaultAzureCredential") as mock_credential_class:
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
            with patch("llm_ci_runner.azure_service.AzureChatCompletion") as mock_chat_completion:
                with patch("llm_ci_runner.azure_service.DefaultAzureCredential") as mock_credential_class:
                    # Setup DefaultAzureCredential to raise generic error
                    mock_credential = AsyncMock()
                    mock_credential.get_token = AsyncMock(side_effect=Exception("Generic RBAC error"))
                    mock_credential_class.return_value = mock_credential

                    # when & then
                    with pytest.raises(AuthenticationError, match="Failed to setup Azure service"):
                        await setup_azure_service()
