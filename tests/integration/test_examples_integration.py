"""
Integration tests for all example files in llm_ci_runner.py

Tests the full pipeline with real file operations and JSON parsing,
but mocked LLM service calls. Uses minimal mocking following the
Given-When-Then pattern.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from llm_ci_runner import main
from tests.mock_factory import (
    create_hbs_template_mock,
    create_jinja2_template_mock,
    create_minimal_response_mock,
    create_pr_review_mock,
    create_structured_output_mock,
    create_text_output_mock,
)


class TestSimpleExampleIntegration:
    """Integration tests for simple-example.json."""

    @pytest.mark.asyncio
    async def test_simple_example_with_text_output(self, temp_integration_workspace, integration_mock_azure_service):
        """Test simple example with text output (no schema)."""
        # given
        input_file = Path("tests/integration/data/simple-chat/input.json")
        output_file = temp_integration_workspace / "output" / "simple_text_output.json"

        # Mock the Azure service response
        mock_response = create_text_output_mock()
        integration_mock_azure_service.get_chat_message_contents.return_value = mock_response

        # when
        with patch(
            "llm_ci_runner.core.setup_llm_service",
            return_value=(integration_mock_azure_service, None),
        ):
            test_args = [
                "llm-ci-runner",
                "--input-file",
                str(input_file),
                "--output-file",
                str(output_file),
                "--log-level",
                "INFO",
            ]

            with patch("sys.argv", test_args):
                await main()

        # then
        assert output_file.exists()
        with open(output_file) as f:
            result = json.load(f)

        assert result["success"] is True
        assert isinstance(result["response"], str)
        assert "CI/CD stands for" in result["response"]
        assert "metadata" in result
        integration_mock_azure_service.get_chat_message_contents.assert_called_once()

    @pytest.mark.asyncio
    async def test_simple_example_with_structured_output(
        self, temp_integration_workspace, integration_mock_azure_service
    ):
        """Test simple example with structured output schema."""
        # given
        input_file = Path("tests/integration/data/simple-chat/input.json")
        schema_file = Path("tests/integration/data/sentiment-analysis/schema.json")
        output_file = temp_integration_workspace / "output" / "simple_structured_output.json"

        # Mock the Azure service response
        mock_response = create_structured_output_mock()
        integration_mock_azure_service.get_chat_message_contents.return_value = mock_response

        # when
        with patch(
            "llm_ci_runner.core.setup_llm_service",
            return_value=(integration_mock_azure_service, None),
        ):
            test_args = [
                "llm_ci_runner.py",
                "--input-file",
                str(input_file),
                "--output-file",
                str(output_file),
                "--schema-file",
                str(schema_file),
                "--log-level",
                "INFO",
            ]

            with patch("sys.argv", test_args):
                await main()

        # then
        assert output_file.exists()
        with open(output_file) as f:
            result = json.load(f)

        assert result["success"] is True
        assert isinstance(result["response"], dict)
        assert result["response"]["sentiment"] == "neutral"
        assert result["response"]["confidence"] == 0.95
        assert "key_points" in result["response"]
        assert "summary" in result["response"]
        integration_mock_azure_service.get_chat_message_contents.assert_called_once()


class TestPRReviewExampleIntegration:
    """Integration tests for pr-review-example.json."""

    @pytest.mark.asyncio
    async def test_pr_review_example_with_text_output(self, temp_integration_workspace, integration_mock_azure_service):
        """Test PR review example with text output."""
        # given
        input_file = Path("tests/integration/data/code-review/input.json")
        output_file = temp_integration_workspace / "output" / "pr_review_output.json"

        # Mock the Azure service response
        mock_response = create_pr_review_mock()
        integration_mock_azure_service.get_chat_message_contents.return_value = mock_response

        # when
        with patch(
            "llm_ci_runner.core.setup_llm_service",
            return_value=(integration_mock_azure_service, None),
        ):
            test_args = [
                "llm_ci_runner.py",
                "--input-file",
                str(input_file),
                "--output-file",
                str(output_file),
                "--log-level",
                "DEBUG",
            ]

            with patch("sys.argv", test_args):
                await main()

        # then
        assert output_file.exists()
        with open(output_file) as f:
            result = json.load(f)

        assert result["success"] is True
        assert isinstance(result["response"], str)
        assert "Code Review Summary" in result["response"]
        assert "SQL injection" in result["response"]
        assert "security" in result["response"].lower()
        integration_mock_azure_service.get_chat_message_contents.assert_called_once()

    @pytest.mark.asyncio
    async def test_pr_review_example_with_code_review_schema(
        self, temp_integration_workspace, integration_mock_azure_service
    ):
        """Test PR review example with code review schema."""
        # given
        input_file = Path("tests/integration/data/code-review/input.json")
        schema_file = Path("tests/integration/data/code-review/schema.json")
        output_file = temp_integration_workspace / "output" / "pr_review_structured_output.json"

        # Create a mock structured response that matches the code review schema
        mock_response = [create_text_output_mock()[0]]
        # Update the content to be valid JSON matching the schema
        structured_pr_response = json.dumps(
            {
                "overall_rating": "approved_with_comments",
                "security_issues": [
                    {
                        "severity": "high",
                        "description": "SQL injection vulnerability",
                        "location": "line 42",
                        "recommendation": "Use parameterized queries",
                    }
                ],
                "code_quality_issues": [
                    {
                        "severity": "medium",
                        "description": "Missing error handling",
                        "location": "line 15",
                        "recommendation": "Add try-catch block",
                    }
                ],
                "positive_aspects": [
                    "Good use of parameterized queries",
                    "Consistent code style",
                ],
                "recommendations": ["Add unit tests", "Consider adding logging"],
                "summary": "PR addresses security vulnerability but needs minor improvements",
            }
        )
        mock_response[0].content = structured_pr_response
        integration_mock_azure_service.get_chat_message_contents.return_value = mock_response

        # when
        with patch(
            "llm_ci_runner.core.setup_llm_service",
            return_value=(integration_mock_azure_service, None),
        ):
            test_args = [
                "llm_ci_runner.py",
                "--input-file",
                str(input_file),
                "--output-file",
                str(output_file),
                "--schema-file",
                str(schema_file),
                "--log-level",
                "DEBUG",
            ]

            with patch("sys.argv", test_args):
                await main()

        # then
        assert output_file.exists()
        with open(output_file) as f:
            result = json.load(f)

        assert result["success"] is True
        assert isinstance(result["response"], dict)
        assert result["response"]["overall_rating"] == "approved_with_comments"
        assert len(result["response"]["security_issues"]) > 0
        assert result["response"]["security_issues"][0]["severity"] == "high"
        integration_mock_azure_service.get_chat_message_contents.assert_called_once()


class TestMinimalExampleIntegration:
    """Integration tests for minimal-example.json."""

    @pytest.mark.asyncio
    async def test_minimal_example_with_text_output(self, temp_integration_workspace, integration_mock_azure_service):
        """Test minimal example with simple greeting."""
        # given
        input_file = Path("tests/integration/data/simple-chat/input.json")  # Using simple-chat for minimal test
        output_file = temp_integration_workspace / "output" / "minimal_output.json"

        # Mock the Azure service response
        mock_response = create_minimal_response_mock()
        integration_mock_azure_service.get_chat_message_contents.return_value = mock_response

        # when
        with patch(
            "llm_ci_runner.core.setup_llm_service",
            return_value=(integration_mock_azure_service, None),
        ):
            test_args = [
                "llm_ci_runner.py",
                "--input-file",
                str(input_file),
                "--output-file",
                str(output_file),
                "--log-level",
                "WARNING",
            ]

            with patch("sys.argv", test_args):
                await main()

        # then
        assert output_file.exists()
        with open(output_file) as f:
            result = json.load(f)

        assert result["success"] is True
        assert isinstance(result["response"], str)
        assert "ready to help" in result["response"].lower()
        integration_mock_azure_service.get_chat_message_contents.assert_called_once()


class TestAllExamplesEndToEnd:
    """End-to-end tests for all examples together."""

    @pytest.mark.asyncio
    async def test_all_examples_process_successfully(self, temp_integration_workspace, integration_mock_azure_service):
        """Test that all examples can be processed successfully."""
        # given
        examples = [
            ("tests/integration/data/simple-chat/input.json", create_text_output_mock),
            ("tests/integration/data/code-review/input.json", create_pr_review_mock),
            (
                "tests/integration/data/simple-chat/input.json",
                create_minimal_response_mock,
            ),  # Using simple-chat for minimal test
        ]

        results = []

        # when
        for i, (input_file, mock_factory) in enumerate(examples):
            output_file = temp_integration_workspace / "output" / f"test_{i}_output.json"
            mock_response = mock_factory()
            integration_mock_azure_service.get_chat_message_contents.return_value = mock_response

            with patch(
                "llm_ci_runner.core.setup_llm_service",
                return_value=(integration_mock_azure_service, None),
            ):
                test_args = [
                    "llm_ci_runner.py",
                    "--input-file",
                    str(input_file),
                    "--output-file",
                    str(output_file),
                    "--log-level",
                    "ERROR",  # Minimal logging for speed
                ]

                with patch("sys.argv", test_args):
                    await main()

            # Verify output
            assert output_file.exists()
            with open(output_file) as f:
                result = json.load(f)
            results.append(result)

        # then
        assert len(results) == 3
        for result in results:
            assert result["success"] is True
            assert "response" in result
            assert "metadata" in result

        # Verify all service calls were made
        assert integration_mock_azure_service.get_chat_message_contents.call_count == 3

    @pytest.mark.asyncio
    async def test_example_with_nonexistent_input_file_raises_error(
        self, temp_integration_workspace, integration_mock_azure_service
    ):
        """Test that nonexistent input file raises appropriate error."""
        # given
        input_file = Path("tests/integration/data/nonexistent.json")
        output_file = temp_integration_workspace / "output" / "error_output.json"

        # when & then
        with patch(
            "llm_ci_runner.core.setup_llm_service",
            return_value=(integration_mock_azure_service, None),
        ):
            test_args = [
                "llm_ci_runner.py",
                "--input-file",
                str(input_file),
                "--output-file",
                str(output_file),
                "--log-level",
                "ERROR",
            ]

            with patch("sys.argv", test_args):
                with pytest.raises(SystemExit) as exc_info:
                    await main()

                assert exc_info.value.code == 1

    @pytest.mark.asyncio
    async def test_example_with_invalid_schema_file_raises_error(
        self, temp_integration_workspace, integration_mock_azure_service
    ):
        """Test that invalid schema file raises appropriate error."""
        # given
        input_file = Path("tests/integration/data/simple-chat/input.json")
        schema_file = Path("tests/integration/data/nonexistent_schema.json")
        output_file = temp_integration_workspace / "output" / "error_output.json"

        # when & then
        with patch(
            "llm_ci_runner.core.setup_llm_service",
            return_value=(integration_mock_azure_service, None),
        ):
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

            with patch("sys.argv", test_args):
                with pytest.raises(SystemExit) as exc_info:
                    await main()

                assert exc_info.value.code == 1


class TestFullPipelineIntegration:
    """Integration tests for the full pipeline with real file operations."""

    @pytest.mark.asyncio
    async def test_full_pipeline_with_context_processing(
        self, temp_integration_workspace, integration_mock_azure_service
    ):
        """Test the full pipeline including context processing."""
        # given
        # Create a test input file with complex context
        input_data = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that analyzes software development topics.",
                },
                {
                    "role": "user",
                    "content": "Explain the benefits of microservices architecture.",
                    "name": "architect",
                },
            ],
            "context": {
                "session_id": "integration-test-123",
                "metadata": {
                    "task_type": "architecture_analysis",
                    "domain": "software_engineering",
                    "complexity": "intermediate",
                },
                "user_preferences": {
                    "detail_level": "comprehensive",
                    "include_examples": True,
                },
            },
        }

        input_file = temp_integration_workspace / "input" / "complex_input.json"
        output_file = temp_integration_workspace / "output" / "complex_output.json"

        # Write input file
        with open(input_file, "w") as f:
            json.dump(input_data, f, indent=2)

        # Mock the Azure service response
        mock_response = create_text_output_mock()
        integration_mock_azure_service.get_chat_message_contents.return_value = mock_response

        # when
        with patch(
            "llm_ci_runner.core.setup_llm_service",
            return_value=(integration_mock_azure_service, None),
        ):
            test_args = [
                "llm_ci_runner.py",
                "--input-file",
                str(input_file),
                "--output-file",
                str(output_file),
                "--log-level",
                "DEBUG",
            ]

            with patch("sys.argv", test_args):
                await main()

        # then
        assert output_file.exists()
        with open(output_file) as f:
            result = json.load(f)

        assert result["success"] is True
        assert isinstance(result["response"], str)
        assert "metadata" in result

        # Verify the service was called with the context
        integration_mock_azure_service.get_chat_message_contents.assert_called_once()
        call_kwargs = integration_mock_azure_service.get_chat_message_contents.call_args[1]
        assert "arguments" in call_kwargs


class TestTemplateIntegration:
    """Integration tests for template-based (Jinja2 and Handlebars) examples."""

    @pytest.mark.asyncio
    async def test_jinja2_template_integration(self, temp_integration_workspace, integration_mock_azure_service):
        """Test Jinja2 template with template vars and schema."""
        # given
        template_file = Path("tests/integration/data/jinja2-example/template.jinja")
        template_vars_file = Path("tests/integration/data/jinja2-example/template-vars.yaml")
        schema_file = Path("tests/integration/data/jinja2-example/schema.yaml")
        output_file = temp_integration_workspace / "output" / "jinja2_output.json"

        # Mock the Azure service response
        mock_response = create_jinja2_template_mock()
        integration_mock_azure_service.get_chat_message_contents.return_value = mock_response

        # when
        with patch(
            "llm_ci_runner.core.setup_llm_service",
            return_value=(integration_mock_azure_service, None),
        ):
            test_args = [
                "llm_ci_runner.py",
                "--template-file",
                str(template_file),
                "--template-vars",
                str(template_vars_file),
                "--schema-file",
                str(schema_file),
                "--output-file",
                str(output_file),
                "--log-level",
                "INFO",
            ]
            with patch("sys.argv", test_args):
                await main()

        # then
        assert output_file.exists()
        with open(output_file) as f:
            result = json.load(f)
        assert result["success"] is True
        assert isinstance(result["response"], dict)
        assert "summary" in result["response"]
        assert "overall_rating" in result["response"]
        integration_mock_azure_service.get_chat_message_contents.assert_called_once()

    @pytest.mark.asyncio
    async def test_hbs_template_integration(self, temp_integration_workspace, integration_mock_azure_service):
        """Test Handlebars template with template vars and schema."""
        # given
        template_file = Path("tests/integration/data/pr-review-template/template.hbs")
        template_vars_file = Path("tests/integration/data/pr-review-template/template-vars.yaml")
        schema_file = Path("tests/integration/data/pr-review-template/schema.yaml")
        output_file = temp_integration_workspace / "output" / "hbs_output.json"

        # Mock the Azure service response
        mock_response = create_hbs_template_mock()
        integration_mock_azure_service.get_chat_message_contents.return_value = mock_response

        # when
        with patch(
            "llm_ci_runner.core.setup_llm_service",
            return_value=(integration_mock_azure_service, None),
        ):
            test_args = [
                "llm_ci_runner.py",
                "--template-file",
                str(template_file),
                "--template-vars",
                str(template_vars_file),
                "--schema-file",
                str(schema_file),
                "--output-file",
                str(output_file),
                "--log-level",
                "INFO",
            ]
            with patch("sys.argv", test_args):
                await main()

        # then
        assert output_file.exists()
        with open(output_file) as f:
            result = json.load(f)
        assert result["success"] is True
        assert isinstance(result["response"], dict)
        assert "description" in result["response"]
        assert "impact" in result["response"]
        integration_mock_azure_service.get_chat_message_contents.assert_called_once()


class TestSimpleExampleIntegrationOpenAI:
    """Integration tests for simple-example.json using OpenAI service."""

    @pytest.mark.asyncio
    async def test_simple_example_with_openai_text_output(
        self,
        temp_integration_workspace,
        mock_openai_service,
        integration_mock_openai_service,
    ):
        """Test simple example with text output (no schema) using OpenAI."""
        # given
        input_file = Path("tests/integration/data/simple-chat/input.json")
        output_file = temp_integration_workspace / "output" / "simple_openai_text_output.json"

        # Mock the OpenAI service response
        mock_response = create_text_output_mock()
        integration_mock_openai_service.get_chat_message_contents.return_value = mock_response

        # when
        with patch(
            "llm_ci_runner.core.setup_llm_service",
            return_value=(integration_mock_openai_service, None),
        ):
            test_args = [
                "llm-ci-runner",
                "--input-file",
                str(input_file),
                "--output-file",
                str(output_file),
                "--log-level",
                "INFO",
            ]
            with patch("sys.argv", test_args):
                await main()

        # then
        assert output_file.exists()
        with open(output_file) as f:
            result = json.load(f)
        assert result["success"] is True
        assert isinstance(result["response"], str)
        assert "CI/CD stands for" in result["response"]
        integration_mock_openai_service.get_chat_message_contents.assert_called_once()
