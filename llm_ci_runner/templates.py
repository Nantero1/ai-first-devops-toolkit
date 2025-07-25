"""
Template handling for LLM CI Runner.

This module provides functionality for loading and rendering templates
using both Handlebars and Jinja2 template engines with YAML variable support.
"""

import json
import logging
from pathlib import Path
from typing import Any

from rich.panel import Panel
from rich.syntax import Syntax
from ruamel.yaml import YAML, YAMLError
from semantic_kernel import Kernel
from semantic_kernel.contents import ChatHistory, ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.functions import KernelArguments
from semantic_kernel.functions.kernel_function_from_prompt import KernelFunctionFromPrompt
from semantic_kernel.prompt_template import (
    HandlebarsPromptTemplate,
    Jinja2PromptTemplate,
    PromptTemplateConfig,
)

from .exceptions import InputValidationError
from .logging_config import CONSOLE

LOGGER = logging.getLogger(__name__)


def get_template_format(template_file: Path) -> str:
    """
    Determine template format based on file extension for multi-engine template support.

    PURPOSE: Detects template format to enable unified template loading across
    Handlebars, Jinja2, and Semantic Kernel YAML templates. Uses simple extension-based
    detection following KISS principles - trusts Semantic Kernel to validate YAML format.

    Args:
        template_file: Path to the template file

    Returns:
        Template format ('handlebars', 'jinja2', or 'semantic-kernel')

    Raises:
        InputValidationError: If template format cannot be determined
    """
    extension = template_file.suffix.lower()

    LOGGER.debug(f"🔍 Detecting template format for extension: {extension}")

    if extension in [".hbs", ".handlebars"]:
        LOGGER.debug("📋 Detected Handlebars template format")
        return "handlebars"
    elif extension in [".jinja", ".j2", ".jinja2"]:
        LOGGER.debug("📋 Detected Jinja2 template format")
        return "jinja2"
    elif extension in [".yaml", ".yml"]:
        # Trust SK to validate YAML format - it will raise errors if invalid
        LOGGER.debug("📋 Detected Semantic Kernel YAML template format")
        return "semantic-kernel"
    else:
        raise InputValidationError(
            f"Unsupported template format: {extension}. "
            f"Supported formats: .hbs, .handlebars, .jinja, .j2, .jinja2, .yaml, .yml"
        )


def load_template_vars(template_vars_file: Path) -> dict[str, Any]:
    """
    Load template variables from JSON or YAML file.

    Args:
        template_vars_file: Path to the template variables file

    Returns:
        Dictionary of template variables

    Raises:
        InputValidationError: If file cannot be loaded or parsed
    """
    LOGGER.debug(f"📂 Loading template variables from: {template_vars_file}")

    try:
        yaml = YAML(typ="safe", pure=True)

        with open(template_vars_file, encoding="utf-8") as f:
            content = f.read()

        # Try YAML first, fallback to JSON
        try:
            template_vars = yaml.load(content)
        except YAMLError:
            # Fallback to JSON
            template_vars = json.loads(content)

        if not isinstance(template_vars, dict):
            raise InputValidationError("Template variables must be a dictionary")

        LOGGER.info(f"✅ Loaded {len(template_vars)} template variables")
        # Pretty print template variables when DEBUG logging is enabled
        if LOGGER.isEnabledFor(logging.DEBUG):
            json_content = json.dumps(template_vars, indent=2, ensure_ascii=False)
            syntax_highlighted = Syntax(json_content, "json", line_numbers=False)
            CONSOLE.print(
                Panel(
                    syntax_highlighted,
                    title="📝 Template Variables",
                    style="cyan",
                )
            )

        return template_vars

    except Exception as e:
        raise InputValidationError(f"Failed to load template variables: {e}") from e


def load_handlebars_template(template_file: Path) -> HandlebarsPromptTemplate:
    """
    Load a Handlebars template from file.

    Args:
        template_file: Path to the Handlebars template file

    Returns:
        Configured HandlebarsPromptTemplate

    Raises:
        InputValidationError: If template cannot be loaded
    """
    LOGGER.debug(f"📂 Loading Handlebars template from: {template_file}")

    try:
        with open(template_file, encoding="utf-8") as f:
            template_content = f.read()

        # Create PromptTemplateConfig for Handlebars
        config = PromptTemplateConfig(
            template=template_content,
            template_format="handlebars",
        )

        template = HandlebarsPromptTemplate(prompt_template_config=config)

        LOGGER.debug("✅ Handlebars template loaded successfully")
        LOGGER.debug(f"   Template length: {len(template_content)} characters")

        return template

    except Exception as e:
        raise InputValidationError(f"Failed to load Handlebars template: {e}") from e


def load_jinja2_template(template_file: Path) -> Jinja2PromptTemplate:
    """
    Load a Jinja2 template from file.

    Args:
        template_file: Path to the Jinja2 template file

    Returns:
        Configured Jinja2PromptTemplate

    Raises:
        InputValidationError: If template cannot be loaded
    """
    LOGGER.debug(f"📂 Loading Jinja2 template from: {template_file}")

    try:
        with open(template_file, encoding="utf-8") as f:
            template_content = f.read()

        # Create PromptTemplateConfig for Jinja2
        config = PromptTemplateConfig(
            template=template_content,
            template_format="jinja2",
        )

        template = Jinja2PromptTemplate(prompt_template_config=config)

        LOGGER.info("✅ Jinja2 template loaded successfully")
        LOGGER.debug(f"   Template length: {len(template_content)} characters")

        return template

    except Exception as e:
        raise InputValidationError(f"Failed to load Jinja2 template: {e}") from e


