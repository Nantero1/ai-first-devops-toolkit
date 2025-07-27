"""
Unit tests for input/output functions in llm_ci_runner.py

Tests load_input_json, write_output_file, and parse_arguments functions
with heavy mocking following the Given-When-Then pattern.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from llm_ci_runner import (
    InputValidationError,
    LLMRunnerError,
    load_input_file,
    load_schema_file,
    parse_arguments,
    write_output_file,
)


class TestLoadInputFile:
    """Tests for load_input_file function."""

    def test_load_valid_input_file(self, temp_input_file):
        """Test loading a valid input JSON file."""
        # given
        input_file = temp_input_file

        # when
        result = load_input_file(input_file)

        # then
        assert isinstance(result, dict)
        assert "messages" in result
        assert isinstance(result["messages"], list)
        assert len(result["messages"]) == 2
        assert result["messages"][0]["role"] == "system"
        assert result["messages"][1]["role"] == "user"

    def test_load_nonexistent_file_raises_error(self):
        """Test that nonexistent file raises InputValidationError."""
        # given
        nonexistent_file = Path("nonexistent.json")

        # when & then
        with pytest.raises(InputValidationError, match="Input file not found"):
            load_input_file(nonexistent_file)

    def test_load_invalid_json_raises_error(self, temp_dir):
        """Test that invalid JSON raises InputValidationError."""
        # given
        invalid_json_file = temp_dir / "invalid.json"
        with open(invalid_json_file, "w") as f:
            f.write("{ invalid json }")

        # when & then
        with pytest.raises(InputValidationError, match="Invalid JSON in input file"):
            load_input_file(invalid_json_file)

    def test_load_file_without_messages_raises_error(self, temp_dir):
        """Test that file without messages field raises InputValidationError."""
        # given
        no_messages_file = temp_dir / "no_messages.json"
        with open(no_messages_file, "w") as f:
            json.dump({"context": {"session_id": "test"}}, f)

        # when & then
        with pytest.raises(InputValidationError, match="Input file must contain 'messages' field"):
            load_input_file(no_messages_file)

    def test_load_file_with_empty_messages_raises_error(self, temp_dir):
        """Test that file with empty messages array raises InputValidationError."""
        # given
        empty_messages_file = temp_dir / "empty_messages.json"
        with open(empty_messages_file, "w") as f:
            json.dump({"messages": []}, f)

        # when & then
        with pytest.raises(InputValidationError, match="'messages' must be a non-empty array"):
            load_input_file(empty_messages_file)

    def test_load_file_with_non_array_messages_raises_error(self, temp_dir):
        """Test that file with non-array messages raises InputValidationError."""
        # given
        non_array_messages_file = temp_dir / "non_array_messages.json"
        with open(non_array_messages_file, "w") as f:
            json.dump({"messages": "not an array"}, f)

        # when & then
        with pytest.raises(InputValidationError, match="'messages' must be a non-empty array"):
            load_input_file(non_array_messages_file)

    def test_load_file_with_context_shows_debug_info(self, temp_input_file, mock_logger):
        """Test that file with context logs debug information."""
        # given
        input_file = temp_input_file

        # when
        result = load_input_file(input_file)

        # then
        assert "context" in result
        # Logger debug should have been called
        mock_logger.debug.assert_called()

    def test_load_file_with_read_error_raises_error(self):
        """Test that file read errors are wrapped in InputValidationError."""
        # given
        error_file = Path("error.json")

        # when & then
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("builtins.open", side_effect=OSError("Permission denied")),
        ):
            with pytest.raises(InputValidationError, match="Error reading input file"):
                load_input_file(error_file)

    def test_load_file_yaml_parsing_error_fallback(self, temp_dir):
        """Test YAML parsing error fallback for non-JSON files."""
        # given
        invalid_yaml_file = temp_dir / "invalid.yaml"
        with open(invalid_yaml_file, "w") as f:
            f.write("invalid: yaml: content: {\nunmatched braces")

        # when & then
        with pytest.raises(InputValidationError, match="Invalid YAML in input file"):
            load_input_file(invalid_yaml_file)

    def test_yaml_message_lists_not_supported(self, temp_dir):
        """Test that YAML message lists are rejected with clear error message."""
        # given
        yaml_file = temp_dir / "input.yaml"
        yaml_content = """
