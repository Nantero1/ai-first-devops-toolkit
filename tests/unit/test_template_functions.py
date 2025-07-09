"""
Unit tests for template functions in llm_ci_runner.py

Tests load_template_vars, load_handlebars_template, and template parsing functions
with heavy mocking following the Given-When-Then pattern.
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import yaml

from llm_ci_runner import (
    InputValidationError,
    load_handlebars_template,
    load_template_vars,
    parse_rendered_template_to_chat_history,
    render_handlebars_template,
)


class TestLoadTemplateVars:
    """Tests for load_template_vars function."""

    def test_load_json_template_vars(self, temp_dir):
        """Test loading template variables from JSON file."""
        # given
        vars_file = temp_dir / "vars.json"
        vars_data = {
            "customer": {
                "first_name": "John",
                "last_name": "Doe",
                "age": 30,
                "membership": "Gold",
            },
            "history": [
                {"role": "user", "content": "What is my current membership level?"},
            ],
        }
        with open(vars_file, "w") as f:
            json.dump(vars_data, f)

        # when
        result = load_template_vars(vars_file)

        # then
        assert isinstance(result, dict)
        assert "customer" in result
        assert "history" in result
        assert result["customer"]["first_name"] == "John"
        assert result["history"][0]["role"] == "user"

    def test_load_yaml_template_vars(self, temp_dir):
        """Test loading template variables from YAML file."""
        # given
        vars_file = temp_dir / "vars.yaml"
        vars_content = """
customer:
  first_name: Jane
  last_name: Smith
  age: 25
  membership: Silver
history:
  - role: user
    content: How can I upgrade my membership?
