"""
LLM execution functionality for LLM CI Runner.

This module provides the core LLM execution logic with retry mechanisms
and structured output handling using Semantic Kernel.
"""

import json
import logging
from typing import Any

from azure.core.exceptions import ClientAuthenticationError
from rich.console import Console
from rich.panel import Panel
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion, OpenAIChatPromptExecutionSettings
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import (
    AzureChatCompletion,
)
from semantic_kernel.contents import ChatHistory
from semantic_kernel.functions import KernelArguments
from semantic_kernel.kernel_pydantic import KernelBaseModel
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from .exceptions import LLMExecutionError

LOGGER = logging.getLogger(__name__)
CONSOLE = Console()


@retry(
    retry=retry_if_exception_type(
        (
            # Network-related exceptions that should be retried
            ConnectionError,
            TimeoutError,
            # Azure-specific exceptions that might be transient
            ClientAuthenticationError,
            # Generic exceptions that might be transient
            RuntimeError,
        )
    ),
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(initial=1, max=10, jitter=2),
    before_sleep=before_sleep_log(LOGGER, logging.WARNING),
    reraise=True,
)
async def execute_llm_task(
    service: AzureChatCompletion | OpenAIChatCompletion,
    chat_history: ChatHistory,
    context: dict[str, Any] | None,
    schema_model: type[KernelBaseModel] | None,
) -> str | dict[str, Any]:
    """
    Execute LLM task using Semantic Kernel with 100% schema enforcement.

    Uses KernelBaseModel with response_format for token-level constraint enforcement,
    guaranteeing 100% schema compliance when schema_model is provided.

    Args:
        service: Azure ChatCompletion service
        chat_history: ChatHistory with messages
        context: Optional context for KernelArguments
        schema_model: Optional KernelBaseModel class for structured output enforcement

    Returns:
        LLM response as string or structured dict with guaranteed schema compliance

    Raises:
        LLMExecutionError: If LLM execution fails
    """
    LOGGER.debug("🤖 Executing LLM task")

    try:
        # Create kernel and add service
        kernel = Kernel()
        kernel.add_service(service)

        # Setup execution settings with proper structured output enforcement
        settings = OpenAIChatPromptExecutionSettings()

        if schema_model:
            # CRITICAL: Use response_format with KernelBaseModel for 100% enforcement
            # This triggers Azure OpenAI's structured outputs with token-level constraints
            settings.response_format = schema_model
            LOGGER.info(f"🔒 Using 100% schema enforcement with model: {schema_model.__name__}")
            LOGGER.debug("   → Token-level constraint enforcement active")
        else:
            LOGGER.debug("📝 Using text output mode (no schema)")

        # Create kernel arguments
        args = KernelArguments(settings=settings)

        # Add context if provided
        if context:
            for key, value in context.items():
                args[key] = value
            LOGGER.debug(f"📋 Added context: {list(context.keys())}")

        # Use the chat completion service directly with chat_history
        result = await service.get_chat_message_contents(
            chat_history=chat_history,
            settings=settings,
            arguments=args,
        )
        LOGGER.debug(result)

        # Extract result content from Semantic Kernel response
        if isinstance(result, list) and len(result) > 0:
            # Direct service call returns list of ChatMessageContent
            response = result[0].content if hasattr(result[0], "content") else str(result[0])
        elif hasattr(result, "value") and result.value:
            # Kernel invoke_prompt returns FunctionResult with value
            if isinstance(result.value, list) and len(result.value) > 0:
                response = result.value[0].content if hasattr(result.value[0], "content") else str(result.value[0])
            else:
                response = str(result.value)
        else:
            response = str(result)

        LOGGER.debug(
            f"📄 Extracted response: {response[:100]}..."
            if len(response) > 100
            else f"📄 Extracted response: {response}"
        )

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
                        border_style="cyan",
                    )
                )

                return parsed_response  # type: ignore[no-any-return]
            except json.JSONDecodeError as e:
                # This should never happen with proper structured output enforcement
                raise LLMExecutionError(f"Schema enforcement failed - invalid JSON returned: {e}") from e

        # Text output mode
        LOGGER.info("✅ LLM task completed successfully")
        LOGGER.debug(f"📄 Response length: {len(response)} characters")

        # Pretty print text output with Rich
        CONSOLE.print("\n[bold green]🤖 LLM Response (Text)[/bold green]")
        CONSOLE.print(Panel(response, title="📝 Text Output", style="green", border_style="green"))

        return response

    except LLMExecutionError:
        raise
    except Exception as e:
        raise LLMExecutionError(f"LLM execution failed: {e}") from e