messages:
  - role: system
    content: You are a helpful assistant.
  - role: user
    content: Hello world
context:
  session_id: test-yaml
"""
        with open(yaml_file, "w") as f:
            f.write(yaml_content)

        # when & then
        with pytest.raises(
            InputValidationError, match="YAML message lists are not supported.*JSON format.*SK templates and schemas"
        ):
            load_input_file(yaml_file)

    def test_load_invalid_yaml_raises_error(self, temp_dir):
        """Test that invalid YAML raises InputValidationError."""
        # given
        invalid_yaml_file = temp_dir / "invalid.yaml"
        with open(invalid_yaml_file, "w") as f:
            f.write("messages:\n  - role: user\n    content: test\n  invalid_key: {\n")

        # when & then
        with pytest.raises(InputValidationError, match="Invalid YAML in input file"):
            load_input_file(invalid_yaml_file)

    def test_load_file_with_non_dict_data_raises_error(self, temp_dir):
        """Test that file with non-dict data raises InputValidationError."""
        # given
        non_dict_file = temp_dir / "non_dict.json"
        with open(non_dict_file, "w") as f:
            json.dump(["not", "a", "dict"], f)

        # when & then
        with pytest.raises(InputValidationError, match="Input file must contain a dictionary"):
            load_input_file(non_dict_file)

    def test_load_file_with_invalid_message_structure_raises_error(self, temp_dir):
        """Test that file with invalid message structure raises InputValidationError."""
        # given
        invalid_message_file = temp_dir / "invalid_message.json"
        with open(invalid_message_file, "w") as f:
            json.dump({"messages": [{"role": "user"}]}, f)  # Missing content

        # when & then
        with pytest.raises(InputValidationError, match="Message 0 must have 'content' field"):
            load_input_file(invalid_message_file)

    def test_load_file_with_invalid_role_raises_error(self, temp_dir):
        """Test that file with invalid role raises InputValidationError."""
        # given
        invalid_role_file = temp_dir / "invalid_role.json"
        with open(invalid_role_file, "w") as f:
            json.dump({"messages": [{"role": "invalid", "content": "test"}]}, f)

        # when & then
        with pytest.raises(InputValidationError, match="Message 0 has invalid role 'invalid'"):
            load_input_file(invalid_role_file)

    def test_load_file_with_non_dict_message_raises_error(self, temp_dir):
        """Test that file with non-dict message raises InputValidationError."""
        # given
        non_dict_message_file = temp_dir / "non_dict_message.json"
        with open(non_dict_message_file, "w") as f:
            json.dump({"messages": ["not a dict"]}, f)

        # when & then
        with pytest.raises(InputValidationError, match="Message 0 must be a dictionary"):
            load_input_file(non_dict_message_file)

    def test_load_file_with_missing_role_raises_error(self, temp_dir):
        """Test that file with missing role raises InputValidationError."""
        # given
        missing_role_file = temp_dir / "missing_role.json"
        with open(missing_role_file, "w") as f:
            json.dump({"messages": [{"content": "test"}]}, f)

        # when & then
        with pytest.raises(InputValidationError, match="Message 0 must have 'role' field"):
            load_input_file(missing_role_file)

    def test_load_file_with_unknown_extension_valid_yaml_succeeds(self, temp_dir):
        """Test that unknown extension file with valid YAML loads successfully."""
        # given
        unknown_ext_file = temp_dir / "unknown.txt"
        yaml_content = """
messages:
  - role: system
    content: You are a helpful assistant.
  - role: user
    content: Hello world