"""
        with open(vars_file, "w") as f:
            f.write(vars_content)

        # when
        result = load_template_vars(vars_file)

        # then
        assert isinstance(result, dict)
        assert result["customer"]["first_name"] == "Jane"
        assert result["customer"]["membership"] == "Silver"
        assert result["history"][0]["content"] == "How can I upgrade my membership?"

    def test_load_nonexistent_vars_file_raises_error(self):
        """Test that nonexistent vars file raises InputValidationError."""
        # given
        nonexistent_file = Path("nonexistent.json")

        # when & then
        with pytest.raises(InputValidationError, match="Template variables file not found"):
            load_template_vars(nonexistent_file)

    def test_load_invalid_json_vars_raises_error(self, temp_dir):
        """Test that invalid JSON vars raises InputValidationError."""
        # given
        invalid_vars_file = temp_dir / "invalid.json"
        with open(invalid_vars_file, "w") as f:
            f.write("{ invalid json }")

        # when & then
        with pytest.raises(InputValidationError, match="Invalid JSON in template variables file"):
            load_template_vars(invalid_vars_file)

    def test_load_invalid_yaml_vars_raises_error(self, temp_dir):
        """Test that invalid YAML vars raises InputValidationError."""
        # given
        invalid_vars_file = temp_dir / "invalid.yaml"
        with open(invalid_vars_file, "w") as f:
            f.write("customer:\n  first_name: John\n  invalid_key: {\n")

        # when & then
        with pytest.raises(InputValidationError, match="Invalid YAML in template variables file"):
            load_template_vars(invalid_vars_file)

    def test_load_non_dict_vars_raises_error(self, temp_dir):
        """Test that non-dict template vars raises InputValidationError."""
        # given
        non_dict_vars_file = temp_dir / "non_dict.json"
        with open(non_dict_vars_file, "w") as f:
            json.dump(["not", "a", "dict"], f)

        # when & then
        with pytest.raises(InputValidationError, match="Template variables must be a valid object"):
            load_template_vars(non_dict_vars_file)


class TestLoadHandlebarsTemplate:
    """Tests for load_handlebars_template function."""

    def test_load_valid_handlebars_template(self, temp_dir):
        """Test loading a valid Handlebars .hbs template."""
        # given
        template_file = temp_dir / "template.hbs"
        template_content = """{{#message role="system"}}
You are an AI agent for {{company_name}}.
Customer: {{customer.first_name}} {{customer.last_name}}
{{/message}}

{{#each history}}
{{#message role="{{role}}"}}
{{content}}
{{/message}}
{{/each}}"""
        with open(template_file, "w") as f:
            f.write(template_content)

        # when
        with (
            patch("llm_ci_runner.PromptTemplateConfig") as mock_config_class,
            patch("llm_ci_runner.HandlebarsPromptTemplate") as mock_template_class,
        ):
            mock_config = MagicMock()
            mock_config.name = "template"
            mock_config_class.return_value = mock_config

            mock_template = MagicMock()
            mock_template_class.return_value = mock_template

            result = load_handlebars_template(template_file)

        # then
        mock_config_class.assert_called_once_with(
            template=template_content,
            template_format="handlebars",
            name="template",
            description="Handlebars template loaded from template.hbs",
        )
        mock_template_class.assert_called_once_with(prompt_template_config=mock_config)
        assert result == mock_template

    def test_load_nonexistent_template_raises_error(self):
        """Test that nonexistent template file raises InputValidationError."""
        # given
        nonexistent_file = Path("nonexistent.yaml")

        # when & then
        with pytest.raises(InputValidationError, match="Template file not found"):
            load_handlebars_template(nonexistent_file)

    def test_load_invalid_template_content_raises_error(self, temp_dir):
        """Test that invalid template content raises InputValidationError."""
        # given
        template_file = temp_dir / "invalid_template.hbs"
        with open(template_file, "w") as f:
            f.write("invalid template content")

        # when & then
        with patch(
            "llm_ci_runner.PromptTemplateConfig",
            side_effect=Exception("Invalid template"),
        ):
            with pytest.raises(InputValidationError, match="Invalid Handlebars template content"):
                load_handlebars_template(template_file)


class TestRenderHandlebarsTemplate:
    """Tests for render_handlebars_template function."""

    @pytest.mark.asyncio
    async def test_render_template_successfully(self):
        """Test successful template rendering."""
        # given
        mock_template = AsyncMock()
        template_vars = {"customer": {"name": "John"}, "company": "Test Corp"}
        mock_kernel = MagicMock()
        rendered_content = '<message role="system">Hello John from Test Corp</message>'

        mock_template.render.return_value = rendered_content

        # when
        result = await render_handlebars_template(mock_template, template_vars, mock_kernel)

        # then
        assert result == rendered_content
        mock_template.render.assert_called_once()

    @pytest.mark.asyncio
    async def test_render_template_failure_raises_error(self):
        """Test that template rendering failure raises InputValidationError."""
        # given
        mock_template = AsyncMock()
        template_vars = {"invalid": "vars"}
        mock_kernel = MagicMock()

        mock_template.render.side_effect = Exception("Rendering failed")

        # when & then
        with pytest.raises(InputValidationError, match="Error rendering Handlebars template"):
            await render_handlebars_template(mock_template, template_vars, mock_kernel)


class TestParseRenderedTemplateToChat:
    """Tests for parse_rendered_template_to_chat_history function."""

    def test_parse_valid_rendered_content(self):
        """Test parsing valid rendered template content."""
        # given
        rendered_content = """
            <message role="system">
                You are a helpful assistant.
            </message>
            <message role="user">
                Hello, how are you?
            </message>
        """

        # when
        with (
            patch("llm_ci_runner.ChatHistory") as mock_chat_history_class,
            patch("llm_ci_runner.ChatMessageContent") as mock_message_class,
            patch("llm_ci_runner.AuthorRole") as mock_role_class,
        ):
            mock_chat_history = MagicMock()
            mock_chat_history_class.return_value = mock_chat_history

            mock_message = MagicMock()
            mock_message_class.return_value = mock_message

            result = parse_rendered_template_to_chat_history(rendered_content)

        # then
        assert result == mock_chat_history
        assert mock_message_class.call_count == 2  # Two messages
        mock_chat_history.add_message.assert_called()

    def test_parse_no_messages_raises_error(self):
        """Test that content with no message blocks raises InputValidationError."""
        # given
        rendered_content = "Just plain text without message blocks"

        # when & then
        with pytest.raises(InputValidationError, match="No <message> blocks found in rendered template"):
            parse_rendered_template_to_chat_history(rendered_content)

    def test_parse_invalid_role_raises_error(self):
        """Test that invalid role raises InputValidationError."""
        # given
        rendered_content = '<message role="invalid_role">Content</message>'

        # when & then
        with patch("llm_ci_runner.AuthorRole", side_effect=ValueError("Invalid role")):
            with pytest.raises(InputValidationError, match="Invalid role 'invalid_role' in message 0"):
                parse_rendered_template_to_chat_history(rendered_content)
