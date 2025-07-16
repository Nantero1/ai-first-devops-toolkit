"""
Unified output formatting for LLM CI Runner.

This module provides centralized formatting functionality for both console display and file output,
eliminating duplication between llm_execution.py and io_operations.py while maintaining separation of concerns.
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from ruamel.yaml import YAML

from .exceptions import LLMRunnerError
from .logging_config import LOGGER

# Rich console instance for display operations
CONSOLE = Console()

# YAML literal formatting threshold - strings longer than this will use DoubleQuotedScalarString
YAML_LITERAL_LENGTH_THRESHOLD = 80


@dataclass
class FormattedOutput:
    """Formatted output data with type-safe interface.

    Encapsulates all necessary data for both console display and file writing
    while maintaining clean separation of concerns.

    Attributes:
        content: Formatted content string (JSON/YAML)
        format_type: Content format ('json', 'yaml', 'text', 'markdown')
        display_title: Rich panel title for console display
        raw_data: Original unformatted data for metadata wrapper
    """

    content: str
    format_type: str
    display_title: str
    raw_data: str | dict[str, Any]


def detect_output_format(output_file: Path | None) -> str:
    """Detect output format from file extension using KISS deterministic approach.

    We know the format from user input, so no complex detection needed.

    Args:
        output_file: Optional path to output file

    Returns:
        Format string: 'yaml', 'json', 'text', or 'markdown'
    """
    if not output_file:
        return "text"

    suffix = Path(output_file).suffix.lower()
    if suffix in [".yaml", ".yml"]:
        return "yaml"
    elif suffix == ".json":
        return "json"
    elif suffix == ".md":
        return "markdown"
    else:
        return "text"


def format_output_content(data: str | dict[str, Any], format_type: str, mode: str = "structured") -> FormattedOutput:
    """Format output content for both console and file display.

    Core formatting logic that handles JSON/YAML conversion with consistent configuration
    across both console display and file writing operations.

    Args:
        data: Raw data to format (string or dictionary)
        format_type: Target format ('json', 'yaml', 'text', 'markdown')
        mode: Output mode ('structured' or 'text')

    Returns:
        FormattedOutput with formatted content and metadata
    """
    # Handle structured data formatting
    if isinstance(data, dict) and mode == "structured":
        if format_type == "yaml":
            # Generate YAML content with consistent configuration
            yaml = YAML()
            yaml.indent(mapping=2, sequence=4, offset=2)
            yaml.default_flow_style = False
            yaml.width = 1000

            yaml_output = StringIO()
            output_data_literal = yaml_recursively_force_literal(copy.deepcopy(data))
            yaml.dump(output_data_literal, yaml_output)
            yaml_content = yaml_output.getvalue()

            return FormattedOutput(
                content=yaml_content, format_type="yaml", display_title="📋 Structured Output (YAML)", raw_data=data
            )
        else:  # Default to JSON
            json_content = json.dumps(data, indent=2, ensure_ascii=False)
            return FormattedOutput(
                content=json_content, format_type="json", display_title="📋 Structured Output (JSON)", raw_data=data
            )

    # Handle text content
    content_str = str(data)

    # Determine display title based on format and mode
    if format_type == "markdown":
        display_title = "📄 Markdown Output"
    elif mode == "text":
        display_title = "📝 Text Output"
    else:
        display_title = "📝 Text Output"

    return FormattedOutput(content=content_str, format_type=format_type, display_title=display_title, raw_data=data)


def display_formatted_console(formatted_output: FormattedOutput) -> None:
    """Display formatted output to console with Rich formatting.

    Preserves existing Rich console formatting including panels, syntax highlighting,
    and proper styling for optimal user experience.

    Args:
        formatted_output: FormattedOutput containing content and metadata
    """
    # Determine console display style based on mode
    if formatted_output.display_title.startswith("📋"):
        # Structured output styling
        CONSOLE.print("\n[bold cyan]🤖 LLM Response (Structured)[/bold cyan]")
        style = "cyan"
    else:
        # Text output styling
        CONSOLE.print("\n[bold green]🤖 LLM Response (Text)[/bold green]")
        style = "green"

    # Apply syntax highlighting based on format type
    highlighted_content = _apply_syntax_highlighting(formatted_output.content, formatted_output.format_type)

    # Display with Rich panel
    CONSOLE.print(
        Panel(
            highlighted_content,
            title=formatted_output.display_title,
            style=style,
        )
    )


def write_formatted_file(formatted_output: FormattedOutput, output_file: Path) -> None:
    """Write formatted output to file with metadata wrapper.

    Maintains existing file writing behavior including metadata wrapper
    and format-specific handling for different file types.

    Args:
        formatted_output: FormattedOutput containing content and metadata
        output_file: Path to output file

    Raises:
        LLMRunnerError: If file writing fails
    """
    LOGGER.debug(f"📝 Writing output to: {output_file}")

    try:
        # Create parent directories if they don't exist
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Determine output format based on extension
        extension = output_file.suffix.lower()

        if extension == ".md":
            # Write direct text for markdown files (no JSON wrapper)
            if isinstance(formatted_output.raw_data, str):
                content = formatted_output.raw_data
            else:
                # If raw_data is dict, extract the text content
                content = formatted_output.raw_data.get("response", str(formatted_output.raw_data))

            with open(output_file, "w", encoding="utf-8") as f:
                f.write(content)

            LOGGER.info(f"✅ Wrote direct text output: {output_file}")

        elif extension in [".yaml", ".yml"]:
            # Wrap response in standard format for YAML
            output_data = {
                "success": True,
                "response": formatted_output.raw_data,
                "metadata": {
                    "runner": "llm-ci-runner",
                    "timestamp": datetime.now().isoformat(),
                },
            }

            output_data_literal = yaml_recursively_force_literal(output_data)
            yaml = YAML(pure=True)
            yaml.default_flow_style = False
            yaml.width = 1000
            yaml.indent(mapping=2, sequence=4, offset=2)

            with open(output_file, "w", encoding="utf-8") as f:
                yaml.dump(output_data_literal, f)

            LOGGER.info(f"✅ Wrote YAML output: {output_file}")

        else:
            # Wrap response in standard format for JSON (default)
            output_data = {
                "success": True,
                "response": formatted_output.raw_data,
                "metadata": {
                    "runner": "llm-ci-runner",
                    "timestamp": datetime.now().isoformat(),
                },
            }

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)

            LOGGER.info(f"✅ Wrote JSON output: {output_file}")

    except Exception as e:
        raise LLMRunnerError(f"Error writing output file: {e}") from e


def _apply_syntax_highlighting(response: str, format_type: str) -> str | Syntax | Markdown:
    """Apply Rich syntax highlighting for known content format.

    KISS approach: No detection needed - we already know the format deterministically.

    Args:
        response: Raw text response
        format_type: Known format ("json", "yaml", "markdown", "text")

    Returns:
        Either the original string (for plain text), a Rich Syntax object (for JSON/YAML),
        or a Rich Markdown object (for markdown) with appropriate formatting
    """
    if not response or not response.strip():
        return response

    if format_type == "json":
        try:
            # Format JSON for better display
            parsed = json.loads(response)
            formatted_json = json.dumps(parsed, indent=2, ensure_ascii=False)
            return Syntax(formatted_json, "json", word_wrap=True)
        except json.JSONDecodeError:
            # If JSON parsing fails, fall back to plain text
            return response
    elif format_type == "yaml":
        # Apply YAML syntax highlighting
        return Syntax(response, "yaml", word_wrap=True)
    elif format_type == "markdown":
        # Use Rich's Markdown class for proper markdown rendering with formatting
        return Markdown(response)
    else:  # format_type == "text" or any other value
        return response


def yaml_recursively_force_literal(data: Any) -> Any:
    """Recursively convert data to use appropriate YAML scalar styles.

    This ensures that multi-line strings and long strings are formatted appropriately
    in YAML output. Strings are formatted as:
    - Literal scalars (|-) for strings containing newlines
    - Double-quoted scalars for long single-line strings (>80 chars)
    - Plain scalars for short strings

    Args:
        data: Data to convert

    Returns:
        Data with appropriate YAML scalar styles applied
    """
    from ruamel.yaml import scalarstring

    if isinstance(data, dict):
        return {k: yaml_recursively_force_literal(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [yaml_recursively_force_literal(item) for item in data]
    elif isinstance(data, str):
        # Use literal scalars only for truly multiline content
        if "\n" in data:
            return scalarstring.LiteralScalarString(data)
        # Use double-quoted scalars for long single-line strings to prevent wrapping
        elif len(data) > YAML_LITERAL_LENGTH_THRESHOLD:
            return scalarstring.DoubleQuotedScalarString(data)
        return data
    else:
        return data