"""
        with open(unknown_ext_file, "w") as f:
            f.write(yaml_content)

        # when
        result = load_input_file(unknown_ext_file)

        # then
        assert isinstance(result, dict)
        assert "messages" in result
        assert len(result["messages"]) == 2

    def test_load_file_with_generic_exception_raises_input_validation_error(self):
        """Test that generic exceptions are wrapped in InputValidationError."""
        # given
        error_file = Path("error.json")

        # when & then
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("builtins.open", side_effect=Exception("Generic error")),
        ):
            with pytest.raises(InputValidationError, match="Failed to load input file"):
                load_input_file(error_file)

    def test_load_file_with_input_validation_error_re_raises(self):
        """Test that InputValidationError is re-raised as-is."""
        # given
        error_file = Path("error.json")

        # when & then
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("builtins.open", side_effect=InputValidationError("Original error")),
        ):
            with pytest.raises(InputValidationError, match="Original error"):
                load_input_file(error_file)


class TestWriteOutputFile:
    """Tests for write_output_file function."""

    def test_write_structured_response(self, temp_output_file):
        """Test writing structured response to output file."""
        # given
        output_file = temp_output_file
        response = {
            "sentiment": "neutral",
            "confidence": 0.95,
            "summary": "Test response",
        }

        # when
        write_output_file(output_file, response)

        # then
        assert output_file.exists()
        with open(output_file) as f:
            written_data = json.load(f)

        assert written_data["success"] is True
        assert written_data["response"] == response
        assert "metadata" in written_data
        assert written_data["metadata"]["runner"] == "llm-ci-runner"

    def test_write_text_response(self, temp_output_file):
        """Test writing text response to output file."""
        # given
        output_file = temp_output_file
        response = "This is a simple text response."

        # when
        write_output_file(output_file, response)

        # then
        assert output_file.exists()
        with open(output_file) as f:
            written_data = json.load(f)

        assert written_data["success"] is True
        assert written_data["response"] == response
        assert "metadata" in written_data

    def test_write_creates_parent_directories(self, temp_dir):
        """Test that parent directories are created if they don't exist."""
        # given
        nested_output_file = temp_dir / "nested" / "deep" / "output.json"
        response = "test response"

        # when
        write_output_file(nested_output_file, response)

        # then
        assert nested_output_file.exists()
        assert nested_output_file.parent.exists()

    def test_write_with_file_permission_error_raises_llm_error(self, temp_output_file):
        """Test that file write errors are wrapped in LLMRunnerError."""
        # given
        output_file = temp_output_file
        response = "test response"

        # when & then
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            with pytest.raises(LLMRunnerError, match="Error writing output file"):
                write_output_file(output_file, response)

    def test_write_with_json_serialization_error_raises_llm_error(self, temp_output_file):
        """Test that JSON serialization errors are wrapped in LLMRunnerError."""
        # given
        output_file = temp_output_file
        # Create a response that can't be serialized to JSON
        response = {"key": set([1, 2, 3])}  # sets are not JSON serializable

        # when & then
        with pytest.raises(LLMRunnerError, match="Error writing output file"):
            write_output_file(output_file, response)

    def test_write_yaml_structured_response(self, temp_dir):
        """Test writing structured response to YAML output file."""
        # given
        output_file = temp_dir / "output.yaml"
        response = {
            "sentiment": "neutral",
            "confidence": 0.95,
            "summary": "Test response",
        }

        # when
        write_output_file(output_file, response)

        # then
        assert output_file.exists()
        import yaml

        with open(output_file) as f:
            written_data = yaml.safe_load(f)

        assert written_data["success"] is True
        assert written_data["response"] == response
        assert "metadata" in written_data
        assert written_data["metadata"]["runner"] == "llm-ci-runner"

    def test_write_yaml_text_response(self, temp_dir):
        """Test writing text response to YAML output file."""
        # given
        output_file = temp_dir / "output.yml"  # Test .yml extension too
        response = "This is a simple text response."

        # when
        write_output_file(output_file, response)

        # then
        assert output_file.exists()
        import yaml

        with open(output_file) as f:
            written_data = yaml.safe_load(f)

        assert written_data["success"] is True
        assert written_data["response"] == response
        assert "metadata" in written_data

    def test_write_markdown_direct_text(self, temp_dir):
        """Test writing direct text to markdown file."""
        # given
        output_file = temp_dir / "output.md"
        response = "This is a markdown response."

        # when
        write_output_file(output_file, response)

        # then
        assert output_file.exists()
        with open(output_file, encoding="utf-8") as f:
            content = f.read()
        assert content == "This is a markdown response."

    def test_write_markdown_dict_response(self, temp_dir):
        """Test writing dict response to markdown file extracts text."""
        # given
        output_file = temp_dir / "output.md"
        response = {"response": "This is a dict response.", "other": "data"}

        # when
        write_output_file(output_file, response)

        # then
        assert output_file.exists()
        with open(output_file, encoding="utf-8") as f:
            content = f.read()
        assert content == "This is a dict response."

    def test_write_markdown_dict_without_response_key(self, temp_dir):
        """Test writing dict without response key to markdown file."""
        # given
        output_file = temp_dir / "output.md"
        response = {"data": "test", "value": 123}

        # when
        write_output_file(output_file, response)

        # then
        assert output_file.exists()
        with open(output_file, encoding="utf-8") as f:
            content = f.read()
        assert "test" in content or "123" in content  # Should contain string representation

    def test_write_with_file_permission_error_raises_llm_error(self, temp_dir):
        """Test that file permission errors raise LLMRunnerError."""
        # given
        output_file = temp_dir / "output.json"
        response = {"test": "data"}

        # when & then
        with (
            patch("pathlib.Path.mkdir", side_effect=PermissionError("Permission denied")),
        ):
            with pytest.raises(LLMRunnerError, match="Error writing output file"):
                write_output_file(output_file, response)

    def test_write_with_json_serialization_error_raises_llm_error(self, temp_dir):
        """Test that JSON serialization errors raise LLMRunnerError."""
        # given
        output_file = temp_dir / "output.json"

        # Create a non-serializable object (function objects can't be JSON serialized)
        def non_serializable_function():
            pass

        response = {"test": non_serializable_function}

        # when & then
        with pytest.raises(LLMRunnerError, match="Error writing output file"):
            write_output_file(output_file, response)

    def test_write_with_yaml_serialization_error_raises_llm_error(self, temp_dir):
        """Test that YAML serialization errors raise LLMRunnerError."""
        # given
        output_file = temp_dir / "output.yaml"

        # Create a non-serializable object (function objects can't be YAML serialized)
        def non_serializable_function():
            pass

        response = {"test": non_serializable_function}

        # when & then
        with pytest.raises(LLMRunnerError, match="Error writing output file"):
            write_output_file(output_file, response)


