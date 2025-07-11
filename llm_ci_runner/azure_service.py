"""
Azure service setup and authentication for LLM CI Runner.

This module provides functionality for setting up Azure OpenAI services
with proper authentication using both API keys and RBAC.
"""

import logging
import os

from azure.core.exceptions import ClientAuthenticationError
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import (
    AzureChatCompletion,
)
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from .exceptions import AuthenticationError

LOGGER = logging.getLogger(__name__)


async def setup_azure_service() -> tuple[AzureChatCompletion, DefaultAzureCredential | None]:
    """
    Setup Azure OpenAI service with authentication.

    Supports both API key and RBAC authentication methods.
    Uses retry logic for transient authentication failures.

    Returns:
        Tuple of (AzureChatCompletion service, credential object)

    Raises:
        AuthenticationError: If authentication setup fails
    """
    LOGGER.debug("🔐 Setting up Azure OpenAI service")

    # Get required environment variables
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    model = os.getenv("AZURE_OPENAI_MODEL")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

    if not endpoint:
        raise AuthenticationError("AZURE_OPENAI_ENDPOINT environment variable is required")
    if not model:
        raise AuthenticationError("AZURE_OPENAI_MODEL environment variable is required")

    LOGGER.info(f"🎯 Using Azure OpenAI endpoint: {endpoint}")
    LOGGER.info(f"🎯 Using model: {model}")
    LOGGER.info(f"🎯 Using API version: {api_version}")

    # Check for API key authentication
    api_key = os.getenv("AZURE_OPENAI_API_KEY")

    if api_key:
        LOGGER.info("🔑 Using API key authentication")
        try:
            service = AzureChatCompletion(
                service_id="azure_openai",
                endpoint=endpoint,
                api_key=api_key,
                deployment_name=model,
                api_version=api_version,
            )
            return service, None
        except ClientAuthenticationError as e:
            raise AuthenticationError(f"Azure authentication failed: {e}") from e
        except Exception as e:
            raise AuthenticationError(f"Error setting up Azure service: {e}") from e
    else:
        LOGGER.info("🔐 Using RBAC authentication with DefaultAzureCredential")

        @retry(
            retry=retry_if_exception_type(
                (
                    # Network-related exceptions that should be retried
                    ConnectionError,
                    TimeoutError,
                    # Generic exceptions that might be transient
                    RuntimeError,
                )
            ),
            stop=stop_after_attempt(3),
            wait=wait_exponential_jitter(initial=1, max=10, jitter=2),
            before_sleep=before_sleep_log(LOGGER, logging.WARNING),
            reraise=True,
        )
        async def token_provider(scopes: list[str] | None = None) -> str:
            """Get access token with retry logic for transient failures."""
            try:
                credential = DefaultAzureCredential()
                token = await credential.get_token("https://cognitiveservices.azure.com/.default")
                return token.token
            except Exception as e:
                LOGGER.error(f"❌ Authentication failed: {e}")
                raise AuthenticationError(f"Failed to authenticate with Azure: {e}") from e

        try:
            service = AzureChatCompletion(
                service_id="azure_openai",
                endpoint=endpoint,
                deployment_name=model,
                api_version=api_version,
                ad_token_provider=token_provider,
            )

            # Test authentication by getting a token
            credential = DefaultAzureCredential()
            await credential.get_token("https://cognitiveservices.azure.com/.default")

            LOGGER.info("✅ Azure service setup completed successfully")
            return service, credential

        except ClientAuthenticationError as e:
            raise AuthenticationError(f"Azure authentication failed. Please check your credentials: {e}") from e
        except Exception as e:
            raise AuthenticationError(f"Failed to setup Azure service: {e}") from e
