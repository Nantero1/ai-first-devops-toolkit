"""
Logging configuration for LLM CI Runner.

This module provides centralized logging setup with Rich formatting
for beautiful console output and proper log level management.
"""

import logging

from rich.console import Console
from rich.logging import RichHandler

# Global CONSOLE for rich output
CONSOLE = Console()

# Global LOGGER for testing compatibility
LOGGER = logging.getLogger("llm_ci_runner")


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

    # Get logger for this module
    logger = logging.getLogger("llm_ci_runner")
    logger.info(f"[bold green]🚀 LLM Runner initialized with log level: {log_level.upper()}[/bold green]")

    return logger