class TestParseArguments:
    """Tests for parse_arguments function."""

    def test_parse_required_arguments(self):
        """Test parsing with only required arguments."""
        # given
        test_args = ["--input-file", "input.json"]  # Only input-file is required

        # when
        with patch("sys.argv", ["llm_ci_runner.py"] + test_args):
            args = parse_arguments()

        # then
        assert args.input_file == Path("input.json")
        assert args.output_file == Path("result.json")  # Default value
        assert args.schema_file is None
        assert args.log_level == "INFO"

    def test_parse_all_arguments(self):
        """Test parsing with all arguments provided."""
        # given
        test_args = [
            "--input-file",
            "input.json",
            "--output-file",
            "output.json",
            "--schema-file",
            "schema.json",
            "--log-level",
            "DEBUG",
        ]

        # when
        with patch("sys.argv", ["llm_ci_runner.py"] + test_args):
            args = parse_arguments()

        # then
        assert args.input_file == Path("input.json")
        assert args.output_file == Path("output.json")
        assert args.schema_file == Path("schema.json")
        assert args.log_level == "DEBUG"

    def test_parse_missing_required_arguments_raises_error(self):
        """Test that missing required arguments raises SystemExit."""
        # given
        test_args = []  # Missing input-file (the only required argument)

        # when & then
        with patch("sys.argv", ["llm_ci_runner.py"] + test_args):
            with pytest.raises(SystemExit):
                parse_arguments()

    @pytest.mark.parametrize("log_level", ["DEBUG", "INFO", "WARNING", "ERROR"])
    def test_parse_valid_log_levels(self, log_level):
        """Test parsing with all valid log levels."""
        # given
        test_args = [
            "--input-file",
            "input.json",
            "--output-file",
            "output.json",
            "--log-level",
            log_level,
        ]

        # when
        with patch("sys.argv", ["llm_ci_runner.py"] + test_args):
            args = parse_arguments()

        # then
        assert args.log_level == log_level

    def test_parse_invalid_log_level_raises_error(self):
        """Test that invalid log level raises SystemExit."""
        # given
        test_args = [
            "--input-file",
            "input.json",
            "--output-file",
            "output.json",
            "--log-level",
            "INVALID",
        ]

        # when & then
        with patch("sys.argv", ["llm_ci_runner.py"] + test_args):
            with pytest.raises(SystemExit):
                parse_arguments()

    def test_parse_with_default_output_file(self):
        """Test parsing with default output file when not specified."""
        # given
        test_args = ["--input-file", "input.json"]  # No output-file specified

        # when
        with patch("sys.argv", ["llm_ci_runner.py"] + test_args):
            args = parse_arguments()

        # then
        assert args.input_file == Path("input.json")
        assert args.output_file == Path("result.json")  # Should use default
        assert args.schema_file is None
        assert args.log_level == "INFO"

    def test_parse_help_argument_raises_system_exit(self):
        """Test that help argument raises SystemExit."""
        # given
        test_args = ["--help"]

        # when & then
        with patch("sys.argv", ["llm_ci_runner.py"] + test_args):
            with pytest.raises(SystemExit):
                parse_arguments()

    def test_parse_template_arguments(self):
        """Test parsing template-related arguments."""
        # given - use handlebars template which allows external schema
        test_args = [
            "--template-file",
            "template.hbs",
            "--template-vars",
            "vars.json",
            "--schema-file",
            "schema.yaml",
        ]

        # when
        with patch("sys.argv", ["llm_ci_runner.py"] + test_args):
            args = parse_arguments()

        # then
        assert args.template_file == Path("template.hbs")
        assert args.template_vars == Path("vars.json")
        assert args.input_file is None
        assert args.schema_file == Path("schema.yaml")

    def test_parse_template_file_without_vars_is_allowed(self):
        """Test that template-file without template-vars is now allowed (optional)."""
        # given
        test_args = ["--template-file", "template.yaml"]  # No template-vars (optional)

        # when
        with patch("sys.argv", ["llm_ci_runner.py"] + test_args):
            args = parse_arguments()

        # then
        assert args.template_file == Path("template.yaml")
        assert args.template_vars is None  # Should be None when not provided
        assert args.input_file is None

    def test_parse_sk_yaml_template_with_schema_file_raises_error(self):
        """Test that SK YAML templates cannot use external schema files."""
        # given - SK YAML template with schema file (should fail)
        test_args = [
            "--template-file",
            "template.yaml",
            "--schema-file",
            "schema.yaml",
        ]

        # when & then
        with patch("sys.argv", ["llm_ci_runner.py"] + test_args):
            with pytest.raises(SystemExit):
                parse_arguments()

    def test_parse_mutually_exclusive_input_methods_raises_error(self):
        """Test that providing both input-file and template-file raises error."""
        # given
        test_args = [
            "--input-file",
            "input.json",
            "--template-file",
            "template.yaml",
            "--template-vars",
            "vars.json",
        ]

        # when & then
        with patch("sys.argv", ["llm_ci_runner.py"] + test_args):
            with pytest.raises(SystemExit):
                parse_arguments()


