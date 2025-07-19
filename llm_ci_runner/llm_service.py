"""
LLM service setup and authentication for LLM CI Runner.

Supports both Azure OpenAI (API key or RBAC) and OpenAI (API key required).
"""

import logging
import os

from azure.core.exceptions import ClientAuthenticationError
from azure.identity.aio import (
    DefaultAzureCredential,
    get_bearer_token_provider,  # NEW: Import for token provider
)
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import (
    AzureChatCompletion,
)

from .exceptions import AuthenticationError
from .retry import retry_network_operation

LOGGER = logging.getLogger(__name__)

# --- Azure logic (unchanged, API key optional, RBAC fallback) ---


@retry_network_operation
async def setup_azure_service() -> tuple[AzureChatCompletion, DefaultAzureCredential | None]:
    """
    Setup Azure OpenAI service with authentication, retry, and timeout protection.

    Supports both API key and RBAC authentication methods.
    Uses integrated retry + timeout logic for transient authentication failures.

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

    LOGGER.debug(f"🎯 Using Azure OpenAI endpoint: {endpoint}")
    LOGGER.info(f"🎯 Using model: {model}")
    LOGGER.debug(f"🎯 Using API version: {api_version}")

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
            credential = DefaultAzureCredential()
            token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")
            service = AzureChatCompletion(
                service_id="azure_openai",
                endpoint=endpoint,
                deployment_name=model,
                api_version=api_version,
                ad_token_provider=token_provider,  # NEW: Use the token provider
            )

            # Test authentication by getting a token
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
    """Setup OpenAI service with API key authentication and retry."""
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
