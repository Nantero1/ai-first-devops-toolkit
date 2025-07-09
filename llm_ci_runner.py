#!/usr/bin/env python3
# AI-First DevOps Toolkit – Created by Benjamin Linnik (https://technologyworkroom.blogspot.com/2025/06/building-ai-first-devops.html)
"""
LLM Runner - A simple CI/CD utility for running LLM tasks with Semantic Kernel

This script provides a zero-friction interface for running arbitrary LLM-driven tasks
in CI/CD pipelines, supporting structured outputs and enterprise authentication.

Usage:
    python llm_ci_runner.py \
        --input-file pr-context.json \
        --output-file review-result.json \
        --schema-file review-schema.json \
        --log-level DEBUG

Environment Variables:
    AZURE_OPENAI_ENDPOINT: Azure OpenAI endpoint URL
    AZURE_OPENAI_MODEL: Your custom model deployment name (e.g., gpt-4.1-nano)
    AZURE_OPENAI_API_VERSION: API version (default: 2024-12-01-preview)

Input Format:
    {
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user",
                "content": "Review this for issues",
                "name": "developer"
            }
        ],
        "context": {  // Optional
            "session_id": "job-123",
            "metadata": {...}
        }
    }
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

import yaml
from azure.core.exceptions import ClientAuthenticationError

# Azure authentication
from azure.identity.aio import DefaultAzureCredential
from json_schema_to_pydantic import create_model as create_model_from_schema  # type: ignore[import-untyped]

# Pydantic imports for schema handling
# Rich imports for beautiful console output
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.traceback import install as install_rich_traceback

# Semantic Kernel imports
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatPromptExecutionSettings
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import (
    AzureChatCompletion,
)
from semantic_kernel.contents import ChatHistory, ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.functions import KernelArguments
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.prompt_template import (
    HandlebarsPromptTemplate,
    PromptTemplateConfig,
)

# Tenacity for retry logic
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

# Install rich traceback for better error display
install_rich_traceback()

# Global CONSOLE for rich output
CONSOLE = Console()
LOGGER = logging.getLogger("llm_ci_runner")


class LLMRunnerError(Exception):
    """Base exception for LLM Runner errors."""

    pass


class InputValidationError(LLMRunnerError):
    """Raised when input validation fails."""

    pass


class AuthenticationError(LLMRunnerError):
    """Raised when Azure authentication fails."""

    pass


class LLMExecutionError(LLMRunnerError):
    """Raised when LLM execution fails."""

    pass


class SchemaValidationError(LLMRunnerError):
    """Raised when JSON schema validation or conversion fails."""

    pass


def create_dynamic_model_from_schema(
    schema_dict: dict[str, Any], model_name: str = "DynamicOutputModel"
) -> type[KernelBaseModel]:
    """
    Create a dynamic Pydantic model from JSON schema that inherits from KernelBaseModel.

    Uses the json-schema-to-pydantic library for robust schema conversion instead of manual implementation.

    Args:
        schema_dict: JSON schema dictionary
        model_name: Name for the generated model class

    Returns:
        Dynamic Pydantic model class inheriting from KernelBaseModel

    Raises:
        SchemaValidationError: If schema conversion fails
    """
    LOGGER.debug(f"🏗️  Creating dynamic model: {model_name}")

    try:
        # Use the dedicated library for robust JSON schema -> Pydantic conversion
        base_generated_model = create_model_from_schema(schema_dict)

        # Create a new class that inherits from both KernelBaseModel and the generated model
        # This ensures we get KernelBaseModel functionality while keeping the schema structure
        class DynamicKernelModel(KernelBaseModel, base_generated_model):  # type: ignore[valid-type, misc]
            pass

        # Set the name for better debugging
        DynamicKernelModel.__name__ = model_name
        DynamicKernelModel.__qualname__ = model_name

        # Count fields for logging
        field_count = len(base_generated_model.model_fields)
        required_fields = [name for name, field in base_generated_model.model_fields.items() if field.is_required()]

        LOGGER.info(f"✅ Created dynamic model with {field_count} fields")
        LOGGER.debug(f"   Required fields: {required_fields}")
        LOGGER.debug(f"   All fields: {list(base_generated_model.model_fields.keys())}")

        return DynamicKernelModel

    except Exception as e:
        raise SchemaValidationError(f"Failed to create dynamic model: {e}") from e


def setup_logging(log_level: str) -> logging.Logger:
    """
    Setup Rich logging with configurable levels, timestamps, and beautiful colors.

    RichHandler automatically routes log messages to appropriate streams:
    - INFO and DEBUG: stdout
    - WARNING, ERROR, CRITICAL: stderr

    This means we don't need separate console.print() calls for errors -
    the logger handles proper stdout/stderr routing with Rich formatting.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)

    Returns:
        Configured logger instance
    """
    # Configure logging with Rich handler
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                console=CONSOLE,
                show_time=True,
                show_level=True,
                show_path=False,
                markup=True,
                rich_tracebacks=True,
            )
        ],
    )

    # Suppress HTTP request logs from Azure libraries unless in DEBUG mode
    if log_level.upper() != "DEBUG":
        # Suppress HTTP request logs from Azure client libraries
        logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
        logging.getLogger("azure.core.pipeline.transport").setLevel(logging.WARNING)
        logging.getLogger("azure.identity").setLevel(logging.WARNING)
        logging.getLogger("azure.core.pipeline").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        # Suppress Semantic Kernel HTTP logs
        logging.getLogger("semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion").setLevel(
            logging.WARNING
        )

    LOGGER.info(f"[bold green]🚀 LLM Runner initialized with log level: {log_level.upper()}[/bold green]")
    return LOGGER


def parse_arguments() -> argparse.Namespace:
    """
    Parse CLI arguments for input file, output file, schema file, and log level.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="LLM Runner - Simple CI/CD utility for LLM tasks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Basic usage with JSON input (output defaults to result.json)
    python llm_ci_runner.py --input-file input.json

    # With structured output schema
    python llm_ci_runner.py --input-file input.json --schema-file schema.json

    # With YAML files
    python llm_ci_runner.py --input-file input.yaml --output-file result.yaml

    # Using Handlebars templates with variables
    python llm_ci_runner.py --template-file prompt.hbs --template-vars vars.yaml --schema-file schema.yaml

    # Using Handlebars templates without variables (static template)
    python llm_ci_runner.py --template-file static-prompt.hbs --schema-file schema.yaml

    # With debug logging
    python llm_ci_runner.py --input-file input.json --log-level DEBUG

