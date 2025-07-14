"""
Integration tests for all example files in llm_ci_runner.py

Tests the full pipeline with real file operations and JSON parsing,
but mocked LLM service calls. Uses minimal mocking following the
Given-When-Then pattern.
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

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

        # Mock the Azure service response with proper ChatMessageContent format
        from tests.mock_factory import create_mock_chat_message_content

        mock_response = create_mock_chat_message_content(
            content="CI/CD stands for Continuous Integration and Continuous Deployment. It's a set of practices that automates the building, testing, and deployment of software, enabling teams to deliver code changes more frequently and reliably."
        )
        integration_mock_azure_service.get_chat_message_contents.return_value = [mock_response]
        # Set the service_id to match what Semantic Kernel expects
        integration_mock_azure_service.service_id = "azure_openai"

        # when
        with (
            patch(
                "llm_ci_runner.core.setup_llm_service",
                return_value=(integration_mock_azure_service, None),
            ),
            patch("llm_ci_runner.llm_execution.AsyncAzureOpenAI") as mock_azure_client,
            patch("llm_ci_runner.llm_execution.AsyncOpenAI") as mock_openai_client,
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

        # Mock the Azure service response with proper ChatMessageContent format
        from tests.mock_factory import create_mock_chat_message_content

        mock_response = create_mock_chat_message_content(
            content='{"sentiment":"neutral","confidence":0.95,"key_points":["Continuous Integration (CI): automated testing and merging of code changes","Continuous Deployment (CD): automated deployment of code to production","Improves software delivery speed and quality","Reduces manual errors","Facilitates frequent releases"],"summary":"CI/CD in software development refers to practices of automatically integrating, testing, and deploying code to improve delivery speed and quality."}'
        )
        integration_mock_azure_service.get_chat_message_contents.return_value = [mock_response]
        # Set the service_id to match what Semantic Kernel expects
        integration_mock_azure_service.service_id = "azure_openai"

        # when
        with (
            patch(
                "llm_ci_runner.core.setup_llm_service",
                return_value=(integration_mock_azure_service, None),
            ),
            patch("llm_ci_runner.llm_execution.AsyncAzureOpenAI") as mock_azure_client,
            patch("llm_ci_runner.llm_execution.AsyncOpenAI") as mock_openai_client,
        ):
            test_args = [
                "llm-ci-runner",
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

        # Mock the Azure service response with proper ChatMessageContent format
        from tests.mock_factory import create_mock_chat_message_content

        mock_response = create_mock_chat_message_content(
            content="## Code Review Summary\n\n**Security Issues Fixed:**\n✅ SQL injection vulnerability resolved by using parameterized queries\n✅ Input validation added for user_id parameter\n\n**Code Quality:**\n- Good use of parameterized queries\n- Proper error handling with ValueError for invalid input\n- Consistent coding style\n\n**Recommendations:**\n- Consider adding logging for security events\n- Add unit tests for the new validation logic\n\n**Overall Assessment:** This PR successfully addresses the SQL injection vulnerability and adds appropriate input validation. The changes follow security best practices."
        )
        integration_mock_azure_service.get_chat_message_contents.return_value = [mock_response]
        # Set the service_id to match what Semantic Kernel expects
        integration_mock_azure_service.service_id = "azure_openai"

        # when
        with (
            patch(
                "llm_ci_runner.core.setup_llm_service",
                return_value=(integration_mock_azure_service, None),
            ),
            patch("llm_ci_runner.llm_execution.AsyncAzureOpenAI") as mock_azure_client,
            patch("llm_ci_runner.llm_execution.AsyncOpenAI") as mock_openai_client,
        ):
            test_args = [
                "llm-ci-runner",
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
        # Mock the Azure service response with proper ChatMessageContent format
        from tests.mock_factory import create_mock_chat_message_content

        mock_response = create_mock_chat_message_content(content=structured_pr_response)
        integration_mock_azure_service.get_chat_message_contents.return_value = [mock_response]
        # Set the service_id to match what Semantic Kernel expects
        integration_mock_azure_service.service_id = "azure_openai"

        # when
        with (
            patch(
                "llm_ci_runner.core.setup_llm_service",
                return_value=(integration_mock_azure_service, None),
            ),
            patch("llm_ci_runner.llm_execution.AsyncAzureOpenAI") as mock_azure_client,
            patch("llm_ci_runner.llm_execution.AsyncOpenAI") as mock_openai_client,
        ):
            test_args = [
                "llm-ci-runner",
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

        # Mock the Azure service response with proper ChatMessageContent format
        from tests.mock_factory import create_mock_chat_message_content

        mock_response = create_mock_chat_message_content(
            content="Hello! I'm ready to help you with any questions or tasks you have."
        )
        integration_mock_azure_service.get_chat_message_contents.return_value = [mock_response]
        # Set the service_id to match what Semantic Kernel expects
        integration_mock_azure_service.service_id = "azure_openai"

        # when
        with (
            patch(
                "llm_ci_runner.core.setup_llm_service",
                return_value=(integration_mock_azure_service, None),
            ),
            patch("llm_ci_runner.llm_execution.AsyncAzureOpenAI") as mock_azure_client,
            patch("llm_ci_runner.llm_execution.AsyncOpenAI") as mock_openai_client,
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
        assert "Hello!" in result["response"]
        integration_mock_azure_service.get_chat_message_contents.assert_called_once()


class TestAllExamplesEndToEnd:
    """End-to-end tests for all example files."""

    @pytest.mark.asyncio
    async def test_all_examples_process_successfully(self, temp_integration_workspace, integration_mock_azure_service):
        """Test that all example files can be processed successfully."""
        # given
        examples = [
            (
                "tests/integration/data/simple-chat/input.json",
                "simple_chat_output.json",
            ),
            (
                "tests/integration/data/code-review/input.json",
                "code_review_output.json",
            ),
        ]

        # Mock the Azure service response with proper ChatMessageContent format
        from tests.mock_factory import create_mock_chat_message_content

        mock_response = create_mock_chat_message_content(
            content="CI/CD stands for Continuous Integration and Continuous Deployment. It's a set of practices that automates the building, testing, and deployment of software, enabling teams to deliver code changes more frequently and reliably."
        )
        integration_mock_azure_service.get_chat_message_contents.return_value = [mock_response]
        # Set the service_id to match what Semantic Kernel expects
        integration_mock_azure_service.service_id = "azure_openai"

        # when
        with (
            patch(
                "llm_ci_runner.core.setup_llm_service",
                return_value=(integration_mock_azure_service, None),
            ),
            patch("llm_ci_runner.llm_execution.AsyncAzureOpenAI") as mock_azure_client,
            patch("llm_ci_runner.llm_execution.AsyncOpenAI") as mock_openai_client,
        ):
            for input_file, output_filename in examples:
                output_file = temp_integration_workspace / "output" / output_filename

                test_args = [
                    "llm-ci-runner",
                    "--input-file",
                    input_file,
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
                assert len(result["response"]) > 0

    @pytest.mark.asyncio
    async def test_example_with_nonexistent_input_file_raises_error(
        self, temp_integration_workspace, integration_mock_azure_service
    ):
        """Test that processing a nonexistent input file raises an appropriate error."""
        # given
        nonexistent_file = "tests/integration/data/nonexistent.json"
        output_file = temp_integration_workspace / "output" / "error_output.json"

        # Mock the Azure service response
        integration_mock_azure_service.get_chat_message_contents.return_value = [
            {"role": "assistant", "content": "Test response", "metadata": {}}
        ]
        # Set the service_id to match what Semantic Kernel expects
        integration_mock_azure_service.service_id = "azure_openai"

        # when
        with patch(
            "llm_ci_runner.core.setup_llm_service",
            return_value=(integration_mock_azure_service, None),
        ):
            test_args = [
                "llm_ci_runner.py",
                "--input-file",
                nonexistent_file,
                "--output-file",
                str(output_file),
                "--log-level",
                "INFO",
            ]

            with patch("sys.argv", test_args):
                # This should raise a SystemExit due to file not found
                with pytest.raises(SystemExit):
                    await main()

    @pytest.mark.asyncio
    async def test_example_with_invalid_schema_file_raises_error(
        self, temp_integration_workspace, integration_mock_azure_service
    ):
        """Test that processing with an invalid schema file raises an appropriate error."""
        # given
        input_file = Path("tests/integration/data/simple-chat/input.json")
        invalid_schema_file = "tests/integration/data/invalid_schema.json"
        output_file = temp_integration_workspace / "output" / "error_output.json"

        # Mock the Azure service response
        integration_mock_azure_service.get_chat_message_contents.return_value = [
            {"role": "assistant", "content": "Test response", "metadata": {}}
        ]
        # Set the service_id to match what Semantic Kernel expects
        integration_mock_azure_service.service_id = "azure_openai"

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
                invalid_schema_file,
                "--log-level",
                "INFO",
            ]

            with patch("sys.argv", test_args):
                # This should raise a SystemExit due to invalid schema file
                with pytest.raises(SystemExit):
                    await main()


class TestFullPipelineIntegration:
    """Full pipeline integration tests."""

    @pytest.mark.asyncio
    async def test_full_pipeline_with_context_processing(
        self, temp_integration_workspace, integration_mock_azure_service
    ):
        """Test the full pipeline with context processing and multiple messages."""
        # given
        input_file = Path("tests/integration/data/code-review/input.json")
        output_file = temp_integration_workspace / "output" / "full_pipeline_output.json"

        # Mock the Azure service response with proper ChatMessageContent format
        from tests.mock_factory import create_mock_chat_message_content

        mock_response = create_mock_chat_message_content(
            content="## Code Review Summary\n\n**Security Issues Fixed:**\n✅ SQL injection vulnerability resolved by using parameterized queries\n✅ Input validation added for user_id parameter\n\n**Code Quality:**\n- Good use of parameterized queries\n- Proper error handling with ValueError for invalid input\n- Consistent coding style\n\n**Recommendations:**\n- Consider adding logging for security events\n- Add unit tests for the new validation logic\n\n**Overall Assessment:** This PR successfully addresses the SQL injection vulnerability and adds appropriate input validation. The changes follow security best practices."
        )
        integration_mock_azure_service.get_chat_message_contents.return_value = [mock_response]
        # Set the service_id to match what Semantic Kernel expects
        integration_mock_azure_service.service_id = "azure_openai"

        # when
        with (
            patch(
                "llm_ci_runner.core.setup_llm_service",
                return_value=(integration_mock_azure_service, None),
            ),
            patch("llm_ci_runner.llm_execution.AsyncAzureOpenAI") as mock_azure_client,
            patch("llm_ci_runner.llm_execution.AsyncOpenAI") as mock_openai_client,
        ):
            test_args = [
                "llm-ci-runner",
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


class TestTemplateIntegration:
    """Integration tests for template-based workflows."""

    @pytest.mark.asyncio
    async def test_jinja2_template_integration(self, temp_integration_workspace, integration_mock_azure_service):
        """Test Jinja2 template integration with real template processing."""
        # given
        template_file = Path("tests/integration/data/jinja2-example/template.jinja")
        template_vars_file = Path("tests/integration/data/jinja2-example/template-vars.yaml")
        schema_file = Path("tests/integration/data/jinja2-example/schema.yaml")
        output_file = temp_integration_workspace / "output" / "jinja2_template_output.json"

        # Mock the Azure service response with proper dictionary format
        mock_response_data = {
            "summary": "Implements rate limiting and improves error handling.",
            "code_quality_score": 9,
            "security_assessment": {
                "vulnerabilities_found": ["None detected"],
                "risk_level": "low",
                "recommendations": [
                    "Continue using parameterized queries",
                    "Add more input validation",
                ],
            },
            "performance_analysis": {
                "impact": "positive",
                "concerns": ["None"],
                "optimizations": ["Consider caching frequent queries"],
            },
            "testing_recommendations": {
                "test_coverage": "adequate",
                "missing_tests": ["Edge case for max_limit"],
                "test_scenarios": [
                    "Test rate limit exceeded",
                    "Test invalid credentials",
                ],
            },
            "suggestions": [
                "Improve documentation",
                "Add logging for rate limit events",
            ],
            "overall_rating": "approve_with_suggestions",
        }

        from tests.mock_factory import create_mock_chat_message_content

        mock_response = create_mock_chat_message_content(content=json.dumps(mock_response_data))
        integration_mock_azure_service.get_chat_message_contents.return_value = [mock_response]
        # Set the service_id to match what Semantic Kernel expects
        integration_mock_azure_service.service_id = "azure_openai"

        # when
        with (
            patch(
                "llm_ci_runner.core.setup_llm_service",
                return_value=(integration_mock_azure_service, None),
            ),
            patch("llm_ci_runner.llm_execution.AsyncAzureOpenAI") as mock_azure_client,
            patch("llm_ci_runner.llm_execution.AsyncOpenAI") as mock_openai_client,
        ):
            test_args = [
                "llm-ci-runner",
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
        assert "code_quality_score" in result["response"]
        assert "security_assessment" in result["response"]
        integration_mock_azure_service.get_chat_message_contents.assert_called_once()

    @pytest.mark.asyncio
    async def test_hbs_template_integration(self, temp_integration_workspace, integration_mock_azure_service):
        """Test Handlebars template integration with real template processing."""
        # given
        template_file = Path("tests/integration/data/pr-review-template/template.hbs")
        template_vars_file = Path("tests/integration/data/pr-review-template/template-vars.yaml")
        schema_file = Path("tests/integration/data/pr-review-template/schema.yaml")
        output_file = temp_integration_workspace / "output" / "hbs_template_output.json"

        # Mock the Azure service response with proper dictionary format
        mock_response_data = {
            "description": "This PR addresses SQL injection vulnerabilities and improves input validation. Session management is now more secure and error handling is robust.",
            "summary": "Fixes security issues and improves session management.",
            "change_type": "security",
            "impact": "high",
            "security_findings": [
                {
                    "type": "vulnerability_fixed",
                    "description": "SQL injection vulnerability resolved by using parameterized queries.",
                    "severity": "high",
                },
                {
                    "type": "security_improvement",
                    "description": "Input validation added for user_id.",
                    "severity": "medium",
                },
            ],
            "testing_notes": [
                "Add tests for invalid credentials",
                "Test session creation with invalid user_id",
            ],
            "deployment_notes": [
                "No downtime expected",
                "Monitor authentication logs post-deployment",
            ],
            "breaking_changes": [],
            "related_issues": [456, 789],
        }

        from tests.mock_factory import create_mock_chat_message_content

        mock_response = create_mock_chat_message_content(content=json.dumps(mock_response_data))
        integration_mock_azure_service.get_chat_message_contents.return_value = [mock_response]
        # Set the service_id to match what Semantic Kernel expects
        integration_mock_azure_service.service_id = "azure_openai"

        # when
        with (
            patch(
                "llm_ci_runner.core.setup_llm_service",
                return_value=(integration_mock_azure_service, None),
            ),
            patch("llm_ci_runner.llm_execution.AsyncAzureOpenAI") as mock_azure_client,
            patch("llm_ci_runner.llm_execution.AsyncOpenAI") as mock_openai_client,
        ):
            test_args = [
                "llm-ci-runner",
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
        assert "summary" in result["response"]
        assert "security_findings" in result["response"]
        integration_mock_azure_service.get_chat_message_contents.assert_called_once()


class TestSimpleExampleIntegrationOpenAI:
    """Integration tests for OpenAI (non-Azure) endpoints."""

    @pytest.mark.asyncio
    async def test_simple_example_with_openai_text_output(
        self,
        temp_integration_workspace,
        integration_mock_openai_service,
        monkeypatch,
    ):
        """Test simple example with OpenAI text output."""
        # given - setup OpenAI environment (clear Azure variables)
        monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
        monkeypatch.delenv("AZURE_OPENAI_MODEL", raising=False)
        monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
        monkeypatch.setenv("OPENAI_CHAT_MODEL_ID", "gpt-4-test")

        input_file = Path("tests/integration/data/simple-chat/input.json")
        output_file = temp_integration_workspace / "output" / "openai_text_output.json"

        # Mock the OpenAI service response with proper ChatMessageContent format
        from tests.mock_factory import create_mock_chat_message_content

        mock_response = create_mock_chat_message_content(
            content="CI/CD stands for Continuous Integration and Continuous Deployment. It's a set of practices that automates the building, testing, and deployment of software, enabling teams to deliver code changes more frequently and reliably."
        )
        integration_mock_openai_service.get_chat_message_contents.return_value = [mock_response]
        # Set the service_id to match what Semantic Kernel expects for OpenAI (not Azure)
        integration_mock_openai_service.service_id = "openai"

        # when
        with (
            patch(
                "llm_ci_runner.core.setup_llm_service",
                return_value=(
                    integration_mock_openai_service,
                    None,
                ),  # OpenAI service returns (service, None)
            ),
            patch("llm_ci_runner.llm_execution.AsyncAzureOpenAI") as mock_azure_client,
            patch("llm_ci_runner.llm_execution.AsyncOpenAI") as mock_openai_client,
        ):
            # Configure the OpenAI client mock to return proper async response
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message = Mock()
            mock_response.choices[
                0
            ].message.content = "CI/CD stands for Continuous Integration and Continuous Deployment. It's a set of practices that automates the building, testing, and deployment of software, enabling teams to deliver code changes more frequently and reliably."

            # Use AsyncMock for the create method to handle await
            from unittest.mock import AsyncMock

            mock_openai_client.return_value.chat.completions.create = AsyncMock(return_value=mock_response)
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
        # Note: The Semantic Kernel service is not called because it falls back to OpenAI SDK
        # This is the expected behavior for OpenAI integration tests
