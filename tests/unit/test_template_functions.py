"""
Unit tests for template functions in llm_ci_runner.py

Tests load_template_vars, load_handlebars_template, load_jinja2_template,
get_template_format, load_template, and template parsing functions
with heavy mocking following the Given-When-Then pattern.
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from llm_ci_runner import (
    InputValidationError,
    get_template_format,
    load_handlebars_template,
    load_jinja2_template,
    load_template,
    load_template_vars,
    parse_rendered_template_to_chat_history,
    render_template,
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
        with pytest.raises(InputValidationError, match="Failed to load template variables"):
            load_template_vars(nonexistent_file)

    def test_load_invalid_json_vars_raises_error(self, temp_dir):
        """Test that invalid JSON vars raises InputValidationError."""
        # given
        invalid_vars_file = temp_dir / "invalid.json"
        with open(invalid_vars_file, "w") as f:
            f.write("{{{{ completely invalid content \n unmatched braces")  # Invalid for both YAML and JSON

        # when & then
        with pytest.raises(InputValidationError, match="Failed to load template variables"):
            load_template_vars(invalid_vars_file)

    def test_load_invalid_yaml_vars_raises_error(self, temp_dir):
        """Test that invalid YAML vars raises InputValidationError."""
        # given
        invalid_vars_file = temp_dir / "invalid.yaml"
        with open(invalid_vars_file, "w") as f:
            f.write("customer:\n  first_name: John\n  invalid_key: {\n")

        # when & then
        with pytest.raises(InputValidationError, match="Failed to load template variables"):
            load_template_vars(invalid_vars_file)

    def test_load_non_dict_vars_raises_error(self, temp_dir):
        """Test that non-dict template vars raises InputValidationError."""
        # given
        non_dict_vars_file = temp_dir / "non_dict.json"
        with open(non_dict_vars_file, "w") as f:
            json.dump(["not", "a", "dict"], f)

        # when & then
        with pytest.raises(InputValidationError, match="Failed to load template variables"):
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
            patch("llm_ci_runner.templates.PromptTemplateConfig") as mock_config_class,
            patch("llm_ci_runner.templates.HandlebarsPromptTemplate") as mock_template_class,
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
        )
        mock_template_class.assert_called_once_with(prompt_template_config=mock_config)
        assert result == mock_template

    def test_load_nonexistent_template_raises_error(self):
        """Test that nonexistent template file raises InputValidationError."""
        # given
        nonexistent_file = Path("nonexistent.yaml")

        # when & then
        with pytest.raises(InputValidationError, match="Failed to load Handlebars template"):
            load_handlebars_template(nonexistent_file)

    def test_load_invalid_template_content_raises_error(self, temp_dir):
        """Test that invalid template content raises InputValidationError."""
        # given
        template_file = temp_dir / "invalid_template.hbs"
        with open(template_file, "w") as f:
            f.write("invalid template content")

        # when & then
        with patch(
            "llm_ci_runner.templates.PromptTemplateConfig",
            side_effect=Exception("Invalid template"),
        ):
            with pytest.raises(InputValidationError, match="Failed to load Handlebars template"):
                load_handlebars_template(template_file)


class TestGetTemplateFormat:
    """Tests for get_template_format function."""

    def test_detect_handlebars_format(self):
        """Test detecting Handlebars format from .hbs extension."""
        # given
        template_file = Path("template.hbs")

        # when
        result = get_template_format(template_file)

        # then
        assert result == "handlebars"

    def test_detect_jinja2_format_jinja_extension(self):
        """Test detecting Jinja2 format from .jinja extension."""
        # given
        template_file = Path("template.jinja")

        # when
        result = get_template_format(template_file)

        # then
        assert result == "jinja2"

    def test_detect_jinja2_format_j2_extension(self):
        """Test detecting Jinja2 format from .j2 extension."""
        # given
        template_file = Path("template.j2")

        # when
        result = get_template_format(template_file)

        # then
        assert result == "jinja2"

    def test_detect_jinja2_format_case_insensitive(self):
        """Test detecting Jinja2 format with uppercase extension."""
        # given
        template_file = Path("template.JINJA")

        # when
        result = get_template_format(template_file)

        # then
        assert result == "jinja2"

    def test_unsupported_extension_raises_error(self):
        """Test that unsupported extension raises InputValidationError."""
        # given
        template_file = Path("template.txt")

        # when & then
        with pytest.raises(InputValidationError, match="Unsupported template format"):
            get_template_format(template_file)

    def test_no_extension_raises_error(self):
        """Test that file without extension raises InputValidationError."""
        # given
        template_file = Path("template")

        # when & then
        with pytest.raises(InputValidationError, match="Unsupported template format"):
            get_template_format(template_file)


class TestLoadJinja2Template:
    """Tests for load_jinja2_template function."""

    def test_load_valid_jinja2_template(self, temp_dir):
        """Test loading a valid Jinja2 template."""
        # given
        template_file = temp_dir / "template.jinja"
        template_content = """<message role="system">
