"""
CLI interface integration tests.

Tests the command-line interface for argument parsing, file handling,
and workflow validation using a subprocess-based approach.
"""

from __future__ import annotations

import pytest

try:
    from integration_helpers import CommonTestData
except ImportError:
    from tests.integration.integration_helpers import CommonTestData


class TestCLIArgumentParsing:
    """Tests for CLI argument parsing and validation."""

    def test_cli_with_missing_required_arguments_shows_error(self, integration_helper):
        """Test that missing required arguments shows appropriate error."""
        # given
        command = ["llm-ci-runner", "--input-file"]

        # when
        result = integration_helper.run_cli_subprocess(command)

        # then
        assert result.returncode == 2  # ArgumentParser error
        assert "expected one argument" in result.stderr.lower() or "error" in result.stderr.lower()

    def test_cli_with_invalid_log_level_shows_error(self, integration_helper):
        """Test that invalid log level shows appropriate error."""
        # given
        command = integration_helper.build_cli_args(
            input_file="test.json", output_file="output.json", log_level="INVALID"
        )

        # when
        result = integration_helper.run_cli_subprocess(command)

        # then
        assert result.returncode != 0
        assert "invalid choice" in result.stderr.lower() or "error" in result.stderr.lower()

    def test_cli_with_nonexistent_input_file_shows_error(self, integration_helper):
        """Test that nonexistent input file shows appropriate error."""
        # given
        command = integration_helper.build_cli_args(input_file="nonexistent.json", output_file="output.json")

        # when
        result = integration_helper.run_cli_subprocess(command)

        # then
        assert result.returncode == 1
        assert "not found" in result.stdout.lower() or "error" in result.stdout.lower()

    @pytest.mark.parametrize("log_level", ["DEBUG", "INFO", "WARNING", "ERROR"])
    def test_cli_with_valid_log_levels_accepts_gracefully(self, integration_helper, log_level):
        """Test that all valid log levels are accepted by argument parser."""
        # given
        input_file = integration_helper.create_input_file("test_input.json", CommonTestData.simple_chat_input())
        output_file = integration_helper.output_dir / "test_output.json"

        command = integration_helper.build_cli_args(input_file=input_file, output_file=output_file, log_level=log_level)

        # when
        result = integration_helper.run_cli_subprocess(command)

        # then
        # Should fail with authentication error (exit code 1), not argument parsing error (exit code 2)
        assert result.returncode == 1  # Authentication failure, not argument parsing
        assert "invalid choice" not in result.stderr.lower()
        assert "unrecognized arguments" not in result.stderr.lower()


class TestCLIFileHandling:
    """Tests for CLI file handling and path validation."""

    def test_cli_with_valid_input_file_proceeds_to_authentication(self, integration_helper):
        """Test that valid input file proceeds to authentication stage."""
        # given
        input_content = CommonTestData.simple_chat_input()
        input_content["context"] = {"session_id": "test-123"}

        input_file = integration_helper.create_input_file("valid_input.json", input_content)
        output_file = integration_helper.output_dir / "output.json"

        command = integration_helper.build_cli_args(input_file=input_file, output_file=output_file, log_level="ERROR")

        # when
        result = integration_helper.run_cli_subprocess(command)

        # then
        assert result.returncode == 1  # Authentication error, not parsing error
        assert "unrecognized arguments" not in result.stderr.lower()
        assert (
            "azure" in result.stdout.lower()
            or "endpoint" in result.stdout.lower()
            or "authentication" in result.stdout.lower()
        )

    def test_cli_with_invalid_json_input_shows_validation_error(self, integration_helper):
        """Test that invalid JSON input shows validation error."""
        # given
        input_file = integration_helper.input_dir / "invalid_input.json"
        output_file = integration_helper.output_dir / "output.json"

        # Create an invalid JSON file
        with open(input_file, "w") as f:
            f.write("{ invalid json content")

        command = integration_helper.build_cli_args(input_file=input_file, output_file=output_file)

        # when
        result = integration_helper.run_cli_subprocess(command)

        # then
        assert result.returncode == 1
        assert "json" in result.stdout.lower() or "invalid" in result.stdout.lower()

    def test_cli_with_schema_file_parameter_is_processed(self, integration_helper):
        """Test that schema file parameter is properly processed."""
        # given
        input_file = integration_helper.create_input_file("input.json", CommonTestData.sentiment_analysis_input())
        schema_file = integration_helper.create_schema_file("schema.json", CommonTestData.sentiment_analysis_schema())
        output_file = integration_helper.output_dir / "output.json"

        command = integration_helper.build_cli_args(
            input_file=input_file, output_file=output_file, schema_file=schema_file, log_level="ERROR"
        )

        # when
        result = integration_helper.run_cli_subprocess(command)

        # then
        # Should reach authentication stage (confirms schema parsing worked)
        assert result.returncode == 1  # Authentication failure
        assert "azure" in result.stdout.lower() or "authentication" in result.stdout.lower()


