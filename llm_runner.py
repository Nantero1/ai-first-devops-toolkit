#!/usr/bin/env python3
"""
LLM Runner - A simple CI/CD utility for running LLM tasks with Semantic Kernel

This script provides a zero-friction interface for running arbitrary LLM-driven tasks
in CI/CD pipelines, supporting structured outputs and enterprise authentication.

Usage:
    python llm_runner.py \
        --input-file pr-context.json \
        --output-file review-result.json \
        --schema-file review-schema.json \
        --log-level DEBUG

Environment Variables:
    AZURE_OPENAI_ENDPOINT: Azure OpenAI endpoint URL
    AZURE_OPENAI_MODEL: Model deployment name (e.g., gpt-4)
    AZURE_OPENAI_API_VERSION: API version (default: 2024-08-01-preview)

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
            "session_id": "task-123",
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
from typing import Dict, List, Optional, Any, Union

# Rich imports for beautiful console output
from rich.console import Console
from rich.logging import RichHandler
from rich.traceback import install as install_rich_traceback

# Semantic Kernel imports
from semantic_kernel import Kernel
from semantic_kernel.contents import ChatHistory, ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.functions import KernelArguments
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import (
    AzureChatCompletion,
)
from semantic_kernel.connectors.ai.open_ai import OpenAIChatPromptExecutionSettings

# Azure authentication
from azure.identity.aio import DefaultAzureCredential
from azure.core.exceptions import ClientAuthenticationError

# Install rich traceback for better error display
install_rich_traceback()

# Global CONSOLE for rich output
CONSOLE = Console()
LOGGER = logging.getLogger("llm_runner")


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
                show_path=True,
                markup=True,
                rich_tracebacks=True,
            )
        ],
    )

    LOGGER.info(
        f"[bold green]🚀 LLM Runner initialized with log level: {log_level.upper()}[/bold green]"
    )
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
    # Basic usage
    python llm_runner.py --input-file input.json --output-file result.json
    
    # With structured output schema
    python llm_runner.py --input-file input.json --output-file result.json --schema-file schema.json
    
    # With debug logging
    python llm_runner.py --input-file input.json --output-file result.json --log-level DEBUG

Environment Variables:
    AZURE_OPENAI_ENDPOINT    Azure OpenAI endpoint URL
    AZURE_OPENAI_MODEL       Model deployment name
    AZURE_OPENAI_API_VERSION API version (default: 2024-08-01-preview)
        """,
    )

    parser.add_argument(
        "--input-file",
        required=True,
        type=Path,
        help="JSON file containing messages and optional context",
    )

    parser.add_argument(
        "--output-file",
        required=True,
        type=Path,
        help="Output file for LLM response (JSON format)",
    )

    parser.add_argument(
        "--schema-file",
        type=Path,
        help="Optional JSON schema file for structured output",
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)",
    )

    return parser.parse_args()


def load_input_json(input_file: Path) -> Dict[str, Any]:
    """
    Load and parse input JSON file containing messages and optional context.

    Args:
        input_file: Path to input JSON file

    Returns:
        Parsed JSON data

    Raises:
        InputValidationError: If file doesn't exist or JSON is invalid
    """
    LOGGER.debug(f"📂 Loading input file: {input_file}")

    if not input_file.exists():
        raise InputValidationError(f"Input file not found: {input_file}")

    try:
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Validate required 'messages' field
        if "messages" not in data:
            raise InputValidationError("Input JSON must contain 'messages' field")

        if not isinstance(data["messages"], list) or len(data["messages"]) == 0:
            raise InputValidationError("'messages' must be a non-empty array")

        LOGGER.debug(f"✅ Loaded {len(data['messages'])} messages")
        if "context" in data:
            LOGGER.debug(
                f"📋 Additional context provided: {list(data['context'].keys())}"
            )

        return data

    except json.JSONDecodeError as e:
        raise InputValidationError(f"Invalid JSON in input file: {e}")
    except Exception as e:
        raise InputValidationError(f"Error reading input file: {e}")