class TestYAMLRecursivelyForceLiteral:
    """Tests for yaml_recursively_force_literal function to improve coverage."""

    def test_yaml_recursively_force_literal_dict(self):
        """Test yaml_recursively_force_literal with dictionary."""
        # given
        data = {"key": "value", "nested": {"inner": "data"}}

        # when
        from llm_ci_runner.formatters import yaml_recursively_force_literal

        result = yaml_recursively_force_literal(data)

        # then
        assert result == data

    def test_yaml_recursively_force_literal_list(self):
        """Test yaml_recursively_force_literal with list."""
        # given
        data = ["item1", "item2", ["nested", "list"]]

        # when
        from llm_ci_runner.formatters import yaml_recursively_force_literal

        result = yaml_recursively_force_literal(data)

        # then
        assert result == data

    def test_yaml_recursively_force_literal_multiline_string(self):
        """Test yaml_recursively_force_literal with multiline string."""
        # given
        data = "line1\nline2\nline3"

        # when
        from llm_ci_runner.formatters import yaml_recursively_force_literal

        result = yaml_recursively_force_literal(data)

        # then
        from ruamel.yaml import scalarstring

        assert isinstance(result, scalarstring.LiteralScalarString)
        assert str(result) == data

    def test_yaml_recursively_force_literal_single_line_string(self):
        """Test yaml_recursively_force_literal with single line string."""
        # given
        data = "single line string"

        # when
        from llm_ci_runner.formatters import yaml_recursively_force_literal

        result = yaml_recursively_force_literal(data)

        # then
        assert result == data  # Should not be converted to LiteralScalarString

    def test_yaml_recursively_force_literal_nested_multiline(self):
        """Test yaml_recursively_force_literal with nested multiline strings."""
        # given
        data = {
            "description": "line1\nline2",
            "items": ["item1", "item2\nitem3"],
            "nested": {"text": "nested\nmultiline"},
        }

        # when
        from llm_ci_runner.formatters import yaml_recursively_force_literal

        result = yaml_recursively_force_literal(data)

        # then
        from ruamel.yaml import scalarstring

        assert isinstance(result["description"], scalarstring.LiteralScalarString)
        assert isinstance(result["items"][1], scalarstring.LiteralScalarString)
        assert isinstance(result["nested"]["text"], scalarstring.LiteralScalarString)
        assert result["items"][0] == "item1"  # Single line should not be converted


