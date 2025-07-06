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
from semantic_kernel.kernel_pydantic import KernelBaseModel

# Azure authentication
from azure.identity.aio import DefaultAzureCredential
from azure.core.exceptions import ClientAuthenticationError

# Install rich traceback for better error display
install_rich_traceback()

# Global console for rich output
console = Console()


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
                console=console,
                show_time=True,
                show_level=True,
                show_path=True,
                markup=True,
                rich_tracebacks=True,
            )
        ],
    )

    logger = logging.getLogger("llm_runner")
    logger.info(
        f"[bold green]🚀 LLM Runner initialized with log level: {log_level.upper()}[/bold green]"
    )
    return logger


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
        help="Optional Pydantic model schema file for structured output",
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)",
    )

    return parser.parse_args()


def load_input_json(input_file: Path, logger: logging.Logger) -> Dict[str, Any]:
    """
    Load and parse input JSON file containing messages and optional context.

    Args:
        input_file: Path to input JSON file
        logger: Logger instance

    Returns:
        Parsed JSON data

    Raises:
        InputValidationError: If file doesn't exist or JSON is invalid
    """
    logger.debug(f"📂 Loading input file: {input_file}")

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

        logger.debug(f"✅ Loaded {len(data['messages'])} messages")
        if "context" in data:
            logger.debug(
                f"📋 Additional context provided: {list(data['context'].keys())}"
            )

        return data

    except json.JSONDecodeError as e:
        raise InputValidationError(f"Invalid JSON in input file: {e}")
    except Exception as e:
        raise InputValidationError(f"Error reading input file: {e}")


def create_chat_history(
    messages: List[Dict[str, Any]], logger: logging.Logger
) -> ChatHistory:
    """
    Create Semantic Kernel ChatHistory from messages array.

    Args:
        messages: List of message dictionaries with role, content, and optional name
        logger: Logger instance

    Returns:
        ChatHistory object ready for Semantic Kernel

    Raises:
        InputValidationError: If message format is invalid
    """
    logger.debug("🔄 Converting messages to ChatHistory")

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
            logger.debug(
                f"  ➕ Added {msg['role']} message ({len(msg['content'])} chars)"
            )

        except ValueError as e:
            raise InputValidationError(
                f"Invalid role '{msg.get('role')}' in message {i}: {e}"
            )
        except Exception as e:
            raise InputValidationError(f"Error processing message {i}: {e}")

    logger.info(f"✅ Created ChatHistory with {len(chat_history)} messages")
    return chat_history


async def setup_azure_service(logger: logging.Logger) -> AzureChatCompletion:
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
    logger.debug("🔐 Setting up Azure OpenAI authentication")

    # Get environment variables
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    model = os.getenv("AZURE_OPENAI_MODEL")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")

    if not endpoint:
        raise AuthenticationError("AZURE_OPENAI_ENDPOINT environment variable not set")
    if not model:
        raise AuthenticationError("AZURE_OPENAI_MODEL environment variable not set")

    logger.debug(f"  🌐 Endpoint: {endpoint}")
    logger.debug(f"  🤖 Model: {model}")
    logger.debug(f"  📅 API Version: {api_version}")

    try:
        # Try API key authentication first if available
        if api_key:
            logger.info("🔑 Using API Key authentication")
            service = AzureChatCompletion(
                deployment_name=model,
                endpoint=endpoint,
                api_key=api_key,
                api_version=api_version,
            )
            logger.info("✅ Azure OpenAI service configured successfully (API Key)")
            return service

        # Fallback to RBAC authentication
        logger.info("🔐 Using Azure RBAC authentication")
        # Setup async Azure credential
        credential = DefaultAzureCredential()

        # Create Azure ChatCompletion service
        service = AzureChatCompletion(
            deployment_name=model,
            endpoint=endpoint,
            ad_token_provider=credential.get_token,
            api_version=api_version,
        )

        logger.info("✅ Azure OpenAI service configured successfully")
        return service

    except ClientAuthenticationError as e:
        raise AuthenticationError(f"Azure authentication failed: {e}")
    except Exception as e:
        raise AuthenticationError(f"Error setting up Azure service: {e}")