def create_chat_history(messages: List[Dict[str, Any]]) -> ChatHistory:
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
                raise InputValidationError(
                    f"Message {i} missing required 'role' or 'content' field"
                )

            # Create ChatMessageContent
            chat_message = ChatMessageContent(
                role=AuthorRole(msg["role"]),
                content=msg["content"],
                name=msg.get("name"),  # Optional name field
            )

            chat_history.add_message(chat_message)
            LOGGER.debug(
                f"  ➕ Added {msg['role']} message ({len(msg['content'])} chars)"
            )

        except ValueError as e:
            raise InputValidationError(
                f"Invalid role '{msg.get('role')}' in message {i}: {e}"
            )
        except Exception as e:
            raise InputValidationError(f"Error processing message {i}: {e}")

    LOGGER.info(f"✅ Created ChatHistory with {len(chat_history)} messages")
    return chat_history


async def setup_azure_service() -> AzureChatCompletion:
    """
    Setup Azure OpenAI service with dual authentication support.

    Authentication Methods (in priority order):
    1. Azure RBAC (default): Uses DefaultAzureCredential for enterprise scenarios
    2. API Key (fallback): Uses AZURE_OPENAI_API_KEY environment variable

    This provides flexibility for different deployment scenarios while maintaining
    security best practices by defaulting to RBAC authentication.

    Args:
        logger: Logger instance

    Returns:
        Configured AzureChatCompletion service

    Raises:
        AuthenticationError: If Azure authentication fails
    """
    LOGGER.debug("🔐 Setting up Azure OpenAI authentication")

    # Get environment variables
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    model = os.getenv("AZURE_OPENAI_MODEL")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
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
            return service

        # Fallback to RBAC authentication
        LOGGER.info("🔐 Using Azure RBAC authentication")
        # Setup async Azure credential
        credential = DefaultAzureCredential()

        # Create Azure ChatCompletion service
        service = AzureChatCompletion(
            deployment_name=model,
            endpoint=endpoint,
            ad_token_provider=credential.get_token,
            api_version=api_version,
        )

        LOGGER.info("✅ Azure OpenAI service configured successfully")
        return service

    except ClientAuthenticationError as e:
        raise AuthenticationError(f"Azure authentication failed: {e}")
    except Exception as e:
        raise AuthenticationError(f"Error setting up Azure service: {e}")


def load_json_schema(schema_file: Optional[Path]) -> Optional[str]:
    """
    Load JSON schema from file for structured output.

    Args:
        schema_file: Optional path to JSON schema file

    Returns:
        JSON schema string or None if no schema

    Raises:
        InputValidationError: If schema file cannot be loaded or is invalid JSON
    """
    if not schema_file:
        LOGGER.debug("📋 No schema file provided - using text output")
        return None

    LOGGER.debug(f"📋 Loading JSON schema from: {schema_file}")

    try:
        if not schema_file.exists():
            raise InputValidationError(f"Schema file not found: {schema_file}")

        with open(schema_file, "r", encoding="utf-8") as f:
            schema_content = f.read().strip()

        # Validate it's valid JSON
        try:
            json.loads(schema_content)
        except json.JSONDecodeError as e:
            raise InputValidationError(f"Invalid JSON in schema file: {e}")

        LOGGER.info(f"✅ JSON schema loaded successfully from: {schema_file}")
        return schema_content

    except InputValidationError:
        raise
    except Exception as e:
        raise InputValidationError(f"Error loading schema file: {e}")