def load_semantic_kernel_yaml_template(template_file: Path) -> KernelFunctionFromPrompt:
    """
    Load a Semantic Kernel YAML template using SK's native YAML parser.

    PURPOSE: Loads self-contained YAML templates that include prompt template,
    input variables, execution settings, and optional schema definitions.
    Uses Microsoft's official KernelFunctionFromPrompt.from_yaml() to ensure
    compatibility with SK conventions and automatic validation.

    Args:
        template_file: Path to the SK YAML template file

    Returns:
        Configured KernelFunctionFromPrompt ready for execution

    Raises:
        InputValidationError: If template cannot be loaded or is invalid
    """
    LOGGER.debug(f"📂 Loading Semantic Kernel YAML template from: {template_file}")

    try:
        with open(template_file, encoding="utf-8") as f:
            yaml_content = f.read()

        # Use SK's native YAML loader - trusts SK to handle all validation
        function = KernelFunctionFromPrompt.from_yaml(yaml_content)

        LOGGER.debug("✅ SK YAML template loaded successfully")
        LOGGER.debug(f"   Template function name: {function.name}")

        return function

    except Exception as e:
        raise InputValidationError(f"Failed to load SK YAML template: {e}") from e


def load_template(
    template_file: Path,
) -> HandlebarsPromptTemplate | Jinja2PromptTemplate | KernelFunctionFromPrompt:
    """
    Load a template from file with automatic format detection for multi-engine support.

    PURPOSE: Provides unified template loading across Handlebars, Jinja2, and
    Semantic Kernel YAML templates. Automatically detects format by extension
    and delegates to appropriate specialized loader function.

    Args:
        template_file: Path to the template file

    Returns:
        Configured template (HandlebarsPromptTemplate, Jinja2PromptTemplate, or KernelFunctionFromPrompt)

    Raises:
        InputValidationError: If template format is unsupported or loading fails
    """
    template_format = get_template_format(template_file)

    if template_format == "handlebars":
        return load_handlebars_template(template_file)
    elif template_format == "jinja2":
        return load_jinja2_template(template_file)
    elif template_format == "semantic-kernel":
        return load_semantic_kernel_yaml_template(template_file)
    else:
        raise InputValidationError(f"Unsupported template format: {template_format}")


async def render_template(
    template: HandlebarsPromptTemplate | Jinja2PromptTemplate,
    template_vars: dict[str, Any],
    kernel: Kernel,
) -> str:
    """
    Render a template with variables using the Semantic Kernel.

    Args:
        template: Template to render
        template_vars: Variables to inject into the template
        kernel: Semantic Kernel instance

    Returns:
        Rendered template content

    Raises:
        InputValidationError: If template rendering fails
    """
    LOGGER.debug("🎨 Rendering template with variables")
    LOGGER.debug(f"   Variables: {list(template_vars.keys())}")

    try:
        # Create KernelArguments from template variables
        arguments = KernelArguments(**template_vars)

        # Render the template with variables
        rendered_content = await template.render(kernel, arguments)

        LOGGER.debug("✅ Template rendered successfully")
        LOGGER.debug(f"   Rendered length: {len(rendered_content)} characters")

        return rendered_content

    except Exception as e:
        raise InputValidationError(f"Failed to render template: {e}") from e


def parse_rendered_template_to_chat_history(rendered_content: str) -> ChatHistory:
    """
    Parse rendered template content into ChatHistory.

    This function parses Microsoft Semantic Kernel format messages from rendered templates:
    <message role="system">System message content</message>
    <message role="user">User message content</message>
    <message role="assistant">Assistant message content</message>

    Args:
        rendered_content: Rendered template content with message tags

    Returns:
        ChatHistory with parsed messages

    Raises:
        InputValidationError: If parsing fails or no messages found
    """
    import re

    LOGGER.debug("🔍 Parsing rendered template to ChatHistory")

    # Regex to match Microsoft Semantic Kernel message format
    message_pattern = r'<message\s+role="([^"]+)"[^>]*>(.*?)</message>'
    matches = re.findall(message_pattern, rendered_content, re.DOTALL)

    if not matches:
        raise InputValidationError(
            'No valid messages found in rendered template. Expected format: <message role="system">content</message>'
        )

    chat_history = ChatHistory()

    for role_str, content in matches:
        # Strip whitespace from content
        content = content.strip()

        # Map role strings to AuthorRole enum
        role_mapping = {
            "system": AuthorRole.SYSTEM,
            "user": AuthorRole.USER,
            "assistant": AuthorRole.ASSISTANT,
        }

        if role_str not in role_mapping:
            raise InputValidationError(f"Invalid message role: {role_str}")

        role = role_mapping[role_str]

        # Create chat message content
        message = ChatMessageContent(role=role, content=content)
        chat_history.add_message(message)

        LOGGER.debug(f"   Added {role_str} message: {len(content)} characters")

    LOGGER.debug(f"✅ Parsed {len(matches)} messages from template")
    return chat_history
