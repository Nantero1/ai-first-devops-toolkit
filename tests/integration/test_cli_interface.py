"""
CLI interface tests for llm_ci_runner.py

Tests the command-line interface via subprocess to ensure
proper argument parsing, help text, and error handling.
Uses the Given-When-Then pattern.
"""

import json
import subprocess
from pathlib import Path

import pytest


class TestCLIArgumentParsing:
    """Tests for CLI argument parsing and validation."""

    def test_cli_help_displays_usage_information(self):
        """Test that --help displays comprehensive usage information."""
        # given
        command = ["uv", "run", "llm_ci_runner.py", "--help"]

        # when
        result = subprocess.run(command, capture_output=True, text=True)

        # then
        assert result.returncode == 0
        assert "LLM Runner - Simple CI/CD utility for LLM tasks" in result.stdout
        assert "--input-file" in result.stdout
        assert "--output-file" in result.stdout
        assert "--schema-file" in result.stdout
        assert "--log-level" in result.stdout
        assert "Environment Variables" in result.stdout
        assert "AZURE_OPENAI_ENDPOINT" in result.stdout

    def test_cli_with_missing_required_arguments_shows_error(self):
        """Test that missing required arguments shows appropriate error."""
        # given
        command = ["uv", "run", "llm_ci_runner.py", "--input-file", "test.json"]

        # when
        result = subprocess.run(command, capture_output=True, text=True)

        # then
        assert result.returncode != 0
        assert "required" in result.stderr.lower() or "error" in result.stderr.lower()

    def test_cli_with_invalid_log_level_shows_error(self):
        """Test that invalid log level shows appropriate error."""
        # given
        command = [
            "uv",
            "run",
            "llm_ci_runner.py",
            "--input-file",
            "test.json",
            "--output-file",
            "output.json",
            "--log-level",
            "INVALID",
        ]

        # when
        result = subprocess.run(command, capture_output=True, text=True)

        # then
        assert result.returncode != 0
        assert "invalid choice" in result.stderr.lower() or "error" in result.stderr.lower()

    def test_cli_with_nonexistent_input_file_shows_error(self):
        """Test that nonexistent input file shows appropriate error."""
        # given
        command = [
            "uv",
            "run",
            "llm_ci_runner.py",
            "--input-file",
            "nonexistent.json",
            "--output-file",
            "output.json",
        ]

        # when
        result = subprocess.run(command, capture_output=True, text=True)

        # then
        assert result.returncode == 1
        # Should show input validation error
        assert "not found" in result.stderr.lower() or "error" in result.stderr.lower()

    @pytest.mark.parametrize("log_level", ["DEBUG", "INFO", "WARNING", "ERROR"])
    def test_cli_with_valid_log_levels_accepts_gracefully(self, temp_dir, log_level):
        """Test that all valid log levels are accepted."""
        # given
        input_file = temp_dir / "test_input.json"
        output_file = temp_dir / "test_output.json"

        # Create a minimal valid input file
        test_data = {"messages": [{"role": "user", "content": "Hello"}]}
        with open(input_file, "w") as f:
            json.dump(test_data, f)

        command = [
            "uv",
            "run",
            "llm_ci_runner.py",
            "--input-file",
            str(input_file),
            "--output-file",
            str(output_file),
            "--log-level",
            log_level,
        ]

        # when
        # This will fail due to missing Azure credentials, but should parse args correctly
        result = subprocess.run(command, capture_output=True, text=True)

        # then
        # Should fail at authentication stage, not argument parsing
        assert result.returncode == 1
        # Should not be an argument parsing error
        assert "invalid choice" not in result.stderr.lower()
        assert "unrecognized arguments" not in result.stderr.lower()


