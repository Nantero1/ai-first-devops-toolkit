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

    # Get logger for this module
    logger = logging.getLogger("llm_ci_runner")
    logger.info(f"🚀 LLM CI Runner initialized with log level: {log_level.upper()}")

    return logger
