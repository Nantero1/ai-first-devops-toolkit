"""
Integration tests for main() function with proper mocking.

Tests the main() function directly using pytest mocking with respx
instead of subprocess calls or test helper classes in production code.
Uses the Given-When-Then pattern.
"""

import json
from unittest.mock import patch

import pytest

from llm_ci_runner import main


class TestMainFunctionIntegration:
    """Integration tests for main() function with proper HTTP mocking."""

    @pytest.mark.asyncio
    async def test_main_with_simple_text_input(self, mock_azure_openai_responses, temp_dir):
        """Test main() with simple text input and output."""
        # given
        input_file = temp_dir / "test_input.json"
        output_file = temp_dir / "test_output.json"

        # Create test input
        test_data = {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is CI/CD?"},
            ]
        }
        with open(input_file, "w") as f:
            json.dump(test_data, f)

        # Mock command line arguments
        test_args = [
            "llm_ci_runner.py",
            "--input-file",
            str(input_file),
            "--output-file",
            str(output_file),
            "--log-level",
            "ERROR",
        ]

        # when
        with patch("sys.argv", test_args):
            await main()

        # then
        assert output_file.exists()

        # Verify output content
        with open(output_file) as f:
            output_data = json.load(f)

        assert output_data["success"] is True
        assert "response" in output_data
        assert "This is a mock response from the test Azure service" in output_data["response"]

    @pytest.mark.asyncio
    async def test_main_with_structured_output(self, mock_azure_openai_responses, temp_dir):
        """Test main() with structured output schema."""
        # given
        input_file = temp_dir / "test_input.json"
        output_file = temp_dir / "test_output.json"
        schema_file = temp_dir / "test_schema.json"

        # Create test input
        test_data = {"messages": [{"role": "user", "content": "Analyze this sentiment"}]}
        with open(input_file, "w") as f:
            json.dump(test_data, f)

        # Create test schema
        schema_data = {
            "type": "object",
            "properties": {
                "sentiment": {"type": "string"},
                "confidence": {"type": "number"},
                "summary": {"type": "string"},
                "key_points": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["sentiment", "confidence"],
        }
        with open(schema_file, "w") as f:
            json.dump(schema_data, f)

        # Mock command line arguments
        test_args = [
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
        with patch("sys.argv", test_args):
            await main()

        # then
        assert output_file.exists()

        # Verify output content
        with open(output_file) as f:
            output_data = json.load(f)

        assert output_data["success"] is True
        assert "response" in output_data
        assert isinstance(output_data["response"], dict)
        assert "sentiment" in output_data["response"]
        assert "confidence" in output_data["response"]

    @pytest.mark.asyncio
    async def test_main_with_template_file(self, mock_azure_openai_responses, temp_dir):
        """Test main() with Handlebars template file."""
        # given
        template_file = temp_dir / "test_template.hbs"
        vars_file = temp_dir / "test_vars.yaml"
        output_file = temp_dir / "test_output.json"

        # Create test template
        template_content = """<message role="system">You are a helpful assistant.</message>
<message role="user">What is {{technology}}?</message>"""
        with open(template_file, "w") as f:
            f.write(template_content)

        # Create test variables
        vars_content = """technology: CI/CD"""
        with open(vars_file, "w") as f:
            f.write(vars_content)

        # Mock command line arguments
        test_args = [
            "llm_ci_runner.py",
            "--template-file",
            str(template_file),
            "--template-vars",
            str(vars_file),
            "--output-file",
            str(output_file),
            "--log-level",
            "ERROR",
        ]

        # when
        with patch("sys.argv", test_args):
            await main()

        # then
        assert output_file.exists()

        # Verify output content
        with open(output_file) as f:
            output_data = json.load(f)

        assert output_data["success"] is True
        assert "response" in output_data
        assert "This is a mock response from the test Azure service" in output_data["response"]

    @pytest.mark.asyncio
    async def test_main_with_missing_input_file_raises_error(self, mock_azure_openai_responses, temp_dir):
        """Test main() with missing input file raises appropriate error."""
        # given
        input_file = temp_dir / "nonexistent.json"
        output_file = temp_dir / "test_output.json"

        # Mock command line arguments
        test_args = [
            "llm_ci_runner.py",
            "--input-file",
            str(input_file),
            "--output-file",
            str(output_file),
            "--log-level",
            "ERROR",
        ]

        # when/then
        with patch("sys.argv", test_args):
            with pytest.raises(SystemExit) as exc_info:
                await main()

            # Should exit with error code 1
            assert exc_info.value.code == 1

    @pytest.mark.asyncio
    async def test_main_with_yaml_input_and_output(self, mock_azure_openai_responses, temp_dir):
        """Test main() with YAML input and output files."""
        # given
        input_file = temp_dir / "test_input.yaml"
        output_file = temp_dir / "test_output.yaml"

        # Create test input in YAML format
        yaml_content = """
messages:
  - role: system
    content: You are a helpful assistant.
  - role: user
    content: What is DevOps?
context:
  session_id: test-yaml-123
"""
        with open(input_file, "w") as f:
            f.write(yaml_content)

        # Mock command line arguments
        test_args = [
            "llm_ci_runner.py",
            "--input-file",
            str(input_file),
            "--output-file",
            str(output_file),
            "--log-level",
            "ERROR",
        ]

        # when
        with patch("sys.argv", test_args):
            await main()

        # then
        assert output_file.exists()

        # Verify output content (should be YAML)
        with open(output_file) as f:
            content = f.read()

        assert "success: true" in content
        assert "response:" in content
        assert "This is a mock response from the test Azure service" in content


class TestMainFunctionErrorHandling:
    """Test error handling in main() function."""

    @pytest.mark.asyncio
    async def test_main_handles_authentication_error_gracefully(self, temp_dir):
        """Test main() handles authentication errors gracefully."""
        # given
        input_file = temp_dir / "test_input.json"
        output_file = temp_dir / "test_output.json"

        # Create test input
        test_data = {"messages": [{"role": "user", "content": "Test message"}]}
        with open(input_file, "w") as f:
            json.dump(test_data, f)

        # Mock command line arguments with invalid credentials
        test_args = [
            "llm_ci_runner.py",
            "--input-file",
            str(input_file),
            "--output-file",
            str(output_file),
            "--log-level",
            "ERROR",
        ]

        # Clear environment variables to force authentication error
        with patch.dict("os.environ", {}, clear=True):
            with patch("sys.argv", test_args):
                with pytest.raises(SystemExit) as exc_info:
                    await main()

                # Should exit with error code 1
                assert exc_info.value.code == 1

    @pytest.mark.asyncio
    async def test_main_handles_invalid_json_schema_gracefully(self, mock_azure_openai_responses, temp_dir):
        """Test main() handles invalid JSON schema gracefully."""
        # given
        input_file = temp_dir / "test_input.json"
        output_file = temp_dir / "test_output.json"
        schema_file = temp_dir / "invalid_schema.json"

        # Create test input
        test_data = {"messages": [{"role": "user", "content": "Test message"}]}
        with open(input_file, "w") as f:
            json.dump(test_data, f)

        # Create invalid schema file
        with open(schema_file, "w") as f:
            f.write("{ invalid json schema")

        # Mock command line arguments
        test_args = [
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

        # when/then
        with patch("sys.argv", test_args):
            with pytest.raises(SystemExit) as exc_info:
                await main()

            # Should exit with error code 1
            assert exc_info.value.code == 1