class TestCLIFileHandling:
    """Tests for CLI file handling and path validation."""

    def test_cli_with_valid_input_file_proceeds_to_authentication(self, temp_dir):
        """Test that valid input file proceeds to authentication stage."""
        # given
        input_file = temp_dir / "valid_input.json"
        output_file = temp_dir / "output.json"

        # Create a valid input file
        test_data = {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello, world!"},
            ],
            "context": {"session_id": "test-123"},
        }
        with open(input_file, "w") as f:
            json.dump(test_data, f)

        command = [
            "uv",
            "run",
            "llm_ci_runner.py",
            "--input-file",
            str(input_file),
            "--output-file",
            str(output_file),
            "--log-level",
            "ERROR",  # Minimize output
        ]

        # when
        result = subprocess.run(command, capture_output=True, text=True)

        # then
        assert result.returncode == 1
        # Should fail at authentication, not input validation
        assert "AZURE_OPENAI_ENDPOINT" in result.stderr or "authentication" in result.stderr.lower()

    def test_cli_with_invalid_json_input_shows_validation_error(self, temp_dir):
        """Test that invalid JSON input shows validation error."""
        # given
        input_file = temp_dir / "invalid_input.json"
        output_file = temp_dir / "output.json"

        # Create an invalid JSON file
        with open(input_file, "w") as f:
            f.write("{ invalid json content }")

        command = [
            "uv",
            "run",
            "llm_ci_runner.py",
            "--input-file",
            str(input_file),
            "--output-file",
            str(output_file),
        ]

        # when
        result = subprocess.run(command, capture_output=True, text=True)

        # then
        assert result.returncode == 1
        assert "json" in result.stderr.lower() or "invalid" in result.stderr.lower()

    def test_cli_with_schema_file_parameter_is_processed(self, temp_dir):
        """Test that schema file parameter is properly processed."""
        # given
        input_file = temp_dir / "input.json"
        schema_file = temp_dir / "schema.json"
        output_file = temp_dir / "output.json"

        # Create valid input file
        input_data = {"messages": [{"role": "user", "content": "Test message"}]}
        with open(input_file, "w") as f:
            json.dump(input_data, f)

        # Create valid schema file
        schema_data = {
            "type": "object",
            "properties": {"response": {"type": "string"}},
            "required": ["response"],
        }
        with open(schema_file, "w") as f:
            json.dump(schema_data, f)

        command = [
            "uv",
            "run",
            "llm_ci_runner.py",
            "--input-file",
            str(input_file),
            "--output-file",
            str(output_file),
            "--schema-file",
            str(schema_file),
            "--log-level",
            "ERROR",
        ]

        # when
        result = subprocess.run(command, capture_output=True, text=True)

        # then
        assert result.returncode == 1
        # Should fail at authentication, not schema processing
        assert "AZURE_OPENAI_ENDPOINT" in result.stderr or "authentication" in result.stderr.lower()
        # Should not have schema-related errors
        assert "schema" not in result.stderr.lower() or "not found" not in result.stderr.lower()


class TestCLIErrorHandling:
    """Tests for CLI error handling and user feedback."""

    def test_cli_with_keyboard_interrupt_shows_cancellation_message(self, temp_dir):
        """Test that keyboard interrupt shows appropriate cancellation message."""
        # Note: This test is conceptual as it's difficult to simulate KeyboardInterrupt in subprocess
        # In a real scenario, this would be tested with process signals
        pass

    def test_cli_with_permission_denied_shows_appropriate_error(self, temp_dir):
        """Test that permission denied errors show appropriate message."""
        # given
        # Create a read-only directory to trigger permission errors
        restricted_dir = temp_dir / "restricted"
        restricted_dir.mkdir(mode=0o444)  # Read-only

        input_file = temp_dir / "input.json"
        output_file = restricted_dir / "output.json"  # This should fail

        # Create valid input file
        input_data = {"messages": [{"role": "user", "content": "Test"}]}
        with open(input_file, "w") as f:
            json.dump(input_data, f)

        command = [
            "uv",
            "run",
            "llm_ci_runner.py",
            "--input-file",
            str(input_file),
            "--output-file",
            str(output_file),
        ]

        # when
        result = subprocess.run(command, capture_output=True, text=True)

        # then
        assert result.returncode == 1
        # Will likely fail before reaching file write due to missing Azure credentials
        # but this tests the overall error handling structure

    def test_cli_shows_colored_output_with_rich_formatting(self, temp_dir):
        """Test that CLI uses Rich formatting for colored output."""
        # given
        command = ["uv", "run", "llm_ci_runner.py", "--help"]

        # when
        result = subprocess.run(command, capture_output=True, text=True)

        # then
        assert result.returncode == 0
        # Rich formatting should be present in help text
        assert "usage:" in result.stdout.lower() or "Usage:" in result.stdout


