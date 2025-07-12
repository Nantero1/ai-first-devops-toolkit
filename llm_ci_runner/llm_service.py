"""
LLM service setup and authentication for LLM CI Runner.

Supports both Azure OpenAI (API key or RBAC) and OpenAI (API key required).
"""

import logging
import os

from azure.core.exceptions import ClientAuthenticationError
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
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

# --- Azure logic (unchanged, API key optional, RBAC fallback) ---


async def get_azure_token_with_credential(
    credential: DefaultAzureCredential | None = None,
) -> str:
    """
    Get Azure access token using DefaultAzureCredential.

    Args:
        credential: Optional credential instance to use. If None, creates a new one.

    Returns:
        Access token string

    Raises:
        AuthenticationError: If authentication fails
    """
    try:
        if credential is None:
            credential = DefaultAzureCredential()

        token = await credential.get_token("https://cognitiveservices.azure.com/.default")
        return token.token
    except Exception as e:
        LOGGER.error(f"❌ Authentication failed: {e}")
        raise AuthenticationError(f"Failed to authenticate with Azure: {e}") from e


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
async def azure_token_provider(scopes: list[str] | None = None) -> str:
    """
    Token provider for Azure OpenAI with retry logic.

    This function matches the signature expected by AzureChatCompletion.ad_token_provider
    and includes retry logic for transient failures.

    Args:
        scopes: Token scopes (ignored, we always use cognitiveservices scope)

    Returns:
        Access token string

    Raises:
        AuthenticationError: If authentication fails
    """
    return await get_azure_token_with_credential()


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

        try:
            service = AzureChatCompletion(
                service_id="azure_openai",
                endpoint=endpoint,
                deployment_name=model,
                api_version=api_version,
                ad_token_provider=azure_token_provider,
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


# --- OpenAI logic (API key required) ---


def has_azure_vars() -> bool:
    """Check if required Azure OpenAI env vars are present (API key optional)."""
    return bool(os.getenv("AZURE_OPENAI_ENDPOINT") and os.getenv("AZURE_OPENAI_MODEL"))


def has_openai_vars() -> bool:
    """Check if required OpenAI env vars are present."""
    return bool(os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_CHAT_MODEL_ID"))


async def setup_openai_service() -> tuple[OpenAIChatCompletion, None]:
    """Setup OpenAI service with API key authentication."""
    api_key = os.getenv("OPENAI_API_KEY")
    model_id = os.getenv("OPENAI_CHAT_MODEL_ID")
    org_id = os.getenv("OPENAI_ORG_ID")
    base_url = os.getenv("OPENAI_BASE_URL")
    if not api_key:
        raise AuthenticationError("OPENAI_API_KEY environment variable is required")
    if not model_id:
        raise AuthenticationError("OPENAI_CHAT_MODEL_ID environment variable is required")
    LOGGER.info(f"🎯 Using OpenAI model: {model_id}")
    if org_id:
        LOGGER.info(f"🎯 Using OpenAI organization: {org_id}")
    if base_url:
        LOGGER.info(f"🎯 Using OpenAI base URL: {base_url}")
    try:
        service = OpenAIChatCompletion(
            ai_model_id=model_id,
            api_key=api_key,
            service_id="openai",
            org_id=org_id,
        )
        LOGGER.info("✅ OpenAI service setup completed successfully")
        return service, None
    except Exception as e:
        raise AuthenticationError(f"Failed to setup OpenAI service: {e}") from e


# --- Unified LLM service setup ---


async def setup_llm_service() -> tuple[AzureChatCompletion | OpenAIChatCompletion, DefaultAzureCredential | None]:
    """
    Setup LLM service with Azure-first priority, OpenAI fallback.
    Azure: endpoint/model required, API key optional (RBAC fallback).
    OpenAI: API key and model required.
    """
    if has_azure_vars():
        return await setup_azure_service()
    elif has_openai_vars():
        return await setup_openai_service()
    else:
        raise AuthenticationError(
            "No valid LLM service configuration found. Please set either:\n"
            "Azure: AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_MODEL\n"
            "OpenAI: OPENAI_API_KEY + OPENAI_CHAT_MODEL_ID"
        )
