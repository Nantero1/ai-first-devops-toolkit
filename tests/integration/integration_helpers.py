"""
Integration test helpers and utilities for LLM CI Runner.

This module provides common functionality to reduce code duplication
across integration tests while maintaining readability and test clarity.
"""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any
from unittest.mock import patch

from tenacity import retry, stop_after_delay, wait_fixed

from llm_ci_runner import main


class IntegrationTestHelper:
    """
    Helper class for common integration test patterns.

    Provides reusable methods for file creation, command execution,
    and result validation to reduce code duplication across test files.
    """

    def __init__(self, temp_workspace: Path):
        """Initialize helper with temporary workspace path."""
        self.workspace = temp_workspace
        self.input_dir = temp_workspace / "input"
        self.output_dir = temp_workspace / "output"
        self.schemas_dir = temp_workspace / "schemas"

    def create_input_file(
        self, filename: str, content: dict[str, Any] | None = None, file_format: str = "json"
    ) -> Path:
        """
        Create an input file with standardized content structure.

        Args:
            filename: Name of the file to create
            content: Content to write (uses default if None)
            file_format: Format of the file ('json' or 'yaml')

        Returns:
            Path to the created file
        """
        if content is None:
            content = {
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "This is a test message."},
                ]
            }

        file_path = self.input_dir / filename

        if file_format == "json":
            with open(file_path, "w") as f:
                json.dump(content, f, indent=2)
        elif file_format == "yaml":
            import yaml

            with open(file_path, "w") as f:
                yaml.dump(content, f, default_flow_style=False)
        else:
            raise ValueError(f"Unsupported file format: {file_format}")

        return file_path

    def create_schema_file(self, filename: str, schema: dict[str, Any] | None = None) -> Path:
        """
        Create a schema file with standardized schema structure.

        Args:
            filename: Name of the schema file to create
            schema: Schema content (uses sentiment analysis schema if None)

        Returns:
            Path to the created schema file
        """
        if schema is None:
            schema = {
                "type": "object",
                "properties": {
                    "sentiment": {"type": "string"},
                    "confidence": {"type": "number"},
                    "summary": {"type": "string"},
                    "key_points": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["sentiment", "confidence"],
            }

        schema_path = self.schemas_dir / filename
        with open(schema_path, "w") as f:
            json.dump(schema, f, indent=2)

        return schema_path

    def create_template_file(self, filename: str, template_content: str, template_format: str = "handlebars") -> Path:
        """
        Create a template file with given content.

        Args:
            filename: Name of the template file
            template_content: Template content
            template_format: Format of the template

        Returns:
            Path to the created template file
        """
        if template_format == "handlebars":
            extension = ".hbs"
        elif template_format == "jinja2":
            extension = ".j2"
        elif template_format == "semantic-kernel":
            extension = ".yaml"
        else:
            extension = ".txt"

        template_path = self.input_dir / f"{filename}{extension}"
        with open(template_path, "w") as f:
            f.write(template_content)

        return template_path

    def create_template_vars_file(self, filename: str, variables: dict[str, Any], file_format: str = "yaml") -> Path:
        """
        Create a template variables file.

        Args:
            filename: Name of the variables file
            variables: Variables dictionary
            file_format: Format ('yaml' or 'json')

        Returns:
            Path to the created variables file
        """
        if file_format == "yaml":
            import yaml

            vars_path = self.input_dir / f"{filename}.yaml"
            with open(vars_path, "w") as f:
                yaml.dump(variables, f, default_flow_style=False)
        else:
            vars_path = self.input_dir / f"{filename}.json"
            with open(vars_path, "w") as f:
                json.dump(variables, f, indent=2)

        return vars_path

    def build_cli_args(
        self,
        input_file: str | Path | None = None,
        output_file: str | Path | None = None,
        schema_file: str | Path | None = None,
        template_file: str | Path | None = None,
        template_vars_file: str | Path | None = None,
        log_level: str = "ERROR",
        additional_args: list[str] | None = None,
    ) -> list[str]:
        """
        Build standardized CLI arguments for main() function calls.

        Args:
            input_file: Path to input file
            output_file: Path to output file
            schema_file: Path to schema file (optional)
            template_file: Path to template file (optional)
            template_vars_file: Path to template variables file (optional)
            log_level: Logging level
            additional_args: Additional CLI arguments

        Returns:
            List of CLI arguments ready for sys.argv patching
        """
        args = ["llm-ci-runner"]

        if input_file:
            args.extend(["--input-file", str(input_file)])
        if output_file:
            args.extend(["--output-file", str(output_file)])
        if schema_file:
            args.extend(["--schema-file", str(schema_file)])
        if template_file:
            args.extend(["--template-file", str(template_file)])
        if template_vars_file:
            args.extend(["--template-vars", str(template_vars_file)])

        args.extend(["--log-level", log_level])

        if additional_args:
            args.extend(additional_args)

        return args

    async def execute_main_with_args(self, args: list[str]) -> Path:
        """
        Execute main() function with given CLI arguments.

        Args:
            args: CLI arguments for main() function

        Returns:
            Path to the output file that was created

        Raises:
            Exception: If main() execution fails
        """
        import os

        # Extract output file path from args for return value
        try:
            output_idx = args.index("--output-file") + 1
            output_file = Path(args[output_idx])
        except (ValueError, IndexError) as exc:
            raise ValueError("--output-file argument is required") from exc

        # Store original working directory
        original_cwd = os.getcwd()

        try:
            # Ensure we stay in the project root directory for execution
            # This should match the current working directory when tests run
            project_root = Path(__file__).parent.parent.parent.resolve()

            # Change to project root if not already there
            if Path(original_cwd) != project_root:
                os.chdir(project_root)

            # Execute main with patched sys.argv
            with patch("sys.argv", args):
                await main()

        finally:
            # Restore original working directory
            if os.getcwd() != original_cwd:
                os.chdir(original_cwd)

        return output_file

    async def run_integration_test(
        self,
        input_content: dict[str, Any] | None = None,
        schema_content: dict[str, Any] | None = None,
        input_filename: str = "test_input.json",
        output_filename: str = "test_output.json",
        schema_filename: str | None = None,
        log_level: str = "ERROR",
        additional_args: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Execute a complete integration test with standardized setup.

        Args:
            input_content: Input data (uses default if None)
            schema_content: Schema data (optional)
            input_filename: Name for input file
            output_filename: Name for output file
            schema_filename: Name for schema file (optional)
            log_level: Logging level
            additional_args: Additional CLI arguments

        Returns:
            Dictionary containing the parsed output data
        """
        # Create input file
        input_file = self.create_input_file(input_filename, input_content)
        output_file = self.output_dir / output_filename

        # Create schema file if specified
        schema_file = None
        if schema_filename and schema_content is not None:
            schema_file = self.create_schema_file(schema_filename, schema_content)

        # Build and execute CLI arguments
        args = self.build_cli_args(
            input_file=input_file,
            output_file=output_file,
            schema_file=schema_file,
            log_level=log_level,
            additional_args=additional_args,
        )

        await self.execute_main_with_args(args)

        # Load and return results
        return self.load_output_file(output_file)

    @retry(
        stop=stop_after_delay(10),  # Increase to 10 seconds for debugging
        wait=wait_fixed(0.2),  # Increase wait to 200ms for filesystem sync
        reraise=True,
    )
    def load_output_file(self, output_file: Path) -> dict[str, Any]:
        """
        Load and parse output file content with retry logic and extensive debugging.

        Retries for up to 10 seconds to handle file I/O race conditions
        where the application may still be writing the file when the
        test tries to read it.

        Args:
            output_file: Path to the output file

        Returns:
            Parsed file content as dictionary

        Raises:
            FileNotFoundError: If file doesn't exist after retry timeout
        """
        import os
        import time

        # Extensive debugging for file I/O issues
        current_dir = os.getcwd()
        output_abs_path = output_file.resolve()
        output_parent = output_file.parent.resolve()

        if not output_file.exists():
            # Final attempt: force filesystem sync and wait a bit more
            time.sleep(0.5)  # Additional wait for filesystem sync
            if not output_file.exists():
                raise FileNotFoundError(
                    f"Output file not found after retry timeout: {output_file} (absolute: {output_abs_path})"
                )

        # Additional check: ensure file is not empty and readable
        try:
            file_size = output_file.stat().st_size
            if file_size == 0:
                raise FileNotFoundError(f"Output file exists but is empty (still being written): {output_file}")
        except OSError as e:
            raise FileNotFoundError(f"Cannot access output file: {output_file} - {e}")

        if output_file.suffix.lower() == ".json":
            with open(output_file) as f:
                content = f.read().strip()
                if not content:
                    raise FileNotFoundError(f"Output file exists but content is empty: {output_file}")
                return json.loads(content)
        elif output_file.suffix.lower() in [".yaml", ".yml"]:
            import yaml

            with open(output_file) as f:
                content = f.read().strip()
                if not content:
                    raise FileNotFoundError(f"Output file exists but content is empty: {output_file}")
                return yaml.safe_load(content)
        else:
            # Try JSON first, then YAML as fallback
            try:
                with open(output_file) as f:
                    return json.load(f)
            except json.JSONDecodeError:
                import yaml

                with open(output_file) as f:
                    return yaml.safe_load(f)

    def assert_successful_response(
        self, result: dict[str, Any], expected_response_type: str = "str", expected_content_substring: str | None = None
    ) -> None:
        """
        Assert that the result indicates successful execution.

        Args:
            result: Result dictionary from output file
            expected_response_type: Expected type of response ('str' or 'dict')
            expected_content_substring: Substring that should be in response
        """
        assert result["success"] is True, f"Expected success=True, got {result.get('success')}"
        assert "response" in result, "Response field missing from result"

        if expected_response_type == "str":
            assert isinstance(result["response"], str), f"Expected str response, got {type(result['response'])}"
        elif expected_response_type == "dict":
            assert isinstance(result["response"], dict), f"Expected dict response, got {type(result['response'])}"

        if expected_content_substring:
            response_str = str(result["response"])
            assert expected_content_substring in response_str, (
                f"Expected '{expected_content_substring}' in response, got: {response_str[:200]}..."
            )

    def assert_structured_response(
        self, result: dict[str, Any], required_fields: list[str], expected_values: dict[str, Any] | None = None
    ) -> None:
        """
        Assert that the result contains structured response with required fields.

        Args:
            result: Result dictionary from output file
            required_fields: List of fields that must be present in response
            expected_values: Optional dict of field->expected_value mappings
        """
        self.assert_successful_response(result, expected_response_type="dict")

        response = result["response"]
        for field in required_fields:
            assert field in response, f"Required field '{field}' missing from response"

        if expected_values:
            for field, expected_value in expected_values.items():
                actual_value = response.get(field)
                assert actual_value == expected_value, f"Expected {field}={expected_value}, got {actual_value}"

    def run_cli_subprocess(
        self, args: list[str], capture_output: bool = True, text: bool = True
    ) -> subprocess.CompletedProcess:
        """
        Run CLI command via subprocess for testing CLI interface.

        Args:
            args: Command arguments (without 'uv run' prefix)
            capture_output: Whether to capture stdout/stderr
            text: Whether to return text output

        Returns:
            CompletedProcess result
        """
        # Add 'uv run' prefix for subprocess execution
        full_command = ["uv", "run"] + args
        return subprocess.run(full_command, capture_output=capture_output, text=text)


class CommonTestData:
    """
    Common test data patterns used across integration tests.

    Provides standardized test data to ensure consistency
    and reduce duplication of test input creation.
    """

    @staticmethod
    def simple_chat_input() -> dict[str, Any]:
        """Standard simple chat input for basic testing."""
        return {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is CI/CD?"},
            ]
        }

    @staticmethod
    def code_review_input() -> dict[str, Any]:
        """Standard code review input for PR analysis testing."""
        return {
            "messages": [
                {"role": "system", "content": "You are a code review assistant."},
                {"role": "user", "content": "Review this Python code for potential issues."},
            ],
            "context": {
                "files": [
                    {"name": "main.py", "content": "def hello_world():\n    print('Hello, World!')\n    return True"}
                ]
            },
        }

    @staticmethod
    def sentiment_analysis_input() -> dict[str, Any]:
        """Standard sentiment analysis input for structured output testing."""
        return {"messages": [{"role": "user", "content": "Analyze the sentiment of this customer feedback."}]}

    @staticmethod
    def sentiment_analysis_schema() -> dict[str, Any]:
        """Standard sentiment analysis schema for structured output testing."""
        return {
            "type": "object",
            "properties": {
                "sentiment": {"type": "string", "enum": ["positive", "negative", "neutral"]},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "summary": {"type": "string"},
                "key_points": {"type": "array", "items": {"type": "string"}},
                "reasoning": {"type": "string"},
            },
            "required": ["sentiment", "confidence"],
            "additionalProperties": False,
        }

    @staticmethod
    def code_review_schema() -> dict[str, Any]:
        """Standard code review schema for structured PR analysis."""
        return {
            "type": "object",
            "properties": {
                "overall_rating": {"type": "string", "enum": ["excellent", "good", "needs_improvement", "poor"]},
                "issues": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string"},
                            "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                            "description": {"type": "string"},
                        },
                    },
                },
                "suggestions": {"type": "array", "items": {"type": "string"}},
                "summary": {"type": "string"},
            },
            "required": ["overall_rating", "summary"],
        }

    @staticmethod
    def handlebars_template() -> str:
        """Standard Handlebars template for template testing."""
        return """<message role="system">You are a helpful assistant.</message>
<message role="user">Hello {{name}}! Please analyze: {{data}}</message>"""

    @staticmethod
    def jinja2_template() -> str:
        """Standard Jinja2 template for template testing."""
        return """<message role="system">You are a code review assistant.</message>
<message role="user">
Review these files:
{% for file in files %}
File: {{ file.name }}
Content: {{ file.content }}
{% endfor %}
</message>"""

    @staticmethod
    def semantic_kernel_template() -> str:
        """Standard Semantic Kernel YAML template for SK testing."""
        return """name: test_analyzer
description: Test analysis template
template: |
  Analyze this input: {{$input_text}}
  
  Provide analysis in the specified format.
input_variables:
  - name: input_text
    description: Text to analyze
execution_settings:
  azure_openai:
    temperature: 0.1
    max_tokens: 200"""

    @staticmethod
    def template_variables() -> dict[str, Any]:
        """Standard template variables for template testing."""
        return {
            "name": "Developer",
            "data": "Customer satisfaction ratings: 4.2/5.0",
            "files": [{"name": "test.py", "content": "print('Hello World')"}],
            "input_text": "This is test input for analysis",
        }

    @staticmethod
    def retry_test_input() -> dict[str, Any]:
        """Standard input for retry mechanism testing with invalid JSON scenarios."""
        return {
            "messages": [
                {"role": "system", "content": "You are a sentiment analysis assistant."},
                {"role": "user", "content": "Please analyze the sentiment of this text: 'I love this product!'"},
            ]
        }

    @staticmethod
    def retry_test_schema() -> dict[str, Any]:
        """Standard schema for retry mechanism testing that expects structured output."""
        return {
            "type": "object",
            "properties": {
                "sentiment": {"type": "string", "enum": ["positive", "negative", "neutral"]},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "summary": {"type": "string"},
                "key_points": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["sentiment", "confidence", "summary", "key_points"],
            "additionalProperties": False,
        }

    @staticmethod
    def invalid_json_responses() -> list[dict[str, Any]]:
        """Sample invalid JSON responses that should trigger retry mechanism."""
        return [
            {
                "description": "Truncated JSON object",
                "content": b"{ invalid json response that will trigger retry",
                "expected_error": "json.JSONDecodeError",
            },
            {
                "description": "Incomplete JSON with missing closing",
                "content": b'{"incomplete": "json without closing',
                "expected_error": "json.JSONDecodeError",
            },
            {
                "description": "Malformed JSON with syntax error",
                "content": b'{"key": value_without_quotes, "another": }',
                "expected_error": "json.JSONDecodeError",
            },
            {
                "description": "Empty response that's not valid JSON",
                "content": b"",
                "expected_error": "json.JSONDecodeError",
            },
        ]