class TestLoadSchemaFile:
    """Tests for schema file loading functionality."""

    def test_load_schema_file_invalid_dict_content(self, temp_dir):
        """Test schema file with non-dict content raises validation error."""
        # given - schema file with list instead of dict (covers line 359)
        invalid_schema_file = temp_dir / "invalid_schema.json"
        with open(invalid_schema_file, "w") as f:
            json.dump(["not", "a", "dict"], f)

        # when & then
        with pytest.raises(InputValidationError, match="Schema file must contain a dictionary"):
            load_schema_file(invalid_schema_file)

    def test_load_schema_file_json_decode_error(self, temp_dir):
        """Test schema file with invalid JSON raises decode error."""
        # given - schema file with invalid JSON (covers line 371)
        invalid_json_file = temp_dir / "invalid.json"
        with open(invalid_json_file, "w") as f:
            f.write('{"invalid": json content')

        # when & then
        with pytest.raises(InputValidationError, match="Invalid JSON in schema file"):
            load_schema_file(invalid_json_file)

    def test_load_schema_file_generic_error(self, temp_dir):
        """Test schema file loading with generic error handling."""
        # given - non-existent schema file (covers line 372)
        non_existent_file = temp_dir / "does_not_exist.json"

        # when & then
        with pytest.raises(InputValidationError, match="Schema file not found"):
            load_schema_file(non_existent_file)


class TestArgumentValidation:
    """Tests for CLI argument validation edge cases."""

    def test_parse_arguments_template_and_input_conflict(self):
        """Test that template and input file conflict raises parser error."""
        # given - arguments with both template and input file (covers line 106)
        import sys
        from unittest.mock import patch

        test_args = ["prog", "--template-file", "template.hbs", "--input-file", "input.json"]
        with patch.object(sys, "argv", test_args):
            with pytest.raises(SystemExit):  # argparse raises SystemExit on error
                parse_arguments()
