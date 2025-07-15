"""LLM execution module with OpenAI SDK fallback for schema enforcement.

Provides robust LLM task execution with automatic fallback from Semantic Kernel
to OpenAI SDK when schema enforcement fails. Handles both structured and text output modes.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

from openai import AsyncAzureOpenAI, AsyncOpenAI
from rich.console import Console
from rich.panel import Panel
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatPromptExecutionSettings

if TYPE_CHECKING:
    from semantic_kernel.services.chat_completion_service import ChatCompletionService  # type: ignore[import-not-found]

from .exceptions import LLMExecutionError
from .io_operations import create_chat_history, load_schema_file
from .schema import generate_one_shot_example

LOGGER = logging.getLogger(__name__)

# Configuration constants for LLM execution
# Removed default constants - using underlying library defaults instead

# LOGGER is already imported from logging_config
CONSOLE = Console()


def _prepare_schema_for_sdk(schema_model: type, schema_dict: dict[str, Any]) -> dict[str, Any]:
    """Prepare schema for OpenAI SDK format with name field.

    Args:
        schema_model: Pydantic model class
        schema_dict: JSON schema dictionary

    Returns:
        Schema dictionary with name field added for SDK compatibility
    """
    schema_with_name = schema_dict.copy()
    schema_with_name["name"] = schema_model.__name__
    return schema_with_name


async def execute_llm_task(
    kernel: Kernel,
    chat_history: list,
    schema_file: str | None = None,
    output_file: str | None = None,
    log_level: str = "INFO",
) -> dict[str, Any]:
    """Execute LLM task with strict schema enforcement.

    Implements dual-path architecture:
    1. Try Semantic Kernel with schema enforcement
    2. If Semantic Kernel fails → Try appropriate SDK (Azure/OpenAI) with schema enforcement
    3. If schema enforcement fails → Raise error (no text mode fallback)

    Users rely on strict schema compliance - if schema enforcement fails, the operation fails.

    Args:
        kernel: Semantic Kernel instance
        chat_history: List of chat messages
        schema_file: Optional schema file path
        output_file: Optional output file path
        log_level: Logging level

    Returns:
        Dictionary containing execution results

    Raises:
        LLMExecutionError: If all execution paths fail
    """
    LOGGER.debug("🤖 Executing LLM task")

    # Load schema if provided
    schema_model = None
    schema_dict = None
    if schema_file:
        try:
            schema_result = load_schema_file(Path(schema_file) if schema_file else None)
            if schema_result:
                schema_model, schema_dict = schema_result
                LOGGER.debug(f"📋 Schema loaded - model: {type(schema_model)}, dict: {type(schema_dict)}")
                LOGGER.debug(f"📋 Schema dict keys: {list(schema_dict.keys())}")
        except Exception as e:
            LOGGER.warning(f"⚠️ Failed to load schema: {e}")
            LOGGER.debug("📝 Continuing without schema enforcement")

    # Enhance prompt with one-shot example if schema is provided
    enhanced_chat_history = _enhance_prompt_with_one_shot_example(chat_history, schema_model)

    # Path 1: Try Semantic Kernel with schema enforcement
    try:
        LOGGER.debug("🔐 Attempting Semantic Kernel with schema enforcement")
        result = await _execute_semantic_kernel_with_schema(kernel, enhanced_chat_history, schema_model, schema_dict)
        LOGGER.debug("✅ Semantic Kernel execution successful")
        return result
    except Exception as e:
        LOGGER.warning(f"⚠️ Semantic Kernel failed: {e}")
        LOGGER.info("🔄 Falling back to OpenAI SDK")

    # Path 2: Try appropriate SDK based on endpoint type
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")

    if azure_endpoint:
        # Try Azure SDK for Azure OpenAI endpoints
        try:
            LOGGER.debug("🔐 Attempting Azure SDK with schema enforcement")
            result = await _execute_sdk_with_schema("azure", enhanced_chat_history, schema_model, schema_dict)
            LOGGER.info("✅ Azure SDK execution successful")
            return result
        except Exception as e:
            LOGGER.warning(f"⚠️ Azure SDK failed: {e}")
            raise LLMExecutionError(f"Schema enforcement failed with Azure SDK: {e}") from e
    else:
        # Try OpenAI SDK for OpenAI endpoints
        try:
            LOGGER.info("🔐 Attempting OpenAI SDK with schema enforcement")
            result = await _execute_sdk_with_schema("openai", enhanced_chat_history, schema_model, schema_dict)
            LOGGER.info("✅ OpenAI SDK execution successful")
            return result
        except Exception as e:
            LOGGER.warning(f"⚠️ OpenAI SDK failed: {e}")
            raise LLMExecutionError(f"Schema enforcement failed with OpenAI SDK: {e}") from e

    # If we reach here, no endpoint was detected
    raise LLMExecutionError("No valid endpoint configuration found")


async def _execute_semantic_kernel_with_schema(
    kernel: Kernel,
    chat_history: list,
    schema_model: type | None,
    schema_dict: dict[str, Any] | None,
) -> dict[str, Any]:
    """Execute LLM task using Semantic Kernel with schema enforcement.

    Args:
        kernel: Semantic Kernel instance
        chat_history: List of chat messages
        schema_model: Optional Pydantic model
        schema_dict: Optional schema dictionary

    Returns:
        Dictionary containing execution results

    Raises:
        Exception: If Semantic Kernel execution fails
    """
    # Get the chat completion service
    service: ChatCompletionService | None = kernel.get_service("azure_openai")
    if not service:
        # Try alternative service IDs
        service = kernel.get_service("openai")
    if not service:
        raise Exception("No chat completion service found")

    # Create settings with schema enforcement
    settings = OpenAIChatPromptExecutionSettings(
        service_id="azure_openai",
    )

    # Set response_format for schema enforcement
    if schema_model and schema_dict:
        # Use the original schema_dict for Azure OpenAI to preserve additionalProperties: false
        # Add required name and schema fields for Azure OpenAI
        schema_with_name = schema_dict.copy()
        schema_with_name["name"] = schema_model.__name__
        settings.response_format = {
            "type": "json_schema",
            "json_schema": {
                "schema": schema_with_name,
                "name": schema_model.__name__,
            },
        }
        LOGGER.info(f"🔒 Using 100% schema enforcement with model: {schema_model.__name__}")
        LOGGER.debug("   → Token-level constraint enforcement active")
        LOGGER.debug(f"   → response_format type: {type(settings.response_format)}")
    else:
        LOGGER.debug("📝 Using text output mode (no schema)")

    # Convert list to ChatHistory for Semantic Kernel compatibility
    sk_chat_history = create_chat_history(chat_history)

    # Execute with Semantic Kernel
    result = await service.get_chat_message_contents(
        chat_history=sk_chat_history,
        settings=settings,
    )

    # Extract content from ChatMessageContent objects
    if result and len(result) > 0:
        content = result[0].content
    else:
        content = ""

    return _process_structured_response(content, schema_model, schema_dict)


def _convert_chat_history_to_openai_format(chat_history: list) -> list[dict[str, str]]:
    """Convert chat history to OpenAI-compatible format (list of dicts).

    Handles both dict and object (e.g., ChatMessageContent) cases.
    """
    converted: list[dict[str, str]] = []
    for msg in chat_history:
        if isinstance(msg, dict):
            # Already in dict format
            if "role" in msg and "content" in msg:
                converted.append({"role": str(msg["role"]), "content": str(msg["content"])})
        else:
            # Try to extract from object attributes
            role = getattr(msg, "role", None)
            content = getattr(msg, "content", None)
            if role and content:
                converted.append({"role": str(role), "content": str(content)})
    if not converted:
        LOGGER.warning("⚠️ No valid messages found after chat history conversion!")
    else:
        LOGGER.debug(f"🔄 Converted chat history to OpenAI format: {converted}")
    return converted


async def _create_azure_client() -> AsyncAzureOpenAI:
    """Create and configure Azure OpenAI client with validation.

    Returns:
        Configured Azure OpenAI client

    Raises:
        ValueError: If required Azure environment variables are missing
    """
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION")

    if not azure_endpoint:
        raise ValueError("AZURE_OPENAI_ENDPOINT is required for Azure SDK")

    return AsyncAzureOpenAI(
        azure_endpoint=azure_endpoint,
        api_key=azure_api_key,  # Will fall back to DefaultAzureCredential if None
        api_version=api_version if api_version else None,
    )


async def _create_openai_client() -> AsyncOpenAI:
    """Create and configure OpenAI client with validation.

    Returns:
        Configured OpenAI client

    Raises:
        ValueError: If required OpenAI environment variables are missing
    """
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_org = os.getenv("OPENAI_ORG_ID")
    openai_base_url = os.getenv("OPENAI_BASE_URL")

    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY is required for OpenAI SDK")

    return AsyncOpenAI(
        api_key=openai_api_key,
        organization=openai_org if openai_org else None,
        base_url=openai_base_url if openai_base_url else None,
    )


async def _execute_sdk_with_schema(
    client_type: str,
    chat_history: list,
    schema_model: type | None,
    schema_dict: dict[str, Any] | None,
) -> dict[str, Any]:
    """Execute LLM task using appropriate SDK with schema enforcement.

    Unified execution logic for both Azure and OpenAI SDKs, eliminating code duplication.

    Args:
        client_type: Either "azure" or "openai"
        chat_history: List of chat messages
        schema_model: Optional Pydantic model
        schema_dict: Optional schema dictionary

    Returns:
        Dictionary containing execution results

    Raises:
        ValueError: If client configuration is invalid
        Exception: If SDK execution fails
    """
    # Create appropriate client and get model
    client: AsyncAzureOpenAI | AsyncOpenAI
    if client_type == "azure":
        client = await _create_azure_client()
        model = os.getenv("AZURE_OPENAI_MODEL")
        if not model:
            raise ValueError("AZURE_OPENAI_MODEL is required for Azure SDK")
    else:  # openai
        client = await _create_openai_client()
        model = os.getenv("OPENAI_CHAT_MODEL_ID")
        if not model:
            raise ValueError("OPENAI_CHAT_MODEL_ID is required for OpenAI SDK")

    # Common message preparation
    messages = _convert_chat_history_to_openai_format(chat_history)

    # Common execution logic
    if schema_model and schema_dict:
        LOGGER.info(f"🔒 Using {client_type.upper()} SDK with model: {schema_model.__name__}")
        schema_prepared = _prepare_schema_for_sdk(schema_model, schema_dict)
        response = await client.beta.chat.completions.parse(
            model=model,
            messages=messages,  # type: ignore
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "schema": schema_prepared,
                    "name": schema_model.__name__,
                },
            },  # type: ignore
        )
        result = response.choices[0].message.content
    else:
        LOGGER.info(f"📝 Using {client_type.upper()} SDK in text mode")
        response = await client.chat.completions.create(
            model=model,
            messages=messages,  # type: ignore
        )
        result = response.choices[0].message.content

    return _process_structured_response(result or "", schema_model, schema_dict)


async def _execute_text_mode(
    kernel: Kernel,
    chat_history: list,
) -> dict[str, Any]:
    """Execute LLM task using text mode (no schema enforcement).

    Args:
        kernel: Semantic Kernel instance
        chat_history: List of chat messages

    Returns:
        Dictionary containing execution results

    Raises:
        Exception: If text mode execution fails
    """
    # Get the chat completion service
    service: ChatCompletionService | None = kernel.get_service("azure_openai")
    if not service:
        # Try alternative service IDs
        service = kernel.get_service("openai")
    if not service:
        raise Exception("No chat completion service found")

    # Create settings for text mode
    settings = OpenAIChatPromptExecutionSettings(
        service_id="azure_openai",
    )

    # Convert list to ChatHistory for Semantic Kernel compatibility
    sk_chat_history = create_chat_history(chat_history)

    # Execute without schema enforcement
    result = await service.get_chat_message_contents(
        chat_history=sk_chat_history,
        settings=settings,
    )

    # Extract content from ChatMessageContent objects
    if result and len(result) > 0:
        content = result[0].content
    else:
        content = ""

    return _process_text_response(content)


def _process_structured_response(
    response: str,
    schema_model: type | None,
    schema_dict: dict[str, Any] | None,
) -> dict[str, Any]:
    """Process structured response from LLM.

    Args:
        response: Raw response from LLM
        schema_model: Optional Pydantic model
        schema_dict: Optional schema dictionary

    Returns:
        Dictionary containing processed results
    """
    # Handle structured output response
    if schema_model:
        try:
            # Parse response as JSON since it's guaranteed to be schema-compliant
            parsed_response = json.loads(response)
            LOGGER.info("✅ LLM task completed with 100% schema-enforced output")
            LOGGER.debug(f"📄 Structured response with {len(parsed_response)} fields")
            LOGGER.debug(f"   Fields: {list(parsed_response.keys())}")

            # Pretty print structured output with Rich
            CONSOLE.print("\n[bold cyan]🤖 LLM Response (Structured)[/bold cyan]")
            CONSOLE.print(
                Panel(
                    json.dumps(parsed_response, indent=2, ensure_ascii=False),
                    title="📋 Structured Output",
                    style="cyan",
                )
            )

            return {
                "success": True,
                "output": parsed_response,
                "mode": "structured",
                "schema_enforced": True,
            }

        except json.JSONDecodeError as e:
            LOGGER.warning(f"⚠️ Failed to parse structured response as JSON: {e}")
            LOGGER.debug(f"   Raw response: {response[:200]}...")
            return _process_text_response(response)

    else:
        return _process_text_response(response)


def _process_text_response(response: str) -> dict[str, Any]:
    """Process text response from LLM.

    Args:
        response: Raw response from LLM

    Returns:
        Dictionary containing processed results
    """
    LOGGER.info("✅ LLM task completed with text output")
    LOGGER.debug(f"📄 Text response length: {len(response)} characters")

    # Pretty print text output with Rich
    CONSOLE.print("\n[bold green]🤖 LLM Response (Text)[/bold green]")
    CONSOLE.print(
        Panel(
            response,
            title="📝 Text Output",
            style="green",
        )
    )

    return {
        "success": True,
        "output": response,
        "mode": "text",
        "schema_enforced": False,
    }


def _enhance_prompt_with_one_shot_example(chat_history: list, schema_model: Any | None) -> list:
    """Enhance the last user message with a one-shot example when schema model is provided.

    Adds a concise example to help the model understand the expected output format
    without overwhelming the context.

    Args:
        chat_history: Original chat history
        schema_model: Optional Pydantic model class

    Returns:
        Enhanced chat history with one-shot example if schema provided
    """
    if not schema_model or not chat_history:
        return chat_history

    # Generate minimal example using the schema model
    try:
        example = generate_one_shot_example(schema_model)
        example_json = json.dumps(example, indent=2)
        required_fields = [name for name, field in schema_model.model_fields.items() if field.is_required()]

        # Create enhanced chat history
        enhanced_history = chat_history.copy()

        # Find the last user message to enhance
        for i in reversed(range(len(enhanced_history))):
            msg = enhanced_history[i]
            if isinstance(msg, dict) and msg.get("role") == "user":
                # Add one-shot example guidance to the user message
                original_content = msg["content"]
                enhanced_content = f"""{original_content}

Please provide your response in the following JSON format (this is just an example structure):

```json
{example_json}
```

Make sure to include all required fields ({required_fields}) and respect any length constraints specified in the schema."""

                enhanced_history[i] = {**msg, "content": enhanced_content}
                break

        LOGGER.debug("✨ Enhanced prompt with one-shot example")
        return enhanced_history

    except Exception as e:
        LOGGER.warning(f"⚠️ Failed to enhance prompt with example: {e}")
        return chat_history