You are an AI agent for {{ company_name }}.
Customer: {{ customer.first_name }} {{ customer.last_name }}
</message>

{% for message in history %}
<message role="{{ message.role }}">
{{ message.content }}
</message>
{% endfor %}"""
        with open(template_file, "w") as f:
            f.write(template_content)

        # when
        with (
            patch("llm_ci_runner.templates.PromptTemplateConfig") as mock_config_class,
            patch("llm_ci_runner.templates.Jinja2PromptTemplate") as mock_template_class,
        ):
            mock_config = MagicMock()
            mock_config.name = "template"
            mock_config_class.return_value = mock_config

            mock_template = MagicMock()
            mock_template_class.return_value = mock_template

            result = load_jinja2_template(template_file)

        # then
        mock_config_class.assert_called_once_with(
            template=template_content,
            template_format="jinja2",
        )
        mock_template_class.assert_called_once_with(prompt_template_config=mock_config)
        assert result == mock_template

    def test_load_jinja2_template_with_j2_extension(self, temp_dir):
        """Test loading a Jinja2 template with .j2 extension."""
        # given
        template_file = temp_dir / "template.j2"
        template_content = """<message role="user">
Hello {{ name }}, how are you today?
</message>"""
        with open(template_file, "w") as f:
            f.write(template_content)

        # when
        with (
            patch("llm_ci_runner.templates.PromptTemplateConfig") as mock_config_class,
            patch("llm_ci_runner.templates.Jinja2PromptTemplate") as mock_template_class,
        ):
            mock_config = MagicMock()
            mock_config_class.return_value = mock_config
            mock_template = MagicMock()
            mock_template_class.return_value = mock_template

            result = load_jinja2_template(template_file)

        # then
        mock_config_class.assert_called_once_with(
            template=template_content,
            template_format="jinja2",
        )
        assert result == mock_template

    def test_load_nonexistent_jinja2_template_raises_error(self):
        """Test that nonexistent Jinja2 template file raises InputValidationError."""
        # given
        nonexistent_file = Path("nonexistent.jinja")

        # when & then
        with pytest.raises(InputValidationError, match="Failed to load Jinja2 template"):
            load_jinja2_template(nonexistent_file)

    def test_load_invalid_jinja2_template_content_raises_error(self, temp_dir):
        """Test that invalid Jinja2 template content raises InputValidationError."""
        # given
        template_file = temp_dir / "invalid_template.jinja"
        with open(template_file, "w") as f:
            f.write("invalid template content")

        # when & then
        with patch(
            "llm_ci_runner.templates.PromptTemplateConfig",
            side_effect=Exception("Invalid template"),
        ):
            with pytest.raises(InputValidationError, match="Failed to load Jinja2 template"):
                load_jinja2_template(template_file)


class TestLoadTemplate:
    """Tests for unified load_template function."""

    def test_load_handlebars_template_via_unified_function(self, temp_dir):
        """Test loading Handlebars template through unified load_template function."""
        # given
        template_file = temp_dir / "template.hbs"
        template_content = """{{#message role="system"}}
You are an AI agent.
{{/message}}"""
        with open(template_file, "w") as f:
            f.write(template_content)

        # when
        with (
            patch("llm_ci_runner.templates.load_handlebars_template") as mock_load_handlebars,
            patch("llm_ci_runner.templates.load_jinja2_template") as mock_load_jinja2,
        ):
            mock_template = MagicMock()
            mock_load_handlebars.return_value = mock_template

            result = load_template(template_file)

        # then
        mock_load_handlebars.assert_called_once_with(template_file)
        mock_load_jinja2.assert_not_called()
        assert result == mock_template

    def test_load_jinja2_template_via_unified_function(self, temp_dir):
        """Test loading Jinja2 template through unified load_template function."""
        # given
        template_file = temp_dir / "template.jinja"
        template_content = """<message role="system">
You are an AI agent.
</message>"""
        with open(template_file, "w") as f:
            f.write(template_content)

        # when
        with (
            patch("llm_ci_runner.templates.load_handlebars_template") as mock_load_handlebars,
            patch("llm_ci_runner.templates.load_jinja2_template") as mock_load_jinja2,
        ):
            mock_template = MagicMock()
            mock_load_jinja2.return_value = mock_template

            result = load_template(template_file)

        # then
        mock_load_jinja2.assert_called_once_with(template_file)
        mock_load_handlebars.assert_not_called()
        assert result == mock_template

    def test_load_template_unsupported_format_raises_error(self):
        """Test that unsupported template format raises InputValidationError."""
        # given
        template_file = Path("template.txt")

        # when & then
        with pytest.raises(InputValidationError, match="Unsupported template format"):
            load_template(template_file)

    def test_load_template_unknown_format_raises_error(self):
        """Test that unknown template format returned by get_template_format raises error."""
        # given
        template_file = Path("template.unknown")

        # when & then
        with patch("llm_ci_runner.templates.get_template_format", return_value="unknown"):
            with pytest.raises(InputValidationError, match="Unsupported template format: unknown"):
                load_template(template_file)


class TestRenderTemplate:
    """Tests for render_template function."""

    @pytest.mark.asyncio
    async def test_render_handlebars_template_successfully(self):
        """Test successful Handlebars template rendering."""
        # given
        mock_template = AsyncMock()
        mock_template.render.return_value = '<message role="user">Hello World</message>'
        template_vars = {"name": "World"}
        mock_kernel = MagicMock()

        # when
        result = await render_template(mock_template, template_vars, mock_kernel)

        # then
        mock_template.render.assert_called_once()
        assert result == '<message role="user">Hello World</message>'

    @pytest.mark.asyncio
    async def test_render_jinja2_template_successfully(self):
        """Test successful Jinja2 template rendering."""
        # given
        mock_template = AsyncMock()
        mock_template.render.return_value = '<message role="user">Hello World</message>'
        template_vars = {"name": "World"}
        mock_kernel = MagicMock()

        # when
        result = await render_template(mock_template, template_vars, mock_kernel)

        # then
        mock_template.render.assert_called_once()
        assert result == '<message role="user">Hello World</message>'

    @pytest.mark.asyncio
    async def test_render_template_failure_raises_error(self):
        """Test that template rendering failure raises InputValidationError."""
        # given
        mock_template = AsyncMock()
        mock_template.render.side_effect = Exception("Template error")
        template_vars = {"name": "World"}
        mock_kernel = MagicMock()

        # when & then
        with pytest.raises(InputValidationError, match="Failed to render template"):
            await render_template(mock_template, template_vars, mock_kernel)

    @pytest.mark.asyncio
    async def test_render_template_with_handlebars_type_detection(self):
        """Test that Handlebars template type is correctly detected in error messages."""
        # given
        mock_template = MagicMock()
        # Mock isinstance to return True for HandlebarsPromptTemplate
        with patch("llm_ci_runner.isinstance", return_value=True):
            mock_template.render.side_effect = Exception("Template error")
            template_vars = {"name": "World"}
            mock_kernel = MagicMock()

            # when & then
            with pytest.raises(InputValidationError, match="Failed to render template"):
                await render_template(mock_template, template_vars, mock_kernel)

    @pytest.mark.asyncio
    async def test_render_template_with_jinja2_type_detection(self):
        """Test that Jinja2 template type is correctly detected in error messages."""
        # given
        mock_template = MagicMock()
        # Mock isinstance to return False for HandlebarsPromptTemplate (making it Jinja2)
        with patch("llm_ci_runner.isinstance", return_value=False):
            mock_template.render.side_effect = Exception("Template error")
            template_vars = {"name": "World"}
            mock_kernel = MagicMock()

            # when & then
            with pytest.raises(InputValidationError, match="Failed to render template"):
                await render_template(mock_template, template_vars, mock_kernel)


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
        result = parse_rendered_template_to_chat_history(rendered_content)

        # then
        # Verify we get a real ChatHistory object
        from semantic_kernel.contents import ChatHistory

        assert isinstance(result, ChatHistory)

        # Verify it has the expected number of messages
        assert len(result.messages) == 2

        # Verify message content and roles
        messages = result.messages
        assert messages[0].role.name == "SYSTEM"
        assert "You are a helpful assistant." in messages[0].content
        assert messages[1].role.name == "USER"
        assert "Hello, how are you?" in messages[1].content

    def test_parse_no_messages_raises_error(self):
        """Test that content with no message blocks raises InputValidationError."""
        # given
        rendered_content = "Just plain text without message blocks"

        # when & then
        with pytest.raises(InputValidationError, match="No valid messages found in rendered template"):
            parse_rendered_template_to_chat_history(rendered_content)

    def test_parse_invalid_role_raises_error(self):
        """Test that invalid role raises InputValidationError."""
        # given
        rendered_content = '<message role="invalid_role">Content</message>'

        # when & then
        with patch(
            "semantic_kernel.contents.utils.author_role.AuthorRole",
            side_effect=ValueError("Invalid role"),
        ):
            with pytest.raises(InputValidationError, match="Invalid message role: invalid_role"):
                parse_rendered_template_to_chat_history(rendered_content)
