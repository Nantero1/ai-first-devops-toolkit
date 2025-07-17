"""
Unit tests for Azure service authentication functions.

Tests get_azure_token_with_credential and azure_token_provider functions
with heavy mocking following the Given-When-Then pattern.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from llm_ci_runner import (
    AuthenticationError,
    setup_azure_service,
    setup_llm_service,
    setup_openai_service,
)


def test_setup_azure_service_uses_ad_token_provider(monkeypatch):
    """Test that setup_azure_service uses ad_token_provider when no API key is set."""
    from llm_ci_runner import llm_service

    # Patch environment to remove API key
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://test.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_MODEL", "gpt-4-test")
    monkeypatch.setenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

    # Patch DefaultAzureCredential and get_bearer_token_provider
    with (
        patch("llm_ci_runner.llm_service.DefaultAzureCredential") as mock_cred_class,
        patch("llm_ci_runner.llm_service.get_bearer_token_provider") as mock_token_provider,
    ):
        mock_cred = Mock()
        mock_cred.get_token = AsyncMock()
        mock_cred_class.return_value = mock_cred
        mock_token_provider.return_value = "token-provider-mock"

        # Patch AzureChatCompletion to check for ad_token_provider
        with patch("llm_ci_runner.llm_service.AzureChatCompletion") as mock_azure_chat:
            mock_service = Mock()
            mock_azure_chat.return_value = mock_service

            # Run setup_azure_service
            import asyncio

            service, credential = asyncio.get_event_loop().run_until_complete(llm_service.setup_azure_service())

            # Assert the correct provider was used
            mock_token_provider.assert_called_once()
            mock_azure_chat.assert_called_once()
            kwargs = mock_azure_chat.call_args.kwargs
            assert "ad_token_provider" in kwargs
            assert kwargs["ad_token_provider"] == "token-provider-mock"
            assert service == mock_service
            assert credential == mock_cred


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

    @pytest.mark.asyncio
    async def test_setup_openai_service_missing_api_key(self):
        """Test setup_openai_service with missing API key."""
        # given
        with patch.dict("os.environ", {"OPENAI_CHAT_MODEL_ID": "gpt-4"}, clear=True):
            # when & then
            with pytest.raises(
                AuthenticationError,
                match="OPENAI_API_KEY environment variable is required",
            ):
                await setup_openai_service()

    @pytest.mark.asyncio
    async def test_setup_openai_service_with_org_id(self):
        """Test setup_openai_service with organization ID."""
        # given
        with patch.dict(
            "os.environ",
            {
                "OPENAI_API_KEY": "test-key",
                "OPENAI_CHAT_MODEL_ID": "gpt-4",
                "OPENAI_ORG_ID": "org-test",
            },
            clear=True,
        ):
            with patch("llm_ci_runner.llm_service.OpenAIChatCompletion") as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service

                # when
                result = await setup_openai_service()

                # then
                assert result[0] == mock_service
                assert result[1] is None
                mock_service_class.assert_called_once_with(
                    ai_model_id="gpt-4",
                    api_key="test-key",
                    service_id="openai",
                    org_id="org-test",
                )

    @pytest.mark.asyncio
    async def test_setup_openai_service_with_base_url(self):
        """Test setup_openai_service with base URL."""
        # given
        with patch.dict(
            "os.environ",
            {
                "OPENAI_API_KEY": "test-key",
                "OPENAI_CHAT_MODEL_ID": "gpt-4",
                "OPENAI_BASE_URL": "https://custom.openai.com",
            },
            clear=True,
        ):
            with patch("llm_ci_runner.llm_service.OpenAIChatCompletion") as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service

                # when
                result = await setup_openai_service()

                # then
                assert result[0] == mock_service
                assert result[1] is None
                mock_service_class.assert_called_once_with(
                    ai_model_id="gpt-4",
                    api_key="test-key",
                    service_id="openai",
                    org_id=None,
                )

    @pytest.mark.asyncio
    async def test_setup_openai_service_exception_raises_auth_error(self):
        """Test that setup_openai_service exceptions are wrapped in AuthenticationError."""
        # given
        with patch.dict(
            "os.environ",
            {"OPENAI_API_KEY": "test-key", "OPENAI_CHAT_MODEL_ID": "gpt-4"},
            clear=True,
        ):
            with patch("llm_ci_runner.llm_service.OpenAIChatCompletion") as mock_service_class:
                mock_service_class.side_effect = Exception("Service creation failed")

                # when & then
                with pytest.raises(AuthenticationError, match="Failed to setup OpenAI service"):
                    await setup_openai_service()
