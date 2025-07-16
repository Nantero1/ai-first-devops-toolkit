"""
Unit tests for formatters module.

Tests all formatting functionality including format detection, content formatting,
console display, and file writing with comprehensive coverage.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from ruamel.yaml import YAML

from llm_ci_runner.exceptions import LLMRunnerError
from llm_ci_runner.formatters import (
    FormattedOutput,
    detect_output_format,
    display_formatted_console,
    format_output_content,
    write_formatted_file,
    yaml_recursively_force_literal,
)


class TestDetectOutputFormat:
    """Tests for output format detection."""

    def test_detect_format_yaml_extension(self):
        """Test YAML format detection for .yaml extension."""
        # given
        output_file = Path("test.yaml")

        # when
        result = detect_output_format(output_file)

        # then
        assert result == "yaml"

    def test_detect_format_yml_extension(self):
        """Test YAML format detection for .yml extension."""
        # given
        output_file = Path("test.yml")

        # when
        result = detect_output_format(output_file)

        # then
        assert result == "yaml"

    def test_detect_format_json_extension(self):
        """Test JSON format detection."""
        # given
        output_file = Path("test.json")

        # when
        result = detect_output_format(output_file)

        # then
        assert result == "json"

    def test_detect_format_markdown_extension(self):
        """Test markdown format detection."""
        # given
        output_file = Path("test.md")

        # when
        result = detect_output_format(output_file)

        # then
        assert result == "markdown"

    def test_detect_format_text_default(self):
        """Test default text format for unknown extension."""
        # given
        output_file = Path("test.txt")

        # when
        result = detect_output_format(output_file)

        # then
        assert result == "text"

    def test_detect_format_none_file(self):
        """Test text format when no file provided."""
        # given
        output_file = None

        # when
        result = detect_output_format(output_file)

        # then
        assert result == "text"


class TestFormatOutputContent:
    """Tests for output content formatting."""

    def test_format_structured_yaml(self):
        """Test structured YAML formatting."""
        # given
        data = {"key": "value", "number": 42}
        format_type = "yaml"
        mode = "structured"

        # when
        result = format_output_content(data, format_type, mode)

        # then
        assert isinstance(result, FormattedOutput)
        assert result.format_type == "yaml"
        assert result.display_title == "📋 Structured Output (YAML)"
        assert result.raw_data == data
        assert "key: value" in result.content
        assert "number: 42" in result.content

    def test_format_structured_json(self):
        """Test structured JSON formatting."""
        # given
        data = {"key": "value", "number": 42}
        format_type = "json"
        mode = "structured"

        # when
        result = format_output_content(data, format_type, mode)

        # then
        assert isinstance(result, FormattedOutput)
        assert result.format_type == "json"
        assert result.display_title == "📋 Structured Output (JSON)"
        assert result.raw_data == data
        # Should be formatted JSON
        expected_json = json.dumps(data, indent=2, ensure_ascii=False)
        assert result.content == expected_json

    def test_format_text_content(self):
        """Test text content formatting."""
        # given
        data = "This is plain text content"
        format_type = "text"
        mode = "text"

        # when
        result = format_output_content(data, format_type, mode)

        # then
        assert isinstance(result, FormattedOutput)
        assert result.format_type == "text"
        assert result.display_title == "📝 Text Output"
        assert result.raw_data == data
        assert result.content == data

    def test_format_markdown_content(self):
        """Test markdown content formatting."""
        # given
        data = "# This is markdown\n\n**Bold text**"
        format_type = "markdown"
        mode = "text"

        # when
        result = format_output_content(data, format_type, mode)

        # then
        assert isinstance(result, FormattedOutput)
        assert result.format_type == "markdown"
        assert result.display_title == "📄 Markdown Output"
        assert result.raw_data == data
        assert result.content == data

    def test_format_structured_defaults_to_json(self):
        """Test structured formatting defaults to JSON for unknown format."""
        # given
        data = {"test": "data"}
        format_type = "unknown"
        mode = "structured"

        # when
        result = format_output_content(data, format_type, mode)

        # then
        assert result.format_type == "json"
        assert result.display_title == "📋 Structured Output (JSON)"


class TestDisplayFormattedConsole:
    """Tests for console display functionality."""

    @patch("llm_ci_runner.formatters.CONSOLE")
    def test_display_structured_output(self, mock_console):
        """Test structured output console display."""
        # given
        formatted_output = FormattedOutput(
            content='{"key": "value"}',
            format_type="json",
            display_title="📋 Structured Output (JSON)",
            raw_data={"key": "value"},
        )

        # when
        display_formatted_console(formatted_output)

        # then
        # Should print structured header and panel
        assert mock_console.print.call_count == 2
        header_call = mock_console.print.call_args_list[0][0][0]
        assert "🤖 LLM Response (Structured)" in header_call
        assert "bold cyan" in header_call

    @patch("llm_ci_runner.formatters.CONSOLE")
    def test_display_text_output(self, mock_console):
        """Test text output console display."""
        # given
        formatted_output = FormattedOutput(
            content="Plain text content",
            format_type="text",
            display_title="📝 Text Output",
            raw_data="Plain text content",
        )

        # when
        display_formatted_console(formatted_output)

        # then
        # Should print text header and panel
        assert mock_console.print.call_count == 2
        header_call = mock_console.print.call_args_list[0][0][0]
        assert "🤖 LLM Response (Text)" in header_call
        assert "bold green" in header_call


class TestWriteFormattedFile:
    """Tests for file writing functionality."""

    def test_write_json_file(self):
        """Test writing JSON file with metadata wrapper."""
        # given
        formatted_output = FormattedOutput(
            content='{"key": "value"}',
            format_type="json",
            display_title="📋 Structured Output (JSON)",
            raw_data={"key": "value"},
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "test.json"

            # when
            write_formatted_file(formatted_output, output_file)

            # then
            assert output_file.exists()
            with open(output_file, "r") as f:
                content = json.load(f)

            assert content["success"] is True
            assert content["response"] == {"key": "value"}
            assert "metadata" in content
            assert content["metadata"]["runner"] == "llm-ci-runner"

    def test_write_yaml_file(self):
        """Test writing YAML file with metadata wrapper."""
        # given
        formatted_output = FormattedOutput(
            content="key: value\n",
            format_type="yaml",
            display_title="📋 Structured Output (YAML)",
            raw_data={"key": "value"},
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "test.yaml"

            # when
            write_formatted_file(formatted_output, output_file)

            # then
            assert output_file.exists()
            yaml = YAML(typ="safe", pure=True)
            with open(output_file, "r") as f:
                content = yaml.load(f)

            assert content["success"] is True
            assert content["response"] == {"key": "value"}
            assert "metadata" in content

    def test_write_markdown_file_direct(self):
        """Test writing markdown file without metadata wrapper."""
        # given
        formatted_output = FormattedOutput(
            content="# Markdown content",
            format_type="markdown",
            display_title="📄 Markdown Output",
            raw_data="# Markdown content",
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "test.md"

            # when
            write_formatted_file(formatted_output, output_file)

            # then
            assert output_file.exists()
            with open(output_file, "r") as f:
                content = f.read()

            assert content == "# Markdown content"

    def test_write_markdown_file_with_dict_data(self):
        """Test writing markdown file when raw_data is dict."""
        # given
        formatted_output = FormattedOutput(
            content="# Markdown content",
            format_type="markdown",
            display_title="📄 Markdown Output",
            raw_data={"response": "# Markdown content"},
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "test.md"

            # when
            write_formatted_file(formatted_output, output_file)

            # then
            assert output_file.exists()
            with open(output_file, "r") as f:
                content = f.read()

            assert content == "# Markdown content"

    def test_write_file_creates_directories(self):
        """Test that file writing creates parent directories."""
        # given
        formatted_output = FormattedOutput(
            content='{"test": "data"}',
            format_type="json",
            display_title="📋 Structured Output (JSON)",
            raw_data={"test": "data"},
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "nested" / "path" / "test.json"

            # when
            write_formatted_file(formatted_output, output_file)

            # then
            assert output_file.exists()
            assert output_file.parent.exists()

    def test_write_file_error_handling(self):
        """Test file writing error handling."""
        # given
        formatted_output = FormattedOutput(
            content='{"test": "data"}',
            format_type="json",
            display_title="📋 Structured Output (JSON)",
            raw_data={"test": "data"},
        )

        # Use a path that's guaranteed to be invalid on all platforms
        # Using a path with null bytes which is invalid on all operating systems
        output_file = Path("test\x00file.json")

        # when/then
        with pytest.raises(LLMRunnerError, match="Error writing output file"):
            write_formatted_file(formatted_output, output_file)


class TestYamlRecursivelyForceLiteral:
    """Tests for YAML literal string handling."""

    @pytest.mark.parametrize(
        "input_data,expected_is_literal,expected_is_quoted,description",
        [
            pytest.param(
                "short text",
                False,
                False,
                "Short single-line string should remain regular string",
                id="short_single_line",
            ),
            pytest.param(
                "",
                False,
                False,
                "Empty string should remain unchanged",
                id="empty_string",
            ),
            pytest.param(
                "line1\nline2\nline3",
                True,
                False,
                "Multiline string should become literal scalar",
                id="multiline_string",
            ),
            pytest.param(
                "This is a very long string that definitely exceeds the 80 character threshold and should be formatted as quoted for readability",
                False,
                True,
                "Long single-line string should become double-quoted scalar",
                id="long_single_line",
            ),
            pytest.param(
                "A" * 1000,
                False,
                True,
                "Very long string should become double-quoted scalar",
                id="very_long_string",
            ),
            pytest.param(
                "Long multiline string\nthat has both length over threshold\nand multiple lines for comprehensive testing",
                True,
                False,
                "Long multiline string should become literal (multiline takes precedence)",
                id="long_multiline_both_conditions",
            ),
        ],
    )
    def test_string_literal_formatting_rules(self, input_data, expected_is_literal, expected_is_quoted, description):
        """Test various string types for appropriate scalar formatting rules."""
        # when
        result = yaml_recursively_force_literal(input_data)

        # then
        from ruamel.yaml.scalarstring import LiteralScalarString, DoubleQuotedScalarString

        if expected_is_literal:
            assert isinstance(result, LiteralScalarString), f"Expected literal scalar: {description}"
        elif expected_is_quoted:
            assert isinstance(result, DoubleQuotedScalarString), f"Expected double-quoted scalar: {description}"
        else:
            assert isinstance(result, str) and not isinstance(
                result, (LiteralScalarString, DoubleQuotedScalarString)
            ), f"Expected regular string: {description}"

    @pytest.mark.parametrize(
        "input_data,expected_result,description",
        [
            pytest.param(
                42,
                42,
                "Integer should remain unchanged",
                id="integer",
            ),
            pytest.param(
                3.14,
                3.14,
                "Float should remain unchanged",
                id="float",
            ),
            pytest.param(
                True,
                True,
                "Boolean should remain unchanged",
                id="boolean",
            ),
            pytest.param(
                None,
                None,
                "None should remain unchanged",
                id="none_value",
            ),
        ],
    )
    def test_non_string_types_unchanged(self, input_data, expected_result, description):
        """Test that non-string types remain unchanged."""
        # when
        result = yaml_recursively_force_literal(input_data)

        # then
        assert result == expected_result, description
        assert type(result) == type(expected_result), f"Type should be preserved: {description}"

    @pytest.mark.parametrize(
        "input_data,expected_literal_keys,expected_quoted_keys,description",
        [
            pytest.param(
                {
                    "short": "text",
                    "long": "This is a very long description that exceeds the 80 character threshold and should be quoted",
                },
                [],
                ["long"],
                "Dictionary with mixed string lengths",
                id="dict_mixed_lengths",
            ),
            pytest.param(
                {"multiline": "line1\nline2", "single": "short", "number": 42},
                ["multiline"],
                [],
                "Dictionary with multiline, single-line, and non-string",
                id="dict_mixed_types",
            ),
            pytest.param(
                {
                    "nested": {
                        "short": "text",
                        "long": "This is a very long nested description that exceeds the threshold and should be quoted",
                        "multiline": "a\nb\nc",
                    }
                },
                ["nested.multiline"],
                ["nested.long"],
                "Nested dictionary with various string types",
                id="nested_dict",
            ),
        ],
    )
    def test_dictionary_processing(self, input_data, expected_literal_keys, expected_quoted_keys, description):
        """Test dictionary processing with various content types."""
        # when
        result = yaml_recursively_force_literal(input_data)

        # then
        from ruamel.yaml.scalarstring import LiteralScalarString, DoubleQuotedScalarString

        def check_nested_key(data, key_path):
            keys = key_path.split(".")
            current = data
            for key in keys:
                current = current[key]
            return current

        # Check that expected keys are literal
        for key_path in expected_literal_keys:
            value = check_nested_key(result, key_path)
            assert isinstance(value, LiteralScalarString), f"Key '{key_path}' should be literal in: {description}"

        # Check that expected keys are quoted
        for key_path in expected_quoted_keys:
            value = check_nested_key(result, key_path)
            assert isinstance(value, DoubleQuotedScalarString), f"Key '{key_path}' should be quoted in: {description}"

        # Verify structure is preserved
        assert isinstance(result, dict), f"Result should be dictionary: {description}"

    @pytest.mark.parametrize(
        "input_data,expected_literal_indices,expected_quoted_indices,description",
        [
            pytest.param(
                [
                    "short",
                    "This is a very long string that exceeds the 80 character threshold and should be quoted",
                    "multi\nline",
                ],
                [2],
                [1],
                "List with mixed string types",
                id="list_mixed_strings",
            ),
            pytest.param(
                [
                    "short text",
                    {"nested": "This is a very long nested string that exceeds the threshold and should be quoted"},
                    42,
                    "another short",
                ],
                [],  # The quoted will be in the nested dict, not the list itself
                [],  # The quoted will be in the nested dict, not the list itself
                "List with nested dictionary containing long string",
                id="list_with_nested_dict",
            ),
        ],
    )
    def test_list_processing(self, input_data, expected_literal_indices, expected_quoted_indices, description):
        """Test list processing with various content types."""
        # when
        result = yaml_recursively_force_literal(input_data)

        # then
        from ruamel.yaml.scalarstring import LiteralScalarString, DoubleQuotedScalarString

        assert isinstance(result, list), f"Result should be list: {description}"
        assert len(result) == len(input_data), f"List length should be preserved: {description}"

        # Check expected literal indices
        for i in expected_literal_indices:
            assert isinstance(result[i], LiteralScalarString), f"Index {i} should be literal in: {description}"

        # Check expected quoted indices
        for i in expected_quoted_indices:
            assert isinstance(result[i], DoubleQuotedScalarString), f"Index {i} should be quoted in: {description}"

    def test_complex_nested_structure(self):
        """Test complex nested structure with all data types."""
        # given
        from ruamel.yaml.scalarstring import LiteralScalarString, DoubleQuotedScalarString

        complex_data = {
            "metadata": {
                "short_title": "Brief",
                "long_description": "This is a very comprehensive description that definitely exceeds our 80 character threshold and should be formatted as a quoted scalar for optimal readability in YAML output files.",
            },
            "items": [
                "short item",
                "This is a very long item description that exceeds the threshold and should be quoted formatted",
                {"nested_multi": "line1\nline2\nline3", "nested_short": "brief"},
            ],
            "config": {
                "enabled": True,
                "timeout": 30,
                "multiline_config": "setting1=value1\nsetting2=value2\nsetting3=value3",
            },
        }

        # when
        result = yaml_recursively_force_literal(complex_data)

        # then
        # Long strings should be quoted
        assert isinstance(result["metadata"]["long_description"], DoubleQuotedScalarString)
        assert isinstance(result["items"][1], DoubleQuotedScalarString)
        assert isinstance(result["items"][2]["nested_multi"], LiteralScalarString)
        assert isinstance(result["config"]["multiline_config"], LiteralScalarString)

        # Short strings should remain regular
        assert not isinstance(result["metadata"]["short_title"], (LiteralScalarString, DoubleQuotedScalarString))
        assert not isinstance(result["items"][0], (LiteralScalarString, DoubleQuotedScalarString))
        assert not isinstance(result["items"][2]["nested_short"], (LiteralScalarString, DoubleQuotedScalarString))

        # Non-strings should be unchanged
        assert result["config"]["enabled"] is True
        assert result["config"]["timeout"] == 30

    def test_yaml_output_formatting_integration(self):
        """Integration test showing actual YAML output formatting."""
        # given
        from ruamel.yaml import YAML
        from io import StringIO

        test_data = {
            "short": "Brief text",
            "long": "This is a very long description that exceeds the 80 character threshold and should be formatted as a literal block scalar",
            "multiline": "Line 1\nLine 2\nLine 3",
        }

        # when
        result = yaml_recursively_force_literal(test_data)

        # Format as YAML
        yaml = YAML()
        yaml.indent(mapping=2, sequence=4, offset=2)
        yaml.default_flow_style = False
        yaml.width = 1000

        output = StringIO()
        yaml.dump(result, output)
        yaml_output = output.getvalue()

        # then
        # Should contain literal block indicators for long and multiline content
        assert "|-" in yaml_output, "Should contain literal block scalar indicator"

        # Short text should not have literal formatting
        lines = yaml_output.split("\n")
        short_line = next((line for line in lines if "short:" in line), None)
        assert short_line and "|-" not in short_line, "Short text should not use literal formatting"


class TestFormattedOutputDataclass:
    """Tests for FormattedOutput dataclass."""

    def test_formatted_output_creation(self):
        """Test FormattedOutput dataclass creation."""
        # given
        content = "test content"
        format_type = "json"
        display_title = "Test Title"
        raw_data = {"test": "data"}

        # when
        formatted_output = FormattedOutput(
            content=content, format_type=format_type, display_title=display_title, raw_data=raw_data
        )

        # then
        assert formatted_output.content == content
        assert formatted_output.format_type == format_type
        assert formatted_output.display_title == display_title
        assert formatted_output.raw_data == raw_data

    def test_formatted_output_equality(self):
        """Test FormattedOutput equality comparison."""
        # given
        formatted_output1 = FormattedOutput("content", "json", "title", {"data": "test"})
        formatted_output2 = FormattedOutput("content", "json", "title", {"data": "test"})
        formatted_output3 = FormattedOutput("different", "json", "title", {"data": "test"})

        # when/then
        assert formatted_output1 == formatted_output2
        assert formatted_output1 != formatted_output3