class TestCLITemplateWorkflows:
    """Tests for CLI template workflow handling."""

    def test_cli_with_handlebars_template_workflow(self, integration_helper):
        """Test CLI with Handlebars template and variables files."""
        # given
        template_file = integration_helper.create_template_file(
            "test_template", CommonTestData.handlebars_template(), "handlebars"
        )
        vars_file = integration_helper.create_template_vars_file(
            "test_vars", CommonTestData.template_variables(), "yaml"
        )
        output_file = integration_helper.output_dir / "output.json"

        command = integration_helper.build_cli_args(
            template_file=template_file, template_vars_file=vars_file, output_file=output_file, log_level="ERROR"
        )

        # when
        result = integration_helper.run_cli_subprocess(command)

        # then
        # Should reach authentication stage (confirms template parsing worked)
        assert result.returncode == 1  # Authentication failure
        assert "azure" in result.stdout.lower() or "authentication" in result.stdout.lower()

    def test_cli_with_jinja2_template_workflow(self, integration_helper):
        """Test CLI with Jinja2 template workflow."""
        # given
        template_file = integration_helper.create_template_file(
            "jinja_template", CommonTestData.jinja2_template(), "jinja2"
        )
        vars_file = integration_helper.create_template_vars_file(
            "jinja_vars", CommonTestData.template_variables(), "json"
        )
        output_file = integration_helper.output_dir / "output.json"

        command = integration_helper.build_cli_args(
            template_file=template_file, template_vars_file=vars_file, output_file=output_file, log_level="ERROR"
        )

        # when
        result = integration_helper.run_cli_subprocess(command)

        # then
        assert result.returncode == 1  # Authentication failure
        assert "azure" in result.stdout.lower() or "authentication" in result.stdout.lower()

    def test_cli_with_semantic_kernel_template_workflow(self, integration_helper):
        """Test CLI with Semantic Kernel YAML template workflow."""
        # given
        template_file = integration_helper.create_template_file(
            "sk_template", CommonTestData.semantic_kernel_template(), "semantic-kernel"
        )
        vars_file = integration_helper.create_template_vars_file(
            "sk_vars", {"input_text": "Test analysis content"}, "yaml"
        )
        output_file = integration_helper.output_dir / "output.yaml"

        command = integration_helper.build_cli_args(
            template_file=template_file, template_vars_file=vars_file, output_file=output_file, log_level="ERROR"
        )

        # when
        result = integration_helper.run_cli_subprocess(command)

        # then
        assert result.returncode == 1  # Authentication failure
        assert "azure" in result.stdout.lower() or "authentication" in result.stdout.lower()


class TestCLIErrorHandling:
    """Tests for CLI error handling and user feedback."""

    @pytest.mark.parametrize(
        "input_format,output_format",
        [
            pytest.param("json", "json", id="json_to_json"),
            pytest.param("json", "yaml", id="json_to_yaml"),
            pytest.param("yaml", "json", id="yaml_to_json"),
            pytest.param("yaml", "yaml", id="yaml_to_yaml"),
        ],
    )
    def test_cli_with_format_combinations_parametrized(self, integration_helper, input_format, output_format):
        """Test CLI with various input/output format combinations using parametrization."""
        # given
        input_content = CommonTestData.simple_chat_input()
        input_file = integration_helper.create_input_file(
            f"test_input.{input_format}", input_content, file_format=input_format
        )
        output_file = integration_helper.output_dir / f"test_output.{output_format}"

        command = integration_helper.build_cli_args(input_file=input_file, output_file=output_file, log_level="ERROR")

        # when
        result = integration_helper.run_cli_subprocess(command)

        # then
        # Should reach authentication (confirms format parsing worked)
        assert result.returncode == 1  # Authentication failure
        assert "unrecognized arguments" not in result.stderr.lower()

    @pytest.mark.parametrize(
        "scenario_name,command_args,expected_code,expected_text",
        [
            pytest.param(
                "missing_input_file",
                {"input_file": "nonexistent.json", "output_file": "out.json"},
                1,
                "not found",
                id="file_not_found_error",
            ),
            pytest.param(
                "invalid_log_level",
                {"input_file": "test.json", "output_file": "out.json", "log_level": "INVALID"},
                2,
                "invalid choice",
                id="invalid_log_level_error",
            ),
        ],
    )
    def test_cli_comprehensive_error_scenarios_parametrized(
        self, integration_helper, scenario_name, command_args, expected_code, expected_text
    ):
        """Test various error scenarios with consistent error handling using parametrization."""
        # given
        command = integration_helper.build_cli_args(**command_args)

        # when
        result = integration_helper.run_cli_subprocess(command)

        # then
        assert result.returncode == expected_code, f"Failed scenario: {scenario_name}"
        output_text = (result.stdout + result.stderr).lower()
        assert expected_text in output_text, f"Failed scenario: {scenario_name}"


# =====================
# CLI Return Code Table
# =====================
# | Scenario                                 | Return Code | Notes                                      |
# |-------------------------------------------|-------------|--------------------------------------------|
# | Valid input, all required args present    |     0       | Output file created, CLI succeeds          |
# | Missing required argument (argparse)      |     2       | Argparse error, help/usage shown           |
# | Input file not found                      |     1       | Custom error, message in stdout            |
# | Invalid JSON input                        |     1       | Custom error, message in stdout            |
# | Invalid log level                         |     2       | Argparse error, help/usage shown           |
# | Invalid schema file                       |     1       | Custom error, message in stdout            |
# | Any other handled error                   |     1       | Custom error, message in stdout            |
# | Unhandled exception                       |     1       | Stack trace, message in stdout             |
#
# See test cases above for examples.