Environment Variables:
    AZURE_OPENAI_ENDPOINT    Azure OpenAI endpoint URL
    AZURE_OPENAI_MODEL       Model deployment name
    AZURE_OPENAI_API_VERSION API version (default: 2024-12-01-preview)
        """,
    )

    # Create mutually exclusive group for input methods
    input_group = parser.add_mutually_exclusive_group(required=True)

    input_group.add_argument(
        "--input-file",
        type=Path,
        help="JSON/YAML file containing messages and optional context",
    )

    input_group.add_argument(
        "--template-file",
        type=Path,
        help="Handlebars .hbs template file for prompt generation",
    )

    parser.add_argument(
        "--template-vars",
        type=Path,
        help="JSON/YAML file containing template variables (optional with --template-file)",
    )

    parser.add_argument(
        "--output-file",
        type=Path,
        default=Path("result.json"),
        help="Output file for LLM response (JSON/YAML format based on extension, default: result.json)",
    )

    parser.add_argument(
        "--schema-file",
        type=Path,
        help="Optional JSON/YAML schema file for structured output",
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)",
    )

    args = parser.parse_args()

    # Note: template-vars is optional when template-file is used
    # Templates may not require variables (e.g., static templates)

    return args


def load_input_file(input_file: Path) -> dict[str, Any]:
    """
    Load and parse input JSON or YAML file containing messages and optional context.

    Args:
        input_file: Path to input JSON or YAML file

    Returns:
        Parsed data

    Raises:
        InputValidationError: If file doesn't exist or format is invalid
    """
    LOGGER.debug(f"📂 Loading input file: {input_file}")

    if not input_file.exists():
        raise InputValidationError(f"Input file not found: {input_file}")

    try:
        with open(input_file, encoding="utf-8") as f:
            # Detect format based on file extension
            if input_file.suffix.lower() in [".yaml", ".yml"]:
                LOGGER.debug("🔍 Detected YAML format")
                data = yaml.safe_load(f)
            else:
                LOGGER.debug("🔍 Detected JSON format")
                data = json.load(f)

        # Validate required 'messages' field
        if "messages" not in data:
            raise InputValidationError("Input file must contain 'messages' field")

        if not isinstance(data["messages"], list) or len(data["messages"]) == 0:
            raise InputValidationError("'messages' must be a non-empty array")

        LOGGER.debug(f"✅ Loaded {len(data['messages'])} messages")
        if "context" in data:
            LOGGER.debug(f"📋 Additional context provided: {list(data['context'].keys())}")

        return data  # type: ignore[no-any-return]

    except yaml.YAMLError as e:
        raise InputValidationError(f"Invalid YAML in input file: {e}") from e
    except json.JSONDecodeError as e:
        raise InputValidationError(f"Invalid JSON in input file: {e}") from e
    except Exception as e:
        raise InputValidationError(f"Error reading input file: {e}") from e


def create_chat_history(messages: list[dict[str, Any]]) -> ChatHistory:
    """
    Create Semantic Kernel ChatHistory from messages array.

    Args:
        messages: List of message dictionaries with role, content, and optional name

    Returns:
        ChatHistory object ready for Semantic Kernel

    Raises:
        InputValidationError: If message format is invalid
    """
    LOGGER.debug("🔄 Converting messages to ChatHistory")

    chat_history = ChatHistory()

    for i, msg in enumerate(messages):
        try:
            # Validate message structure
            if "role" not in msg or "content" not in msg:
                raise InputValidationError(f"Message {i} missing required 'role' or 'content' field")

            # Create ChatMessageContent
            chat_message = ChatMessageContent(
                role=AuthorRole(msg["role"]),
                content=msg["content"],
                name=msg.get("name"),  # Optional name field
            )

            chat_history.add_message(chat_message)
            LOGGER.debug(f"  ➕ Added {msg['role']} message ({len(msg['content'])} chars)")

        except ValueError as e:
            raise InputValidationError(f"Invalid role '{msg.get('role')}' in message {i}: {e}") from e
        except Exception as e:
            raise InputValidationError(f"Error processing message {i}: {e}") from e

    LOGGER.info(f"✅ Created ChatHistory with {len(chat_history)} messages")
    return chat_history


async def setup_azure_service() -> tuple[AzureChatCompletion, DefaultAzureCredential | None]:
    """
    Setup Azure OpenAI service with dual authentication support.

    Authentication Methods (in priority order):
    1. Azure RBAC (default): Uses DefaultAzureCredential for enterprise scenarios
    2. API Key (fallback): Uses AZURE_OPENAI_API_KEY environment variable

    This provides flexibility for different deployment scenarios while maintaining
    security best practices by defaulting to RBAC authentication.

    Returns:
        Tuple of (configured AzureChatCompletion service, credential or None)

    Raises:
        AuthenticationError: If Azure authentication fails
    """
    LOGGER.debug("🔐 Setting up Azure OpenAI authentication")

    # Get environment variables
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    model = os.getenv("AZURE_OPENAI_MODEL")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")

    if not endpoint:
        raise AuthenticationError("AZURE_OPENAI_ENDPOINT environment variable not set")
    if not model:
        raise AuthenticationError("AZURE_OPENAI_MODEL environment variable not set")

    LOGGER.debug(f"  🌐 Endpoint: {endpoint}")
    LOGGER.debug(f"  🤖 Model: {model}")
    LOGGER.debug(f"  📅 API Version: {api_version}")

    try:
        # Try API key authentication first if available
        if api_key:
            LOGGER.info("🔑 Using API Key authentication")
            service = AzureChatCompletion(
                deployment_name=model,
                endpoint=endpoint,
                api_key=api_key,
                api_version=api_version,
            )
            LOGGER.info("✅ Azure OpenAI service configured successfully (API Key)")
            return service, None

        # Fallback to RBAC authentication
        LOGGER.info("🔐 Using Azure RBAC authentication")
        # Setup async Azure credential
        credential = DefaultAzureCredential()

        # Define a callable token provider with better error handling
        async def token_provider(scopes: list[str] | None = None) -> str:
            if scopes is None:
                scopes = ["https://cognitiveservices.azure.com/.default"]
            try:
                # Azure credential handles its own HTTP requests internally
                token = await credential.get_token(*scopes)
                LOGGER.debug(f"✅ Token acquired successfully, expires: {token.expires_on}")
                return token.token
            except Exception as e:
                LOGGER.error(f"❌ Failed to acquire Azure token: {e}")
                LOGGER.info("💡 Ensure you're logged in with 'az login' or have proper managed identity permissions")
                raise AuthenticationError(f"Azure token acquisition failed: {e}") from e

        # Create Azure ChatCompletion service
        service = AzureChatCompletion(
            deployment_name=model,
            endpoint=endpoint,
            ad_token_provider=token_provider,
            api_version=api_version,
        )

        LOGGER.info("✅ Azure OpenAI service configured successfully")
        return service, credential

    except ClientAuthenticationError as e:
        raise AuthenticationError(f"Azure authentication failed: {e}") from e
    except Exception as e:
        raise AuthenticationError(f"Error setting up Azure service: {e}") from e


def load_schema_file(schema_file: Path | None) -> type[KernelBaseModel] | None:
    """
    Load JSON or YAML schema from file and convert to dynamic Pydantic model for 100% enforcement.

    Args:
        schema_file: Optional path to JSON or YAML schema file

    Returns:
        Dynamic KernelBaseModel class or None if no schema

    Raises:
        InputValidationError: If schema file cannot be loaded or is invalid format
        SchemaValidationError: If schema conversion to Pydantic model fails
    """
    if not schema_file:
        LOGGER.debug("📋 No schema file provided - using text output")
        return None

    LOGGER.debug(f"📋 Loading schema from: {schema_file}")

    try:
        if not schema_file.exists():
            raise InputValidationError(f"Schema file not found: {schema_file}")

        with open(schema_file, encoding="utf-8") as f:
            # Detect format based on file extension
            if schema_file.suffix.lower() in [".yaml", ".yml"]:
                LOGGER.debug("🔍 Detected YAML schema format")
                schema_dict = yaml.safe_load(f)
            else:
                LOGGER.debug("🔍 Detected JSON schema format")
                schema_content = f.read().strip()
                schema_dict = json.loads(schema_content)

        if not isinstance(schema_dict, dict):
            raise InputValidationError("Schema must be a valid JSON object")

        # Create dynamic Pydantic model from schema
        model_name = f"Schema_{schema_file.stem.title().replace('-', '').replace('_', '')}"
        dynamic_model = create_dynamic_model_from_schema(schema_dict, model_name)

        LOGGER.info(f"✅ Schema converted to Pydantic model: {model_name}")
        return dynamic_model

    except yaml.YAMLError as e:
        raise InputValidationError(f"Invalid YAML in schema file: {e}") from e
    except json.JSONDecodeError as e:
        raise InputValidationError(f"Invalid JSON in schema file: {e}") from e
    except (InputValidationError, SchemaValidationError):
        raise
    except Exception as e:
        raise InputValidationError(f"Error loading schema file: {e}") from e


def load_template_vars(template_vars_file: Path) -> dict[str, Any]:
    """
    Load template variables from JSON or YAML file.

    Args:
        template_vars_file: Path to template variables file

    Returns:
        Dictionary of template variables

    Raises:
        InputValidationError: If file cannot be loaded or is invalid format
    """
    LOGGER.debug(f"📋 Loading template variables from: {template_vars_file}")

    try:
        if not template_vars_file.exists():
            raise InputValidationError(f"Template variables file not found: {template_vars_file}")

        with open(template_vars_file, encoding="utf-8") as f:
            # Detect format based on file extension
            if template_vars_file.suffix.lower() in [".yaml", ".yml"]:
                LOGGER.debug("🔍 Detected YAML template variables format")
                vars_dict = yaml.safe_load(f)
            else:
                LOGGER.debug("🔍 Detected JSON template variables format")
                vars_dict = json.load(f)

        if not isinstance(vars_dict, dict):
            raise InputValidationError("Template variables must be a valid object")

        LOGGER.info(f"✅ Loaded {len(vars_dict)} template variables")
        LOGGER.debug(f"   Variables: {list(vars_dict.keys())}")
        return vars_dict

    except yaml.YAMLError as e:
        raise InputValidationError(f"Invalid YAML in template variables file: {e}") from e
    except json.JSONDecodeError as e:
        raise InputValidationError(f"Invalid JSON in template variables file: {e}") from e
    except Exception as e:
        raise InputValidationError(f"Error loading template variables file: {e}") from e


def load_handlebars_template(template_file: Path) -> HandlebarsPromptTemplate:
    """
    Load Handlebars template from .hbs file and create PromptTemplate instance.

    Args:
        template_file: Path to Handlebars .hbs template file

    Returns:
        Configured HandlebarsPromptTemplate instance

    Raises:
        InputValidationError: If template file cannot be loaded or is invalid
    """
    LOGGER.debug(f"📋 Loading Handlebars template from: {template_file}")

    try:
        if not template_file.exists():
            raise InputValidationError(f"Template file not found: {template_file}")

        with open(template_file, encoding="utf-8") as f:
            template_content = f.read()

        # Create PromptTemplateConfig with raw Handlebars template content
        try:
            template_config = PromptTemplateConfig(
                template=template_content,
                template_format="handlebars",
                name=template_file.stem,
                description=f"Handlebars template loaded from {template_file.name}",
            )
        except Exception as e:
            raise InputValidationError(f"Invalid Handlebars template content: {e}") from e

        # Create HandlebarsPromptTemplate instance
        template = HandlebarsPromptTemplate(prompt_template_config=template_config)

        LOGGER.info(f"✅ Loaded Handlebars template: {template_config.name or 'unnamed'}")
        return template

    except InputValidationError:
        raise
    except Exception as e:
        raise InputValidationError(f"Error loading template file: {e}") from e


async def render_handlebars_template(
    template: HandlebarsPromptTemplate,
    template_vars: dict[str, Any],
    kernel: Kernel,
) -> str:
    """
    Render Handlebars template with provided variables.

    Args:
        template: HandlebarsPromptTemplate instance
        template_vars: Dictionary of template variables
        kernel: Semantic Kernel instance

    Returns:
        Rendered template content

    Raises:
        InputValidationError: If template rendering fails
    """
    LOGGER.debug("🔄 Rendering Handlebars template")

    try:
        # Create KernelArguments from template variables
        arguments = KernelArguments(**template_vars)

        # Render template
        rendered_content = await template.render(kernel, arguments)

        LOGGER.info("✅ Handlebars template rendered successfully")
        LOGGER.debug(f"📄 Rendered content length: {len(rendered_content)} characters")

        return rendered_content

    except Exception as e:
        raise InputValidationError(f"Error rendering Handlebars template: {e}") from e


def parse_rendered_template_to_chat_history(rendered_content: str) -> ChatHistory:
    """
    Parse rendered Handlebars template content into ChatHistory.

    Expects the rendered content to contain <message role="...">content</message> blocks.

    Args:
        rendered_content: Rendered template content with <message> blocks

    Returns:
        ChatHistory object ready for Semantic Kernel

    Raises:
        InputValidationError: If message parsing fails
    """
    import re

    LOGGER.debug("🔄 Parsing rendered template to ChatHistory")

    try:
        # Find all <message> blocks using regex
        message_pattern = r'<message\s+role="([^"]+)"[^>]*>(.*?)</message>'
        matches = re.findall(message_pattern, rendered_content, re.DOTALL | re.IGNORECASE)

        if not matches:
            raise InputValidationError("No <message> blocks found in rendered template")

        chat_history = ChatHistory()

        for i, (role, content) in enumerate(matches):
            try:
                # Clean up content (strip whitespace)
                cleaned_content = content.strip()

                # Create ChatMessageContent
                chat_message = ChatMessageContent(
                    role=AuthorRole(role.lower()),
                    content=cleaned_content,
                )

                chat_history.add_message(chat_message)
                LOGGER.debug(f"  ➕ Added {role} message ({len(cleaned_content)} chars)")

            except ValueError as e:
                raise InputValidationError(f"Invalid role '{role}' in message {i}: {e}") from e

        LOGGER.info(f"✅ Parsed {len(chat_history)} messages from rendered template")
        return chat_history

    except InputValidationError:
        raise
    except Exception as e:
        raise InputValidationError(f"Error parsing rendered template: {e}") from e


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
    service: AzureChatCompletion,
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


def write_output_file(output_file: Path, response: str | dict[str, Any]) -> None:
    """
    Write LLM response to output file in JSON or YAML format based on file extension.

    Args:
        output_file: Path to output file
        response: LLM response to write

    Raises:
        LLMRunnerError: If file writing fails
    """
    LOGGER.debug(f"💾 Writing output to: {output_file}")

    try:
        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Prepare output data
        output_data = {
            "success": True,
            "response": response,
            "metadata": {
                "runner": "llm_ci_runner.py",
                "timestamp": "auto-generated",  # You could add actual timestamp
            },
        }

        # Write to file based on extension
        with open(output_file, "w", encoding="utf-8") as f:
            if output_file.suffix.lower() in [".yaml", ".yml"]:
                LOGGER.debug("🔍 Writing YAML output format")
                yaml.dump(
                    output_data,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    indent=2,
                )
            else:
                LOGGER.debug("🔍 Writing JSON output format")
                json.dump(output_data, f, indent=2, ensure_ascii=False)

        LOGGER.info(f"✅ Output written to: {output_file}")

    except Exception as e:
        raise LLMRunnerError(f"Error writing output file: {e}") from e


async def main() -> None:
    """
    Main entry point for LLM Runner.

    Orchestrates the entire pipeline from input parsing to output generation.
    Supports both direct input files and Handlebars template rendering.
    """
    credential = None
    try:
        # Parse CLI arguments
        args = parse_arguments()

        # Setup logging with Rich
        setup_logging(args.log_level)

        # Setup Azure OpenAI service
        LOGGER.info("🔐 Authenticating with Azure...")
        service, credential = await setup_azure_service()

        # Load schema and convert to dynamic Pydantic model if provided
        schema_model = load_schema_file(args.schema_file)

        # Choose execution path based on input method
        if args.template_file:
            # Template-based execution path
            LOGGER.info("📝 Using Handlebars template mode...")

            # Load template variables (optional)
            if args.template_vars:
                LOGGER.info("📥 Loading template variables...")
                template_vars = load_template_vars(args.template_vars)
            else:
                LOGGER.info("📝 No template variables provided - using empty variables")
                template_vars = {}

            # Load Handlebars template
            LOGGER.info("📋 Loading Handlebars template...")
            template = load_handlebars_template(args.template_file)

            # Create kernel for rendering
            kernel = Kernel()
            kernel.add_service(service)

            # Render template with variables
            LOGGER.info("🔄 Rendering template...")
            rendered_content = await render_handlebars_template(template, template_vars, kernel)

            # Parse rendered content to ChatHistory
            chat_history = parse_rendered_template_to_chat_history(rendered_content)

            # No additional context in template mode
            context = None

        else:
            # Direct input file execution path
            LOGGER.info("📥 Using direct input file mode...")

            # Load and validate input file
            input_data = load_input_file(args.input_file)

            # Create ChatHistory from messages
            chat_history = create_chat_history(input_data["messages"])

            # Extract context if provided
            context = input_data.get("context")

        # Execute LLM task with 100% schema enforcement
        LOGGER.info("🤖 Processing with LLM...")
        response = await execute_llm_task(
            service=service,
            chat_history=chat_history,
            context=context,
            schema_model=schema_model,
        )

        # Write output file
        LOGGER.info("💾 Saving results...")
        write_output_file(args.output_file, response)

        # Success message
        CONSOLE.print("\n[bold green]🎉 LLM Runner completed successfully![/bold green]")
        CONSOLE.print(f"[dim]📁 Output saved to: {args.output_file}[/dim]")

    except LLMRunnerError as e:
        LOGGER.error(f"❌ {e}")
        sys.exit(1)

    except KeyboardInterrupt:
        LOGGER.warning("⚠️  Operation cancelled by user")
        CONSOLE.print("\n[yellow]⚠️  Operation cancelled[/yellow]")
        sys.exit(1)

    except Exception as e:
        # Unexpected error - log with full traceback
        LOGGER.critical(f"💥 Unexpected error: {e}", exc_info=True)
        sys.exit(1)

    finally:
        # Properly close Azure credential to prevent unclosed client session warnings
        if credential is not None:
            try:
                await credential.close()
                LOGGER.debug("🔒 Azure credential closed successfully")
            except Exception as e:
                LOGGER.debug(f"Warning: Failed to close Azure credential: {e}")
                # Don't raise - this is cleanup, not critical


def cli_main() -> None:
    """Synchronous wrapper for the async main function."""
    asyncio.run(main())


if __name__ == "__main__":
    cli_main()
