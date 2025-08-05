"""
Core execution logic for LLM CI Runner.

This module provides the main orchestration logic that ties together
all the components: input loading, template processing, LLM execution,
and output writing. Functions are designed to be used both as CLI
commands and as library methods for programmatic access.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any

from rich.panel import Panel
from rich.traceback import install as install_rich_traceback
from semantic_kernel import Kernel
from semantic_kernel.contents import ChatHistory
from semantic_kernel.functions.kernel_function_from_prompt import KernelFunctionFromPrompt

from .exceptions import (
    InputValidationError,
    LLMRunnerError,
    SchemaValidationError,
)
from .io_operations import (
    create_chat_history,
    load_input_file,
    load_schema_file,
    parse_arguments,
    write_output_file,
)
from .llm_execution import execute_llm_task
from .llm_service import setup_llm_service
from .logging_config import CONSOLE, setup_logging
from .templates import (
    load_template,
    load_template_vars,
    parse_rendered_template_to_chat_history,
    render_template,
)

# Install rich traceback for better error display
install_rich_traceback()

LOGGER = logging.getLogger(__name__)


def _extract_model_id_from_yaml(yaml_function: KernelFunctionFromPrompt) -> str | None:
    """
    Extract model_id from YAML execution_settings.

    This function looks for model_id in the YAML template's execution_settings
    and returns it to be used as the actual deployment_name.

    Args:
        yaml_function: The loaded Semantic Kernel function from YAML

    Returns:
        model_id if found in YAML, None otherwise
    """
    try:
        if hasattr(yaml_function, "prompt_execution_settings"):
            # Check for azure_openai execution settings
            azure_settings = yaml_function.prompt_execution_settings.get("azure_openai")
            if azure_settings and hasattr(azure_settings, "extension_data"):
                model_id = azure_settings.extension_data.get("model_id")
                if model_id and isinstance(model_id, str):
                    LOGGER.debug(f"🎯 YAML specifies model_id: {model_id}")
                    return str(model_id)  # Explicit cast to satisfy mypy

        LOGGER.debug("🎯 No model_id found in YAML execution_settings")
        return None

    except Exception as e:
        LOGGER.warning(f"⚠️ Error extracting model_id from YAML: {e}")
        return None


async def _create_azure_service_with_model(model_id: str) -> tuple[Any, Any]:
    """
    Create Azure OpenAI service with specific model as deployment_name.

    This creates a new service instance using the YAML-specified model_id
    as the actual deployment_name, enabling dynamic model selection.

    Args:
        model_id: The model/deployment name from YAML

    Returns:
        Tuple of (Configured AzureChatCompletion service, credential or None)
    """
    import os

    from azure.identity.aio import DefaultAzureCredential, get_bearer_token_provider
    from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import AzureChatCompletion

    # Get Azure configuration from environment
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")

    if not endpoint:
        raise ValueError("AZURE_OPENAI_ENDPOINT environment variable is required")

    if api_key:
        # API key authentication
        service = AzureChatCompletion(
            service_id="azure_openai",
            endpoint=endpoint,
            api_key=api_key,
            deployment_name=model_id,  # Use YAML model_id as deployment_name
            api_version=api_version,
        )
        return service, None  # No credential to close for API key auth
    else:
        # RBAC authentication
        credential = DefaultAzureCredential()
        token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")
        service = AzureChatCompletion(
            service_id="azure_openai",
            endpoint=endpoint,
            deployment_name=model_id,  # Use YAML model_id as deployment_name
            api_version=api_version,
            ad_token_provider=token_provider,
        )
        return service, credential  # Return credential for proper cleanup


async def process_input_file(input_file: str) -> list[dict[str, str]]:
    """
    Process input file and create chat history.

    Loads input data from JSON file and converts it to chat history format
    for LLM processing. This function provides the core input file processing
    logic that can be used both by CLI and library consumers.

    Args:
        input_file: Path to JSON input file containing messages

    Returns:
        List of message dictionaries in chat history format

    Raises:
        InputValidationError: If input file is invalid or missing
        LLMRunnerError: If file processing fails
    """
    LOGGER.info("📂 Processing input files")

    # Load input data
    input_data = load_input_file(Path(input_file))
    messages = input_data["messages"]

    # Create chat history
    chat_history = create_chat_history(messages)

    # Convert to list format using common helper
    return _convert_chat_history_to_list(chat_history)


def _template_requires_json_output(template: KernelFunctionFromPrompt) -> bool:
    """
    Check if SK template requires JSON output based on execution settings.

    Examines the template's execution settings to determine if it has
    a json_schema response_format defined, which indicates structured
    JSON output is required rather than optional.

    Args:
        template: SK template function to examine

    Returns:
        True if template explicitly requires JSON output, False otherwise
    """
    try:
        # Check if template has prompt_execution_settings
        if not hasattr(template, "prompt_execution_settings"):
            return False

        settings = template.prompt_execution_settings

        # Check for Azure OpenAI settings (most common case)
        if "azure_openai" in settings:
            azure_settings = settings["azure_openai"]

            # Check for response_format in extension_data
            if (
                hasattr(azure_settings, "extension_data")
                and isinstance(azure_settings.extension_data, dict)
                and "response_format" in azure_settings.extension_data
            ):
                response_format = azure_settings.extension_data["response_format"]

                # If response_format specifies json_schema, JSON is required
                if (
                    isinstance(response_format, dict)
                    and response_format.get("type") == "json_schema"
                    and "json_schema" in response_format
                ):
                    return True

        # Check for OpenAI settings as fallback
        if "openai" in settings:
            openai_settings = settings["openai"]

            # Similar check for OpenAI settings
            if (
                hasattr(openai_settings, "extension_data")
                and isinstance(openai_settings.extension_data, dict)
                and "response_format" in openai_settings.extension_data
            ):
                response_format = openai_settings.extension_data["response_format"]

                if (
                    isinstance(response_format, dict)
                    and response_format.get("type") == "json_schema"
                    and "json_schema" in response_format
                ):
                    return True

        return False

    except (AttributeError, KeyError, TypeError):
        # If we can't determine schema requirements, assume JSON is not required
        # This ensures backward compatibility and avoids false failures
        return False


def _load_template_variables(template_vars_file: str | None) -> dict[str, Any]:
    """Load template variables from file or return empty dict."""
    if template_vars_file:
        return load_template_vars(Path(template_vars_file))
    else:
        LOGGER.info("📝 No template variables provided - using defaults")
        return {}


def _detect_template_format(template_file: str) -> str:
    """Detect template format from file extension."""
    extension = Path(template_file).suffix.lower()
    if extension in [".yaml", ".yml"]:
        return "semantic-kernel"
    elif extension in [".hbs"]:
        return "handlebars"
    elif extension in [".j2", ".jinja"]:
        return "jinja2"
    else:
        # Default to handlebars for unknown extensions
        return "handlebars"


async def _process_template_unified(
    template: Any,  # KernelFunctionFromPrompt | HandlebarsPromptTemplate | Jinja2PromptTemplate
    template_format: str,  # "semantic-kernel", "handlebars", "jinja2"
    template_vars: dict[str, Any],  # Unified variables
    service: Any,  # LLM service
    schema_result: tuple[Any, dict] | None,  # Schema model + dict
    output_file: str | None,  # Output file path
    additional_credentials: list[Any] | None = None,  # List to track additional credentials
) -> str | dict[str, Any]:
    """
    Unified template processor that handles all template types.

    This function consolidates the logic from the old duplicate functions:
    - process_sk_yaml_template_with_vars()
    - process_handlebars_jinja_template_with_vars()

    Args:
        template: Loaded template object (SK, Handlebars, or Jinja2)
        template_format: Template format identifier
        template_vars: Template variables dictionary
        service: LLM service instance
        schema_result: Optional schema validation tuple
        output_file: Optional output file path

    Returns:
        Response from LLM execution - string or dict based on schema
    """
    from semantic_kernel.functions.kernel_function_from_prompt import KernelFunctionFromPrompt

    # Initialize response variable with proper typing
    response: str | dict[str, Any]

    if isinstance(template, KernelFunctionFromPrompt):
        # SK YAML template - dynamic service creation based on YAML model_id
        LOGGER.info("🔧 Processing Semantic Kernel YAML template")

        # Extract model_id from YAML and create appropriate service
        try:
            yaml_model_id = _extract_model_id_from_yaml(template)

            if yaml_model_id:
                # Create service with YAML model_id as deployment_name
                dynamic_service, dynamic_credential = await _create_azure_service_with_model(yaml_model_id)
                LOGGER.info(f"✅ Using YAML-specified model: {yaml_model_id}")
                kernel = _create_kernel_with_service(dynamic_service)

                # Track additional credential for cleanup
                if dynamic_credential and additional_credentials is not None:
                    additional_credentials.append(dynamic_credential)
            else:
                # Fallback to environment-configured service
                LOGGER.info("✅ Using environment model")
                kernel = _create_kernel_with_service(service)

        except Exception as e:
            LOGGER.warning(f"⚠️ Dynamic service creation failed, using environment service: {e}")
            # Fallback to original service
            kernel = _create_kernel_with_service(service)

        # Execute template with variables
        try:
            result = await kernel.invoke(template, **template_vars)

            # Check if template requires JSON output
            requires_json = _template_requires_json_output(template)

            if requires_json and result and result.value:
                # Parse JSON from SK result
                import json

                content = result.value[0].content if hasattr(result.value[0], "content") else str(result.value[0])
                try:
                    response = json.loads(content)
                    LOGGER.info(f"✅ SK template executed successfully - JSON response: {type(response)}")
                except json.JSONDecodeError as e:
                    raise SchemaValidationError(f"Schema enforcement failed: Invalid JSON response - {e}") from e
            else:
                # Return as string
                response = str(result.value[0]) if result and result.value else ""
                LOGGER.info(f"✅ SK template executed successfully - string response: {len(response)} chars")

        except Exception as e:
            LOGGER.error(f"❌ SK template execution failed: {e}")
            raise

    else:
        # Handlebars/Jinja2 template workflow
        LOGGER.info(f"🔧 Processing {template_format} template")

        # Use template variables or empty dict
        vars_dict = template_vars if template_vars is not None else {}
        LOGGER.debug(f"🔧 Using template variables: {list(vars_dict.keys())}")

        # Create kernel for template rendering
        kernel = Kernel()

        # Render template
        rendered_content = await render_template(template, vars_dict, kernel)

        # Parse rendered content to chat history
        chat_history = parse_rendered_template_to_chat_history(rendered_content)

        # Convert to list format
        chat_history_list = _convert_chat_history_to_list(chat_history)

        # Execute with LLM and schema enforcement
        if schema_result:
            # Create temporary schema file for execute_llm_task function
            import json
            import os
            import tempfile

            schema_model, schema_dict = schema_result
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp_file:
                json.dump(schema_dict, tmp_file, indent=2)
                schema_file_path = tmp_file.name

            # Create kernel for execution
            kernel = _create_kernel_with_service(service)

            # Use execute_llm_task for proper schema enforcement
            llm_result = await execute_llm_task(kernel, chat_history_list, schema_file_path, output_file)

            # Clean up temporary file
            os.unlink(schema_file_path)

            # Extract response from result
            if isinstance(llm_result, dict) and "output" in llm_result:
                # Keep structured output as dict, convert text output to string
                if llm_result.get("mode") == "structured":
                    response = llm_result["output"]
                else:
                    response = str(llm_result["output"])
            else:
                response = str(llm_result)
        else:
            # No schema - use simple execution
            response = await execute_llm_with_chat_history(service, chat_history_list, None, output_file)

    # Save output if requested
    if output_file:
        _write_output_if_specified(output_file, response)
        LOGGER.info(f"💾 Response saved to {output_file}")

    return response


def _convert_chat_history_to_list(chat_history: Any) -> list[dict[str, str]]:
    """Convert ChatHistory object to list format if needed."""
    if isinstance(chat_history, ChatHistory):
        chat_history_list: list[dict[str, str]] = []
        for msg in chat_history.messages:
            chat_history_list.append(
                {
                    "role": (msg.role.value if hasattr(msg.role, "value") else str(msg.role)),
                    "content": msg.content,
                }
            )
        return chat_history_list

    return chat_history  # type: ignore


def _create_kernel_with_service(service: Any) -> Kernel:
    """Create and configure Semantic Kernel with service.

    Adds comprehensive debugging for service registration to help diagnose
    KernelServiceNotFoundError issues with SK service selection.
    """
    kernel = Kernel()

    # Add service with debug logging
    kernel.add_service(service)

    # Debug: Verify service registration
    services = kernel.services
    LOGGER.debug(f"🔍 Registered services: {services}")
    LOGGER.debug(f"🔍 Service type: {type(service)}")
    LOGGER.debug(f"🔍 Service ID: {getattr(service, 'service_id', 'NO_ID')}")
    LOGGER.debug(f"🔍 Service attributes: {[attr for attr in dir(service) if not attr.startswith('_')]}")

    # Additional SK service validation
    if hasattr(service, "ai_model_id"):
        LOGGER.debug(f"🔍 AI Model ID: {service.ai_model_id}")

    return kernel


def _write_output_if_specified(output_file: str | None, content: str | dict[str, Any]) -> None:
    """Write content to output file if specified."""
    if output_file:
        LOGGER.info("📝 Writing output")
        write_output_file(Path(output_file), content)


async def load_template_from_string(template_content: str, template_format: str) -> Any:
    """
    Load template from string content with specified format.

    PURPOSE: Creates template objects from string content rather than files,
    enabling direct Python integration without requiring temporary file creation.

    Args:
        template_content: Template content as string
        template_format: Template format ("handlebars", "jinja2", "semantic-kernel")

    Returns:
        Template object (HandlebarsPromptTemplate, Jinja2PromptTemplate, or KernelFunctionFromPrompt)

    Raises:
        InputValidationError: If template loading fails
    """
    LOGGER.debug(f"🔧 Loading template from string - format: {template_format}")

    if template_format == "handlebars":
        from semantic_kernel.prompt_template import HandlebarsPromptTemplate, PromptTemplateConfig

        config = PromptTemplateConfig(
            template=template_content,
            template_format="handlebars",
        )
        return HandlebarsPromptTemplate(prompt_template_config=config)

    elif template_format == "jinja2":
        from semantic_kernel.prompt_template import Jinja2PromptTemplate, PromptTemplateConfig

        config = PromptTemplateConfig(
            template=template_content,
            template_format="jinja2",
        )
        return Jinja2PromptTemplate(prompt_template_config=config)

    elif template_format == "semantic-kernel":
        from semantic_kernel.functions.kernel_function_from_prompt import KernelFunctionFromPrompt

        # Use SK's YAML parser to create function from string
        return KernelFunctionFromPrompt.from_yaml(template_content)

    else:
        raise InputValidationError(f"Unsupported template format: {template_format}")


async def execute_llm_with_chat_history(
    service: Any,
    chat_history: list[dict[str, str]],
    schema_file: str | None = None,
    output_file: str | None = None,
) -> str | dict[str, Any]:
    """
    Execute LLM task with chat history.

    Creates kernel, executes LLM task with provided chat history,
    and handles response extraction. This provides the core LLM
    execution logic for traditional workflows.

    Args:
        service: LLM service instance (Azure/OpenAI)
        chat_history: List of message dictionaries
        schema_file: Optional schema file for response validation
        output_file: Optional output file path

    Returns:
        String response from LLM execution or structured dict if schema validation was used

    Raises:
        LLMRunnerError: If LLM execution fails
    """
    LOGGER.info("🚀 Starting LLM execution")

    # Create kernel for execution
    kernel = _create_kernel_with_service(service)

    result = await execute_llm_task(
        kernel,
        chat_history,
        schema_file,
        output_file,
    )

    # Extract response from result
    response: str | dict[str, Any]
    if isinstance(result, dict) and "output" in result:
        # Keep structured output as dict, convert text output to string
        if result.get("mode") == "structured":
            response = result["output"]
        else:
            response = str(result["output"])
    else:
        response = str(result)

    # Write output if specified
    _write_output_if_specified(output_file, response)

    return response


async def run_llm_task(
    # Template input (explicit for reliability)
    template_content: str | None = None,  # Python library primary
    template_file: str | None = None,  # CLI compatibility
    # Required format specification
    template_format: str | None = None,  # "handlebars", "jinja2", "semantic-kernel"
    # SMART auto-detection (99% reliable)
    template_vars: dict[str, Any] | str | None = None,  # Dict content OR file path
    schema: dict[str, Any] | str | Path | None = None,  # Dict content OR file path
    # Backward compatibility - separate file parameters
    template_vars_file: str | None = None,  # For explicit file-based template vars
    schema_file: str | None = None,  # For explicit schema file
    # Standard parameters
    output_file: str | None = None,
    log_level: str = "INFO",
    # Input file compatibility (internal use only)
    _input_file: str | None = None,
) -> str | dict[str, Any]:
    """
    Run LLM task with specified parameters.

    Main library function that provides programmatic access to LLM CI Runner
    functionality. Handles service setup, input processing, and execution
    coordination without CLI dependencies. Supports both file-based and
    direct string-based template input for enhanced Python integration.

    Args:
        input_file: Path to JSON input file (mutually exclusive with template_file/template_content)
        template_file: Path to template file (.hbs, .j2, .jinja, .yaml, .yml)
        template_vars_file: Optional template variables file (mutually exclusive with template_vars)
        schema_file: Optional schema file for response validation
        output_file: Optional output file path
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        template_content: Template content as string (mutually exclusive with template_file)
        template_format: Template format ("handlebars", "jinja2", "semantic-kernel") - required with template_content
        template_vars: Template variables as dict (mutually exclusive with template_vars_file)

    Returns:
        Response from LLM execution - string for text output or
        dictionary for structured JSON output

    Raises:
        InputValidationError: If parameters are invalid
        LLMRunnerError: If execution fails

    Examples:
        >>> # Simple input file processing
        >>> response = await run_llm_task(input_file="input.json")

        >>> # File-based template processing
        >>> response = await run_llm_task(
        ...     template_file="template.yaml",
        ...     template_vars_file="vars.yaml",
        ...     output_file="result.json"
        ... )

        >>> # String-based template processing
        >>> response = await run_llm_task(
        ...     template_content="Hello {{name}}!",
        ...     template_format="handlebars",
        ...     template_vars={"name": "World"},
        ...     output_file="result.txt"
        ... )

        >>> # SK YAML template with embedded schema
        >>> response = await run_llm_task(
        ...     template_content=\"\"\"
        ... template: "Analyze: {{input_text}}"
        ... input_variables:
        ...   - name: input_text
        ... execution_settings:
        ...   azure_openai:
        ...     temperature: 0.1
        ... \"\"\",
        ...     template_format="semantic-kernel",
        ...     template_vars={"input_text": "Sample data"}
        ... )
    """
    # Validate input parameters - unified API approach
    if not _input_file and not template_file and not template_content:
        raise InputValidationError("Either template_content, template_file, or input file must be specified")

    # Check mutually exclusive template inputs
    template_inputs = [_input_file, template_file, template_content]
    if sum(1 for x in template_inputs if x is not None) > 1:
        raise InputValidationError("Cannot specify multiple input sources")

    # Check mutually exclusive template_vars parameters
    if template_vars is not None and template_vars_file is not None:
        raise InputValidationError(
            "Cannot specify both template_vars and template_vars_file - they are mutually exclusive"
        )

    # Check mutually exclusive schema parameters
    if schema is not None and schema_file is not None:
        raise InputValidationError("Cannot specify both schema and schema_file - they are mutually exclusive")

    # Check template_format requirement for string templates
    if template_content and not template_format:
        raise InputValidationError("template_format is required when using templates")

    # Validate template_format values
    if template_format and template_format not in ["handlebars", "jinja2", "semantic-kernel"]:
        raise InputValidationError(
            f"Invalid template_format: {template_format}. Must be one of: handlebars, jinja2, semantic-kernel"
        )

    # Setup logging
    setup_logging(log_level)

    credential = None
    additional_credentials: list[Any] = []  # Track all credentials for proper cleanup
    try:
        # Setup LLM service (Azure or OpenAI)
        LOGGER.info("🔐 Setting up LLM service")
        service, credential = await setup_llm_service()

        # Smart auto-detection for schema (supports both dict and file path)
        schema_result = None
        if schema_file is not None:
            # Handle explicit schema_file parameter first
            LOGGER.debug(f"🔧 Loading schema_file: {schema_file}")
            schema_result = load_schema_file(Path(schema_file))
            LOGGER.debug(
                f"📋 Explicit schema_file loaded from: {schema_file}, result: {type(schema_result) if schema_result else 'None'}"
            )
        elif schema is not None:
            # Handle smart auto-detection schema parameter
            LOGGER.debug(f"🔧 Loading schema parameter: {type(schema)}")
            if isinstance(schema, dict):
                # Direct dict schema - convert to tuple format
                from llm_ci_runner.schema import create_dynamic_model_from_schema

                schema_model = create_dynamic_model_from_schema(schema)
                schema_result = (schema_model, schema)
                LOGGER.debug(f"📋 Dict schema loaded - model: {type(schema_model)}")
            elif isinstance(schema, str | Path):
                # File path schema - load from file (handle both str and Path)
                schema_result = load_schema_file(Path(schema))
                LOGGER.debug(f"📋 File schema loaded from: {schema}")

        # Log when no schema is provided
        if schema_result is None:
            LOGGER.debug("🔧 No schema or schema_file parameter provided")
            LOGGER.debug("📋 No schema loaded")

        # Smart auto-detection for template variables (supports both dict and file path)
        resolved_template_vars = {}
        # Handle explicit template_vars_file parameter first
        if template_vars_file is not None:
            resolved_template_vars = _load_template_variables(template_vars_file)
            LOGGER.debug(f"📋 Explicit template_vars_file loaded from: {template_vars_file}")
        elif template_vars is not None:
            if isinstance(template_vars, dict):
                # Direct dict variables
                resolved_template_vars = template_vars
                LOGGER.debug("📋 Dict template variables loaded")
            elif isinstance(template_vars, str):
                # File path variables - load from file
                resolved_template_vars = _load_template_variables(template_vars)
                LOGGER.debug(f"📋 File template variables loaded from: {template_vars}")

        # Initialize response variable with proper typing
        response: str | dict[str, Any]

        # Process input based on mode using unified approach
        if _input_file:
            # Traditional input file mode (CLI compatibility)
            chat_history = await process_input_file(_input_file)

            # Use execute_llm_task for proper schema enforcement
            if schema_result:
                # Create temporary schema file for execute_llm_task function
                import tempfile

                schema_model, schema_dict = schema_result
                with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp_file:
                    json.dump(schema_dict, tmp_file, indent=2)
                    schema_file_path = tmp_file.name

                # Create kernel for execution
                kernel = _create_kernel_with_service(service)

                # Use execute_llm_task for proper schema enforcement
                input_result = await execute_llm_task(kernel, chat_history, schema_file_path, output_file)

                # Clean up temporary file
                import os

                os.unlink(schema_file_path)

                # Extract response from result
                if isinstance(input_result, dict) and "output" in input_result:
                    # Keep structured output as dict, convert text output to string
                    if input_result.get("mode") == "structured":
                        response = input_result["output"]
                    else:
                        response = str(input_result["output"])
                else:
                    response = str(input_result)

                # 🔧 FIX: Write output file - this was missing!
                _write_output_if_specified(output_file, response)
            else:
                # No schema - use direct schema file path if available (string format)
                input_schema_file_path: str | None = schema if isinstance(schema, str) else None
                response = await execute_llm_with_chat_history(
                    service, chat_history, input_schema_file_path, output_file
                )

        elif template_file:
            # File-based template mode with unified processing
            LOGGER.info("📄 Processing template file")
            template = load_template(Path(template_file))
            response = await _process_template_unified(
                template,
                template_format or _detect_template_format(template_file),
                resolved_template_vars,
                service,
                schema_result,
                output_file,
                additional_credentials,
            )

        elif template_content:
            # String-based template mode with unified processing
            LOGGER.info("📄 Processing template content")
            if template_format is None:
                raise ValueError("template_format must be specified when using template_content")

            template = await load_template_from_string(template_content, template_format)
            response = await _process_template_unified(
                template,
                template_format,
                resolved_template_vars,
                service,
                schema_result,
                output_file,
                additional_credentials,
            )

        else:
            # This should never happen due to validation above
            raise InputValidationError("No input method specified")

        return response

    finally:
        # Properly close Azure credential to prevent unclosed client session warnings
        if credential is not None:
            try:
                await credential.close()
                LOGGER.debug("🔒 Azure credential closed successfully")
            except Exception as e:
                LOGGER.debug(f"Warning: Failed to close Azure credential: {e}")
                # Don't raise - this is cleanup, not critical

        # Close any additional credentials created during template processing
        for i, cred in enumerate(additional_credentials):
            if cred is not None:
                try:
                    await cred.close()
                    LOGGER.debug(f"🔒 Additional Azure credential {i + 1} closed successfully")
                except Exception as e:
                    LOGGER.debug(f"Warning: Failed to close additional Azure credential {i + 1}: {e}")
                    # Don't raise - this is cleanup, not critical


async def main() -> None:
    """
    Main CLI function for LLM CI Runner.

    Provides CLI interface with proper error handling and user feedback.
    Orchestrates the workflow by parsing arguments and delegating to
    appropriate library functions.

    Raises:
        SystemExit: On any error with appropriate exit code
    """
    try:
        # Parse arguments
        args = parse_arguments()

        # Display startup banner
        CONSOLE.print(
            Panel.fit(
                "[bold blue]LLM CI Runner[/bold blue]\n[dim]AI-powered automation for pipelines[/dim]",
                border_style="blue",
            )
        )

        # Execute using library function with unified API
        response = await run_llm_task(
            _input_file=str(args.input_file) if args.input_file else None,  # Convert Path to string
            template_file=str(args.template_file) if args.template_file else None,  # Convert Path to string
            template_vars=str(args.template_vars) if args.template_vars else None,  # Convert Path to string
            schema=str(args.schema_file) if args.schema_file else None,  # Convert Path to string
            output_file=str(args.output_file) if args.output_file else None,
            log_level=args.log_level,
        )

        # Success message
        CONSOLE.print(
            Panel.fit(
                f"[bold green]✅ Success![/bold green]\n"
                f"Response length: {len(str(response))} characters\n"
                f"Output written to: [bold]{args.output_file or 'console'}[/bold]",
                border_style="green",
            )
        )

    except KeyboardInterrupt:
        LOGGER.info("⏹️  Interrupted by user")
        sys.exit(130)
    except LLMRunnerError as e:
        LOGGER.error(f"❌ LLM Runner error: {e}")
        CONSOLE.print(
            Panel.fit(
                f"[bold red]Error[/bold red]\n{str(e)}",
                border_style="red",
            )
        )
        sys.exit(1)
    except Exception as e:
        LOGGER.error(f"❌ Unexpected error: {e}")
        CONSOLE.print(
            Panel.fit(
                f"[bold red]Unexpected Error[/bold red]\n{str(e)}",
                border_style="red",
            )
        )
        sys.exit(1)


def cli_main() -> None:
    """
    CLI entry point for LLM CI Runner.

    This function serves as the main entry point for the command-line interface.
    It runs the async main function in an event loop.
    """
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
