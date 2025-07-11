"""
Input/Output operations for LLM CI Runner.

This module provides functionality for loading input files, writing output files,
and parsing command line arguments with proper error handling.
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML, YAMLError
from semantic_kernel.contents import ChatHistory, ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole

from .exceptions import InputValidationError, LLMRunnerError
from .logging_config import LOGGER


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments with comprehensive validation.

    Supports both traditional input file mode and template-based mode.
    Template variables are optional when using template files.

    Returns:
        Parsed arguments namespace

    Raises:
        SystemExit: If arguments are invalid or help is requested
    """
    parser = argparse.ArgumentParser(
        prog="llm-ci-runner",
        description="LLM CI Runner - AI-powered automation for pipelines",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Traditional input file mode
  llm-ci-runner --input-file input.json --schema-file schema.json --output-file result.json

  # Template-based mode with variables
  llm-ci-runner --template-file template.hbs --template-vars vars.yaml --schema-file schema.yaml

  # Template-based mode without variables (static template)
  llm-ci-runner --template-file template.hbs --schema-file schema.yaml

  # YAML input files
  llm-ci-runner --input-file config.yaml --schema-file schema.yaml --output-file result.yaml

Environment Variables:
    AZURE_OPENAI_ENDPOINT    Azure OpenAI endpoint URL
    AZURE_OPENAI_MODEL       Model deployment name
    AZURE_OPENAI_API_VERSION API version (default: 2024-12-01-preview)
    AZURE_OPENAI_API_KEY     API key (optional, uses RBAC if not provided)
        """,
    )

    # Input method group (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--input-file",
        type=Path,
        help="Input JSON/YAML file with messages and context",
    )
    input_group.add_argument(
        "--template-file",
        type=Path,
        help="Template file (.hbs, .handlebars, .jinja, .j2, .jinja2)",
    )

    # Template variables (optional when using template-file)
    parser.add_argument(
        "--template-vars",
        type=Path,
        help="Template variables file (JSON/YAML) - optional when using --template-file",
    )

    # Output and schema
    parser.add_argument(
        "--schema-file",
        type=Path,
        help="JSON/YAML schema file for structured output validation",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=Path("result.json"),
        help="Output file path (default: result.json)",
    )

    # Logging
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)",
    )

    args = parser.parse_args()

    # Validate template usage
    if args.template_file and args.input_file:
        parser.error("Cannot use both --template-file and --input-file")

    # Template variables are optional when using template files
    # File existence will be checked when the template is actually loaded

    return args


def load_input_file(input_file: Path) -> dict[str, Any]:
    """
    Load input data from JSON or YAML file.

    Supports both JSON and YAML formats with automatic detection.
    Validates required structure and provides detailed error messages.

    Args:
        input_file: Path to the input file

    Returns:
        Dictionary containing messages and optional context

    Raises:
        InputValidationError: If file cannot be loaded or is invalid
    """
    LOGGER.debug(f"📂 Loading input file: {input_file}")

    if not input_file.exists():
        raise InputValidationError(f"Input file not found: {input_file}")

    try:
        yaml = YAML(typ="safe")

        with open(input_file, encoding="utf-8") as f:
            content = f.read()

        # Determine format based on file extension
        extension = input_file.suffix.lower()

        if extension in [".yaml", ".yml"]:
            # Try YAML first, fallback to JSON
            try:
                data = yaml.load(content)
            except YAMLError as e:
                # For .yaml/.yml files, don't fallback to JSON - fail immediately
                raise InputValidationError(f"Invalid YAML in input file: {e}") from e
        else:
            # Try JSON first, fallback to YAML
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                # For .json files, don't fallback to YAML - fail immediately
                if extension == ".json":
                    raise InputValidationError(f"Invalid JSON in input file: {e}") from e
                # For other files, try YAML fallback
                try:
                    data = yaml.load(content)
                except YAMLError as e:
                    raise InputValidationError(f"Invalid YAML in input file: {e}") from e

        if not isinstance(data, dict):
            raise InputValidationError("Input file must contain a dictionary")

        # Validate required structure
        if "messages" not in data:
            raise InputValidationError("Input file must contain 'messages' field")

        messages = data["messages"]
        if not isinstance(messages, list):
            raise InputValidationError("'messages' must be a non-empty array")

        if not messages:
            raise InputValidationError("'messages' must be a non-empty array")

        # Validate each message
        for i, message in enumerate(messages):
            if not isinstance(message, dict):
                raise InputValidationError(f"Message {i} must be a dictionary")

            if "role" not in message:
                raise InputValidationError(f"Message {i} must have 'role' field")

            if "content" not in message:
                raise InputValidationError(f"Message {i} must have 'content' field")

            role = message["role"]
            if role not in ["system", "user", "assistant"]:
                raise InputValidationError(
                    f"Message {i} has invalid role '{role}'. Valid roles: system, user, assistant"
                )

        LOGGER.info(f"✅ Loaded input file with {len(messages)} messages")

        # Log context if present
        if "context" in data:
            context = data["context"]
            LOGGER.debug(f"   Context keys: {list(context.keys()) if isinstance(context, dict) else 'non-dict'}")

        return data

    except OSError as e:
        raise InputValidationError(f"Error reading input file: {e}") from e
    except Exception as e:
        # Re-raise InputValidationError as-is
        if isinstance(e, InputValidationError):
            raise
        raise InputValidationError(f"Failed to load input file: {e}") from e


def create_chat_history(messages: list[dict[str, Any]]) -> ChatHistory:
    """
    Create ChatHistory from message list.

    Converts message dictionaries to ChatMessageContent objects
    with proper role mapping and validation.

    Args:
        messages: List of message dictionaries

    Returns:
        ChatHistory with all messages

    Raises:
        InputValidationError: If message structure is invalid
    """
    LOGGER.debug(f"💬 Creating ChatHistory from {len(messages)} messages")

    chat_history = ChatHistory()

    for i, message in enumerate(messages):
        # Validate required fields
        if "role" not in message or "content" not in message:
            raise InputValidationError(f"Message {i} missing required 'role' or 'content' field")

        role_str = message["role"]
        content = message["content"]
        name = message.get("name")  # Optional name field

        # Map role strings to AuthorRole enum
        role_mapping = {
            "system": AuthorRole.SYSTEM,
            "user": AuthorRole.USER,
            "assistant": AuthorRole.ASSISTANT,
        }

        if role_str not in role_mapping:
            raise InputValidationError(f"Invalid message role: {role_str}")

        role = role_mapping[role_str]

        try:
            # Create chat message content
            chat_message = ChatMessageContent(role=role, content=content)

            # Add name if provided
            if name:
                chat_message.name = name

            chat_history.add_message(chat_message)

            LOGGER.debug(f"   Added {role_str} message: {len(content)} characters")

        except Exception as e:
            raise InputValidationError(f"Failed to create message {i}: {e}") from e

    LOGGER.info(f"✅ Created ChatHistory with {len(messages)} messages")
    return chat_history


def write_output_file(output_file: Path, response: str | dict[str, Any]) -> None:
    """
    Write response to output file in JSON or YAML format.

    Automatically detects output format based on file extension.
    Creates parent directories if they don't exist.
    Wraps response in standard format with success and metadata.

    Args:
        output_file: Path to the output file
        response: Response data to write

    Raises:
        InputValidationError: If writing fails
    """
    LOGGER.debug(f"📝 Writing output to: {output_file}")

    try:
        # Create parent directories if they don't exist
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Wrap response in standard format
        output_data = {
            "success": True,
            "response": response,
            "metadata": {
                "runner": "llm_ci_runner.py",
                "timestamp": datetime.now().isoformat(),
            },
        }

        # Determine output format based on extension
        extension = output_file.suffix.lower()

        if extension in [".yaml", ".yml"]:
            # Write as YAML
            yaml = YAML()
            yaml.default_flow_style = False
            yaml.indent(mapping=2, sequence=4, offset=2)

            with open(output_file, "w", encoding="utf-8") as f:
                yaml.dump(output_data, f)

            LOGGER.info(f"✅ Wrote YAML output: {output_file}")

        else:
            # Write as JSON (default)
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)

            LOGGER.info(f"✅ Wrote JSON output: {output_file}")

    except Exception as e:
        raise LLMRunnerError(f"Error writing output file: {e}") from e


def load_schema_file(schema_file: Path | None) -> type | None:
    """
    Load schema file and create dynamic model.

    Args:
        schema_file: Path to the schema file (optional)

    Returns:
        Dynamic model class or None if no schema provided

    Raises:
        InputValidationError: If schema loading fails
    """
    if schema_file is None:
        LOGGER.debug("📋 No schema file provided - using text output mode")
        return None

    LOGGER.debug(f"📋 Loading schema file: {schema_file}")

    if not schema_file.exists():
        raise InputValidationError(f"Schema file not found: {schema_file}")

    try:
        yaml = YAML(typ="safe")

        with open(schema_file, encoding="utf-8") as f:
            content = f.read()

        # Try YAML first, fallback to JSON
        try:
            schema_dict = yaml.load(content)
        except YAMLError:
            # Fallback to JSON
            schema_dict = json.loads(content)

        if not isinstance(schema_dict, dict):
            raise InputValidationError("Schema file must contain a dictionary")

        # Import here to avoid circular imports
        from .schema import create_dynamic_model_from_schema

        model = create_dynamic_model_from_schema(schema_dict)
        LOGGER.info("✅ Loaded schema and created dynamic model")

        return model

    except json.JSONDecodeError as e:
        raise InputValidationError(f"Invalid JSON in schema file: {e}") from e
    except Exception as e:
        raise InputValidationError(f"Failed to load schema file: {e}") from e


def yaml_recursively_force_literal(data: Any) -> Any:
    """
    Recursively convert data to use literal YAML style.

    This ensures that multi-line strings are preserved as literal blocks
    in YAML output, making them more readable.

    Args:
        data: Data to convert

    Returns:
        Data with literal YAML style applied
    """
    from ruamel.yaml import scalarstring

    if isinstance(data, dict):
        return {k: yaml_recursively_force_literal(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [yaml_recursively_force_literal(item) for item in data]
    elif isinstance(data, str) and "\n" in data:
        return scalarstring.LiteralScalarString(data)
    else:
        return data
