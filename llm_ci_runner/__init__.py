"""
LLM CI Runner - AI-powered automation for pipelines.

This package provides a zero-friction interface for running arbitrary LLM-driven tasks
in CI/CD pipelines, supporting structured outputs and enterprise authentication.

Main Features:
- 🤖 AI-powered code reviews with structured findings
- 📝 Intelligent documentation generation
- 🔍 Security analysis with guaranteed schema compliance
- 🎯 Quality gates through AI-driven validation
- 📄 Template-driven workflows with Handlebars and Jinja2
- 🔐 Enterprise security with Azure RBAC support
- 📦 CI/CD friendly with JSON/YAML input/output

Usage:
    # Traditional input file mode
    llm-ci-runner --input-file input.json --schema-file schema.json --output-file result.json

    # Template-based mode
    llm-ci-runner --template-file template.hbs --template-vars vars.yaml --schema-file schema.yaml

Environment Variables:
    AZURE_OPENAI_ENDPOINT: Azure OpenAI endpoint URL
    AZURE_OPENAI_MODEL: Your custom model deployment name
    AZURE_OPENAI_API_VERSION: API version (default: 2024-12-01-preview)
    AZURE_OPENAI_API_KEY: API key (optional, uses RBAC if not provided)
"""

# Import main CLI entry point
from azure.identity.aio import DefaultAzureCredential
from rich.logging import RichHandler
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatPromptExecutionSettings
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import (
    AzureChatCompletion,
)

# Import additional functions for testing compatibility
# Import classes for testing compatibility
from semantic_kernel.contents import ChatHistory, ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.prompt_template import (
    HandlebarsPromptTemplate,
    Jinja2PromptTemplate,
    PromptTemplateConfig,
)

from .core import cli_main, main
from .exceptions import (
    AuthenticationError,
    InputValidationError,
    LLMExecutionError,
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

# Import core functionality for programmatic use
from .llm_service import (
    azure_token_provider,
    get_azure_token_with_credential,
    setup_azure_service,
    setup_llm_service,
    setup_openai_service,
)

# Import logger for testing compatibility
from .logging_config import CONSOLE, LOGGER, setup_logging
from .schema import create_dynamic_model_from_schema
from .templates import (
    get_template_format,
    load_handlebars_template,
    load_jinja2_template,
    load_template,
    load_template_vars,
    parse_rendered_template_to_chat_history,
    render_template,
)

__all__ = [
    # Main entry points
    "cli_main",
    "main",
    # Functions for testing compatibility
    "create_chat_history",
    "execute_llm_task",
    "load_input_file",
    "load_schema_file",
    "load_template",
    "load_template_vars",
    "parse_arguments",
    "parse_rendered_template_to_chat_history",
    "render_template",
    "setup_azure_service",
    "setup_llm_service",
    "setup_openai_service",
    "write_output_file",
    # Core functionality
    "azure_token_provider",
    "get_azure_token_with_credential",
    "create_dynamic_model_from_schema",
    # Template functionality
    "get_template_format",
    "load_handlebars_template",
    "load_jinja2_template",
    # Logging
    "setup_logging",
    "CONSOLE",
    # Exceptions
    "LLMRunnerError",
    "InputValidationError",
    "AuthenticationError",
    "LLMExecutionError",
    "SchemaValidationError",
    # Classes for testing compatibility
    "ChatHistory",
    "ChatMessageContent",
    "AuthorRole",
    "AzureChatCompletion",
    "HandlebarsPromptTemplate",
    "Jinja2PromptTemplate",
    "PromptTemplateConfig",
    "Kernel",
    "OpenAIChatPromptExecutionSettings",
    "DefaultAzureCredential",
    "RichHandler",
    # Logger for testing compatibility
    "LOGGER",
]

# Package metadata
__version__ = "1.2.0"
__author__ = "Benjamin Linnik"
__url__ = "https://github.com/Nantero1/ai-first-devops-toolkit"
