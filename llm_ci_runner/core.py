"""
Core execution logic for LLM CI Runner.

This module provides the main orchestration logic that ties together
all the components: input loading, template processing, LLM execution,
and output writing. Functions are designed to be used both as CLI
commands and as library methods for programmatic access.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any

from rich.panel import Panel
from rich.traceback import install as install_rich_traceback
from semantic_kernel import Kernel
from semantic_kernel.contents import ChatHistory
from semantic_kernel.functions import KernelArguments
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


async def process_sk_yaml_template(
    template: KernelFunctionFromPrompt,
    service: Any,
    template_vars_file: str | None = None,
    output_file: str | None = None,
) -> str | dict[str, Any]:
    """
    Process SK YAML template through direct kernel execution.

    PURPOSE: Executes self-contained Semantic Kernel YAML templates that include
    embedded prompt template, input variables, execution settings, and optional
    schema definitions. Uses SK's native kernel.invoke() for complete template
    lifecycle management including schema validation and structured output.

    Args:
        template: Loaded SK YAML template function
        service: Configured LLM service (Azure/OpenAI)
        template_vars_file: Optional external template variables file
        output_file: Optional output file path for writing results

    Returns:
        Response from template execution - either string for text output
        or dictionary for structured JSON output

    Raises:
        LLMRunnerError: If template execution fails
    """
    LOGGER.info("📋 Using Semantic Kernel YAML template")

    # Create kernel with service
    kernel = _create_kernel_with_service(service)

    # Prepare arguments - merge template vars with SK input variables
    sk_arguments = KernelArguments()
    template_vars = _load_template_variables(template_vars_file)
    sk_arguments.update(template_vars)

    # SK handles EVERYTHING: template rendering, chat history, schema validation, LLM execution
    LOGGER.info("🚀 Executing SK YAML template")

    # Debug: Pre-invoke service validation
    LOGGER.debug(f"🔍 Template execution settings: {getattr(template, 'prompt_execution_settings', 'NO_SETTINGS')}")
    LOGGER.debug(f"🔍 Available kernel services: {kernel.services}")
    LOGGER.debug(f"🔍 Template name: {getattr(template, 'name', 'NO_NAME')}")
    LOGGER.debug(f"🔍 SK Arguments: {dict(sk_arguments)}")

    try:
        result = await kernel.invoke(template, sk_arguments)
        LOGGER.debug("✅ SK template execution successful")
    except Exception as e:
        LOGGER.error(f"🚨 SK invoke failed: {e}")
        LOGGER.error(f"🚨 Error type: {type(e).__name__}")
        LOGGER.error(f"🚨 Template: {getattr(template, 'name', 'UNKNOWN')}")
        LOGGER.error(
            f"🚨 Available services: {[s.service_id for s in kernel.services.values() if hasattr(s, 'service_id')]}"
        )
        if hasattr(template, "prompt_execution_settings"):
            LOGGER.error(f"🚨 Template execution settings: {template.prompt_execution_settings}")
        raise

    # Extract content (SK returns FunctionResult with value list of ChatMessageContent)
    response: str | dict[str, Any]
    if result is not None and hasattr(result, "value") and result.value:
        # Get the first ChatMessageContent from the value list
        chat_content = result.value[0]
        if hasattr(chat_content, "content"):
            content = str(chat_content.content)

            # Check if template requires JSON output by examining execution settings
            requires_json = _template_requires_json_output(template)

            # Parse JSON based on template requirements
            try:
                import json

                response = json.loads(content)
                LOGGER.debug("✅ Parsed structured JSON response from SK template")
            except (json.JSONDecodeError, ValueError) as e:
                if requires_json:
                    # Template explicitly requires JSON - this is an error that should trigger retry
                    raise SchemaValidationError(
                        f"SK template requires JSON output but received invalid JSON: {str(e)}. "
                        f"Content: {content[:200]}..."
                    ) from e
                else:
                    # Template allows text output - fallback to string is acceptable
                    response = content
                    LOGGER.debug("📝 Keeping text response from SK template (JSON not required)")
        else:
            response = str(chat_content)
    elif result is not None and hasattr(result, "content"):
        # Fallback for direct content access
        content = str(result.content)

        # Check if template requires JSON output
        requires_json = _template_requires_json_output(template)

        # Parse JSON based on template requirements
        try:
            import json

            response = json.loads(content)
            LOGGER.debug("✅ Parsed structured JSON response from SK template")
        except (json.JSONDecodeError, ValueError) as e:
            if requires_json:
                # Template explicitly requires JSON - this is an error that should trigger retry
                raise SchemaValidationError(
                    f"SK template requires JSON output but received invalid JSON: {str(e)}. Content: {content[:200]}..."
                ) from e
            else:
                # Template allows text output - fallback to string is acceptable
                response = content
                LOGGER.debug("📝 Keeping text response from SK template (JSON not required)")
    else:
        response = str(result) if result is not None else ""

    # Write output if specified (write_output_file handles both str and dict)
    _write_output_if_specified(output_file, response)

    return response


def _load_template_variables(template_vars_file: str | None) -> dict[str, Any]:
    """Load template variables from file or return empty dict."""
    if template_vars_file:
        return load_template_vars(Path(template_vars_file))
    else:
        LOGGER.info("📝 No template variables provided - using defaults")
        return {}


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


async def process_sk_yaml_template_with_vars(
    template: KernelFunctionFromPrompt,
    service: Any,
    template_vars: dict[str, Any] | None = None,
    output_file: str | None = None,
) -> str | dict[str, Any]:
    """
    Process SK YAML template with dict-based template variables.

    Enhanced version of process_sk_yaml_template that accepts template variables
    as a Python dict rather than requiring a file.
    """
    LOGGER.info("📋 Using Semantic Kernel YAML template with dict vars")

    # Create kernel with service
    kernel = _create_kernel_with_service(service)

    # Prepare arguments from dict
    sk_arguments = KernelArguments()
    if template_vars:
        sk_arguments.update(template_vars)
        LOGGER.debug(f"🔧 Using template variables: {list(template_vars.keys())}")
    else:
        LOGGER.debug("🔧 No template variables provided")

    # Execute template
    LOGGER.info("🚀 Executing SK YAML template")

    try:
        result = await kernel.invoke(template, sk_arguments)
        LOGGER.debug("✅ SK template execution successful")
    except Exception as e:
        LOGGER.error(f"🚨 SK invoke failed: {e}")
        raise

    # Extract and process response (same logic as original function)
    response: str | dict[str, Any]
    if result is not None and hasattr(result, "value") and result.value:
        # Get the first ChatMessageContent from the value list
        chat_content = result.value[0]
        if hasattr(chat_content, "content"):
            content = str(chat_content.content)

            # Check if template requires JSON output by examining execution settings
            requires_json = _template_requires_json_output(template)

            # Parse JSON based on template requirements
            try:
                import json

                response = json.loads(content)
                LOGGER.debug("✅ Parsed structured JSON response from SK template")
            except (json.JSONDecodeError, ValueError) as e:
                if requires_json:
                    raise SchemaValidationError(
                        f"SK template requires JSON output but received invalid JSON: {str(e)}. "
                        f"Content: {content[:200]}..."
                    ) from e
                else:
                    response = content
                    LOGGER.debug("📝 Keeping text response from SK template (JSON not required)")
        else:
            response = str(chat_content)
    else:
        response = str(result) if result is not None else ""

    # Write output if specified
    _write_output_if_specified(output_file, response)

    return response


async def process_handlebars_jinja_template_with_vars(
    template: Any,
    template_vars: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    """
    Process Handlebars or Jinja2 template with dict-based template variables.

    Enhanced version of process_handlebars_jinja_template that accepts template variables
    as a Python dict rather than requiring a file.
    """
    LOGGER.info("🎨 Processing Handlebars/Jinja2 template with dict vars")

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
    return _convert_chat_history_to_list(chat_history)


async def process_handlebars_jinja_template(
    template: Any,
    template_vars_file: str | None = None,
) -> list[dict[str, str]]:
    """
    Process Handlebars or Jinja2 template.

    Handles template variable loading, rendering, and chat history conversion
    for Handlebars (.hbs) and Jinja2 (.j2, .jinja) templates.

    Args:
        template: Loaded template object (Handlebars/Jinja2)
        template_vars_file: Optional template variables file path

    Returns:
        List of message dictionaries in chat history format

    Raises:
        LLMRunnerError: If template processing fails
    """
    LOGGER.info("🎨 Processing Handlebars/Jinja2 template")

    # Load template variables
    template_vars = _load_template_variables(template_vars_file)

    # Create kernel for template rendering
    kernel = Kernel()

    # Render template
    rendered_content = await render_template(template, template_vars, kernel)

    # Parse rendered content to chat history
    chat_history = parse_rendered_template_to_chat_history(rendered_content)

    # Convert to list format
    return _convert_chat_history_to_list(chat_history)


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
    input_file: str | None = None,
    template_file: str | None = None,
    template_vars_file: str | None = None,
    schema_file: str | None = None,
    output_file: str | None = None,
    log_level: str = "INFO",
    # NEW: String-based parameters for direct Python usage
    template_content: str | None = None,
    template_format: str | None = None,  # "handlebars", "jinja2", "semantic-kernel"
    template_vars: dict[str, Any] | None = None,
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
    # Validate input parameters - enhanced for string-based templates
    if not input_file and not template_file and not template_content:
        raise InputValidationError("Either input_file, template_file, or template_content must be specified")

    # Check mutually exclusive template inputs
    template_inputs = [input_file, template_file, template_content]
    if sum(1 for x in template_inputs if x is not None) > 1:
        raise InputValidationError(
            "Cannot specify multiple template inputs: input_file, template_file, and template_content are mutually exclusive"
        )

    # Check template_format requirement for string templates
    if template_content and not template_format:
        raise InputValidationError("template_format is required when using template_content")

    # Check mutually exclusive template variables
    if template_vars_file and template_vars:
        raise InputValidationError("Cannot specify both template_vars_file and template_vars")

    # Validate template_format values
    if template_format and template_format not in ["handlebars", "jinja2", "semantic-kernel"]:
        raise InputValidationError(
            f"Invalid template_format: {template_format}. Must be one of: handlebars, jinja2, semantic-kernel"
        )

    # Setup logging
    setup_logging(log_level)

    credential = None
    try:
        # Setup LLM service (Azure or OpenAI)
        LOGGER.info("🔐 Setting up LLM service")
        service, credential = await setup_llm_service()

        # Load schema if provided
        schema_result = load_schema_file(Path(schema_file) if schema_file else None)
        if schema_result:
            schema_model, schema_dict = schema_result
            LOGGER.debug(f"📋 Schema loaded - model: {type(schema_model)}, dict: {type(schema_dict)}")
        else:
            LOGGER.debug("📋 No schema loaded")

        # Initialize response variable with proper typing
        response: str | dict[str, Any]

        # Process input based on mode
        if input_file:
            # Traditional input file mode
            chat_history = await process_input_file(input_file)
            response = await execute_llm_with_chat_history(service, chat_history, schema_file, output_file)

        elif template_file:
            # File-based template mode
            LOGGER.info("📄 Processing template file")

            # Load template from file
            template = load_template(Path(template_file))

            # Handle different template types
            if isinstance(template, KernelFunctionFromPrompt):
                # SK YAML template - self-contained execution
                response = await process_sk_yaml_template(template, service, template_vars_file, output_file)
            else:
                # Handlebars/Jinja2 template workflow
                chat_history = await process_handlebars_jinja_template(template, template_vars_file)
                response = await execute_llm_with_chat_history(service, chat_history, schema_file, output_file)

        elif template_content:
            # String-based template mode
            LOGGER.info("📄 Processing template content")

            # Validate template_format is provided
            if template_format is None:
                raise ValueError("template_format must be specified when using template_content")

            # Load template from string content
            template = await load_template_from_string(template_content, template_format)

            # Handle different template types
            if isinstance(template, KernelFunctionFromPrompt):
                # SK YAML template - self-contained execution
                response = await process_sk_yaml_template_with_vars(template, service, template_vars, output_file)
            else:
                # Handlebars/Jinja2 template workflow
                chat_history = await process_handlebars_jinja_template_with_vars(template, template_vars)
                response = await execute_llm_with_chat_history(service, chat_history, schema_file, output_file)
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

        # Execute using library function
        response = await run_llm_task(
            input_file=args.input_file,
            template_file=args.template_file,
            template_vars_file=args.template_vars,
            schema_file=args.schema_file,
            output_file=args.output_file,
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