async def execute_llm_task(
    service: AzureChatCompletion,
    chat_history: ChatHistory,
    context: Optional[Dict[str, Any]],
    json_schema: Optional[str],
) -> Union[str, Dict[str, Any]]:
    """
    Execute LLM task using Semantic Kernel with optional structured output.

    Args:
        service: Azure ChatCompletion service
        chat_history: ChatHistory with messages
        context: Optional context for KernelArguments
        json_schema: Optional JSON schema string for structured output
        logger: Logger instance

    Returns:
        LLM response as string or structured dict

    Raises:
        LLMExecutionError: If LLM execution fails
    """
    LOGGER.debug("🤖 Executing LLM task")

    try:
        # Create kernel and add service
        kernel = Kernel()
        kernel.add_service(service)

        # Setup execution settings
        settings = OpenAIChatPromptExecutionSettings()

        if json_schema:
            # Use basic JSON mode - schema will guide the prompt
            settings.response_format = {"type": "json_object"}
            LOGGER.debug("📋 Using JSON output mode with schema guidance")

        # Create kernel arguments
        args = KernelArguments(settings=settings)

        # Add context if provided
        if context:
            for key, value in context.items():
                args[key] = value
            LOGGER.debug(f"📋 Added context: {list(context.keys())}")

        # Build prompt template based on whether schema is provided
        if json_schema:
            prompt_template = (
                """{{$chat_history}}

IMPORTANT: You must respond with valid JSON that follows this exact schema:

```json
"""
                + json_schema
                + """
```

Respond ONLY with valid JSON that matches this schema. Do not include any other text."""
            )
        else:
            prompt_template = "{{$chat_history}}"

        # Execute LLM with prompt template
        LOGGER.info("🚀 Sending request to LLM...")

        result = await kernel.invoke_prompt(
            prompt=prompt_template,
            arguments=args,
            chat_history=chat_history,
        )

        # Extract result content
        if hasattr(result, "value") and result.value:
            response = (
                result.value[0].content
                if hasattr(result.value[0], "content")
                else str(result.value[0])
            )
        else:
            response = str(result)

        # If we used structured output, try to parse as JSON
        if json_schema and response:
            try:
                parsed_response = json.loads(response)
                LOGGER.info("✅ LLM task completed with structured output")
                LOGGER.debug(
                    f"📄 Structured response with {len(parsed_response)} fields"
                )
                return parsed_response
            except json.JSONDecodeError:
                LOGGER.warning("⚠️  Response was not valid JSON, returning as text")

        LOGGER.info("✅ LLM task completed successfully")
        LOGGER.debug(f"📄 Response length: {len(response)} characters")

        return response

    except Exception as e:
        raise LLMExecutionError(f"LLM execution failed: {e}")


def write_output_file(output_file: Path, response: Union[str, Dict[str, Any]]) -> None:
    """
    Write LLM response to output file in JSON format.

    Args:
        output_file: Path to output file
        response: LLM response to write
        logger: Logger instance

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
                "runner": "llm_runner.py",
                "timestamp": "auto-generated",  # You could add actual timestamp
            },
        }

        # Write to file
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        LOGGER.info(f"✅ Output written to: {output_file}")

    except Exception as e:
        raise LLMRunnerError(f"Error writing output file: {e}")


async def main() -> None:
    """
    Main entry point for LLM Runner.

    Orchestrates the entire pipeline from input parsing to output generation.
    """
    try:
        # Parse CLI arguments
        args = parse_arguments()

        # Setup logging with Rich
        setup_logging(args.log_level)

        # Load and validate input JSON
        LOGGER.info("📥 Loading input data...")
        input_data = load_input_json(args.input_file)

        # Create ChatHistory from messages
        chat_history = create_chat_history(input_data["messages"])

        # Setup Azure OpenAI service
        LOGGER.info("🔐 Authenticating with Azure...")
        service = await setup_azure_service()

        # Load JSON schema if provided
        json_schema = load_json_schema(args.schema_file)

        # Execute LLM task
        LOGGER.info("🤖 Processing with LLM...")
        response = await execute_llm_task(
            service=service,
            chat_history=chat_history,
            context=input_data.get("context"),
            json_schema=json_schema,
        )

        # Write output file
        LOGGER.info("💾 Saving results...")
        write_output_file(args.output_file, response)

        # Success message
        CONSOLE.print(
            "\n[bold green]🎉 LLM Runner completed successfully![/bold green]"
        )
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


if __name__ == "__main__":
    asyncio.run(main())