def load_schema_model(
    schema_file: Optional[Path], logger: logging.Logger
) -> Optional[type]:
    """
    Load Pydantic model from schema file for structured output.

    Args:
        schema_file: Optional path to schema file
        logger: Logger instance

    Returns:
        Pydantic model class or None if no schema

    Note:
        This is a placeholder for schema loading. In practice, you would
        either import predefined models or dynamically create them from JSON schema.
    """
    if not schema_file:
        logger.debug("📋 No schema file provided - using text output")
        return None

    logger.debug(f"📋 Schema file provided: {schema_file}")
    logger.warning("⚠️  Schema loading not yet implemented - using text output")

    # TODO: Implement schema loading
    # This could either:
    # 1. Import from a Python module
    # 2. Dynamically create Pydantic model from JSON schema
    # 3. Use predefined models

    return None


async def execute_llm_task(
    service: AzureChatCompletion,
    chat_history: ChatHistory,
    context: Optional[Dict[str, Any]],
    schema_model: Optional[type],
    logger: logging.Logger,
) -> Union[str, Dict[str, Any]]:
    """
    Execute LLM task using Semantic Kernel with optional structured output.

    Args:
        service: Azure ChatCompletion service
        chat_history: ChatHistory with messages
        context: Optional context for KernelArguments
        schema_model: Optional Pydantic model for structured output
        logger: Logger instance

    Returns:
        LLM response as string or structured dict

    Raises:
        LLMExecutionError: If LLM execution fails
    """
    logger.debug("🤖 Executing LLM task")

    try:
        # Create kernel and add service
        kernel = Kernel()
        kernel.add_service(service)

        # Setup execution settings
        settings = OpenAIChatPromptExecutionSettings()
        if schema_model:
            settings.response_format = schema_model
            logger.debug("📋 Using structured output with Pydantic model")

        # Create kernel arguments
        args = KernelArguments(settings=settings)

        # Add context if provided
        if context:
            for key, value in context.items():
                args[key] = value
            logger.debug(f"📋 Added context: {list(context.keys())}")

        # Execute LLM with simple prompt template
        logger.info("🚀 Sending request to LLM...")

        result = await kernel.invoke_prompt(
            prompt_template="{{$chat_history}}",
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

        logger.info("✅ LLM task completed successfully")
        logger.debug(f"📄 Response length: {len(response)} characters")

        return response

    except Exception as e:
        raise LLMExecutionError(f"LLM execution failed: {e}")


def write_output_file(
    output_file: Path, response: Union[str, Dict[str, Any]], logger: logging.Logger
) -> None:
    """
    Write LLM response to output file in JSON format.

    Args:
        output_file: Path to output file
        response: LLM response to write
        logger: Logger instance

    Raises:
        LLMRunnerError: If file writing fails
    """
    logger.debug(f"💾 Writing output to: {output_file}")

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

        logger.info(f"✅ Output written to: {output_file}")

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
        logger = setup_logging(args.log_level)

        # Load and validate input JSON
        logger.info("📥 Loading input data...")
        input_data = load_input_json(args.input_file, logger)

        # Create ChatHistory from messages
        chat_history = create_chat_history(input_data["messages"], logger)

        # Setup Azure OpenAI service
        logger.info("🔐 Authenticating with Azure...")
        service = await setup_azure_service(logger)

        # Load schema model if provided
        schema_model = load_schema_model(args.schema_file, logger)

        # Execute LLM task
        logger.info("🤖 Processing with LLM...")
        response = await execute_llm_task(
            service=service,
            chat_history=chat_history,
            context=input_data.get("context"),
            schema_model=schema_model,
            logger=logger,
        )

        # Write output file
        logger.info("💾 Saving results...")
        write_output_file(args.output_file, response, logger)

        # Success message
        console.print(
            "\n[bold green]🎉 LLM Runner completed successfully![/bold green]"
        )
        console.print(f"[dim]📁 Output saved to: {args.output_file}[/dim]")

    except LLMRunnerError as e:
        logger.error(f"❌ {e}")
        sys.exit(1)

    except KeyboardInterrupt:
        logger.warning("⚠️  Operation cancelled by user")
        console.print("\n[yellow]⚠️  Operation cancelled[/yellow]")
        sys.exit(1)

    except Exception as e:
        # Unexpected error - log with full traceback
        logger.critical(f"💥 Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
