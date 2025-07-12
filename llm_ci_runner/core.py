"""
Core execution logic for LLM CI Runner.

This module provides the main orchestration logic that ties together
all the components: input loading, template processing, LLM execution,
and output writing.
"""

import asyncio
import logging
import sys

from rich.panel import Panel
from rich.traceback import install as install_rich_traceback

from .exceptions import (
    InputValidationError,
    LLMRunnerError,
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


async def main() -> None:
    """
    Main execution function for LLM CI Runner.

    Orchestrates the entire workflow:
    1. Parse command line arguments
    2. Setup logging
    3. Load input data or templates
    4. Setup LLM service (Azure or OpenAI)
    5. Execute LLM task
    6. Write output

    Raises:
        SystemExit: On any error with appropriate exit code
    """
    try:
        # Parse arguments
        args = parse_arguments()

        # Setup logging
        setup_logging(args.log_level)

        # Display startup banner
        CONSOLE.print(
            Panel.fit(
                "[bold blue]LLM CI Runner[/bold blue]\n[dim]AI-powered automation for pipelines[/dim]",
                border_style="blue",
            )
        )

        # Setup LLM service (Azure or OpenAI)
        LOGGER.info("🔐 Setting up LLM service")
        service, credential = await setup_llm_service()

        # Load schema if provided
        schema_model = load_schema_file(args.schema_file)

        # Process input based on mode
        if args.input_file:
            # Traditional input file mode
            LOGGER.info("📂 Processing input file mode")

            # Load input data
            input_data = load_input_file(args.input_file)
            messages = input_data["messages"]
            context = input_data.get("context")

            # Create chat history
            chat_history = create_chat_history(messages)

        elif args.template_file:
            # Template-based mode
            LOGGER.info("📄 Processing template mode")

            # Load template
            template = load_template(args.template_file)

            # Load template variables (optional)
            template_vars = {}
            if args.template_vars:
                template_vars = load_template_vars(args.template_vars)
            else:
                LOGGER.info("📝 No template variables provided - using static template")

            # Create kernel for template rendering
            from semantic_kernel import Kernel

            kernel = Kernel()

            # Render template
            rendered_content = await render_template(template, template_vars, kernel)

            # Parse rendered content to chat history
            chat_history = parse_rendered_template_to_chat_history(rendered_content)

            # No context in template mode
            context = None

        else:
            # This should never happen due to argument validation
            raise InputValidationError("No input method specified")

        # Execute LLM task
        LOGGER.info("🚀 Starting LLM execution")
        response = await execute_llm_task(service, chat_history, context, schema_model)

        # Write output
        LOGGER.info("📝 Writing output")
        write_output_file(args.output_file, response)

        # Success message
        CONSOLE.print(
            Panel.fit(
                f"[bold green]✅ Success![/bold green]\nOutput written to: [bold]{args.output_file}[/bold]",
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