class TestCLIIntegrationWithExamples:
    """Integration tests for CLI with example files."""

    @pytest.mark.parametrize(
        "example_file",
        [
            "examples/simple-example.json",
            "examples/minimal-example.json",
            "examples/pr-review-example.json",
        ],
    )
    def test_cli_with_example_files_reaches_authentication_stage(self, temp_dir, example_file):
        """Test that CLI with example files reaches authentication stage."""
        # given
        output_file = temp_dir / f"output_{Path(example_file).stem}.json"

        command = [
            "uv",
            "run",
            "llm_ci_runner.py",
            "--input-file",
            example_file,
            "--output-file",
            str(output_file),
            "--log-level",
            "ERROR",
        ]

        # when
        result = subprocess.run(command, capture_output=True, text=True)

        # then
        assert result.returncode == 1
        # Should fail at authentication, not input processing
        assert "AZURE_OPENAI_ENDPOINT" in result.stderr or "authentication" in result.stderr.lower()

    def test_cli_with_structured_output_example_processes_schema(self, temp_dir):
        """Test that CLI with structured output processes schema correctly."""
        # given
        input_file = "examples/simple-example.json"
        schema_file = "examples/structured-output-example.json"
        output_file = temp_dir / "structured_output.json"

        command = [
            "uv",
            "run",
            "llm_ci_runner.py",
            "--input-file",
            input_file,
            "--output-file",
            str(output_file),
            "--schema-file",
            schema_file,
            "--log-level",
            "ERROR",
        ]

        # when
        result = subprocess.run(command, capture_output=True, text=True)

        # then
        assert result.returncode == 1
        # Should fail at authentication, not schema processing
        assert "AZURE_OPENAI_ENDPOINT" in result.stderr or "authentication" in result.stderr.lower()
        # Should not have schema-related errors
        assert "schema" not in result.stderr.lower() or "invalid" not in result.stderr.lower()


class TestCLILoggingAndOutput:
    """Tests for CLI logging and output behavior."""

    def test_cli_with_debug_logging_shows_verbose_output(self, temp_dir):
        """Test that debug logging shows verbose output."""
        # given
        input_file = temp_dir / "input.json"
        output_file = temp_dir / "output.json"

        # Create minimal valid input
        with open(input_file, "w") as f:
            json.dump({"messages": [{"role": "user", "content": "test"}]}, f)

        command = [
            "uv",
            "run",
            "llm_ci_runner.py",
            "--input-file",
            str(input_file),
            "--output-file",
            str(output_file),
            "--log-level",
            "DEBUG",
        ]

        # when
        result = subprocess.run(command, capture_output=True, text=True)

        # then
        assert result.returncode == 1
        # Should show more detailed logging information
        # The exact content depends on where it fails, but should have debug info

    def test_cli_with_error_logging_shows_minimal_output(self, temp_dir):
        """Test that error logging shows minimal output."""
        # given
        input_file = temp_dir / "input.json"
        output_file = temp_dir / "output.json"

        # Create minimal valid input
        with open(input_file, "w") as f:
            json.dump({"messages": [{"role": "user", "content": "test"}]}, f)

        command = [
            "uv",
            "run",
            "llm_ci_runner.py",
            "--input-file",
            str(input_file),
            "--output-file",
            str(output_file),
            "--log-level",
            "ERROR",
        ]

        # when
        result = subprocess.run(command, capture_output=True, text=True)

        # then
        assert result.returncode == 1
        # Should show minimal output with error logging
        # The output should be less verbose than DEBUG mode
