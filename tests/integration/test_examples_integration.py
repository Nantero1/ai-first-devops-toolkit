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


class TestSemanticKernelIntegration:
    """Integration tests for Semantic Kernel YAML template functionality."""

    @pytest.mark.asyncio
    async def test_sk_simple_question_template(self, temp_integration_workspace, sk_mock_kernel_invoke):
        """Test Semantic Kernel simple question template with realistic response."""
        # given
        template_file = Path("tests/integration/data/sk-simple-question/template.yaml")
        template_vars_file = Path("tests/integration/data/sk-simple-question/template-vars.yaml")
        output_file = temp_integration_workspace / "output" / "sk_simple_output.json"

        # when - Mock only kernel.invoke at the exact integration point, let all SK code run naturally
        # This follows integration test guidelines: mock external dependencies, test behavior end-to-end
        with patch("semantic_kernel.kernel.Kernel.invoke", sk_mock_kernel_invoke):
            test_args = [
                "llm-ci-runner",
                "--template-file",
                str(template_file),
                "--template-vars",
                str(template_vars_file),
                "--output-file",
                str(output_file),
                "--log-level",
                "INFO",
            ]

            with patch("sys.argv", test_args):
                await main()

        # then - Test end-to-end behavior: SK template should produce expected output
        assert output_file.exists()
        with open(output_file) as f:
            result = json.load(f)

        # Verify behavior: successful execution with expected response structure
        assert result["success"] is True
        assert isinstance(result["response"], str)
        assert "Continuous Integration" in result["response"]
        assert "Continuous Deployment" in result["response"]
        assert "metadata" in result

        # Verify the SK kernel.invoke was called (integration test validates end-to-end behavior)
        sk_mock_kernel_invoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_sk_structured_analysis_template(self, temp_integration_workspace, integration_mock_azure_service):
        """Test Semantic Kernel structured analysis template with JSON schema output."""
        # given
        template_file = Path("tests/integration/data/sk-structured-analysis/template.yaml")
        template_vars_file = Path("tests/integration/data/sk-structured-analysis/template-vars.yaml")
        output_file = temp_integration_workspace / "output" / "sk_structured_output.json"

        # Mock realistic structured JSON response that matches the schema
        realistic_structured_response = {
            "sentiment": "neutral",
            "confidence": 0.75,
            "key_themes": [
                "CI/CD pipeline implementation",
                "Deployment frequency improvement",
                "Test coverage concerns",
                "Team reactions to changes",
            ],
            "summary": "The text discusses a successful CI/CD pipeline implementation that improved deployment frequency but raised concerns about testing and monitoring, with mixed team reactions.",
            "word_count": 65,
        }

        from tests.mock_factory import create_mock_chat_message_content

        mock_response = create_mock_chat_message_content(content=json.dumps(realistic_structured_response))
        integration_mock_azure_service.get_chat_message_contents.return_value = [mock_response]
        integration_mock_azure_service.service_id = "azure_openai"

        # when - Mock only the LLM service, let SK template processing run naturally
        with patch("llm_ci_runner.core.setup_llm_service", return_value=(integration_mock_azure_service, None)):
            test_args = [
                "llm-ci-runner",
                "--template-file",
                str(template_file),
                "--template-vars",
                str(template_vars_file),
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

        # Verify behavior: successful structured output execution
        assert result["success"] is True
        assert isinstance(result["response"], dict)

        # Verify structured response contains expected schema fields
        response_data = result["response"]
        assert response_data["sentiment"] == "neutral"
        assert "key_themes" in response_data
        assert len(response_data["key_themes"]) >= 1
        assert response_data["confidence"] == 0.75
        assert "summary" in response_data
        assert "word_count" in response_data

        # Verify integration metadata
        assert "metadata" in result

        # Verify the LLM service was called
        integration_mock_azure_service.get_chat_message_contents.assert_called_once()

    @pytest.mark.asyncio
    async def test_sk_template_error_handling(self, temp_integration_workspace):
        """Test Semantic Kernel template error handling behavior."""
        # given
        template_file = Path("tests/integration/data/sk-simple-question/template.yaml")
        template_vars_file = Path("tests/integration/data/sk-simple-question/template-vars.yaml")
        output_file = temp_integration_workspace / "output" / "sk_error_output.json"

        # when - simulate kernel.invoke failure (external dependency error)
        # Following integration test guidelines: mock only external dependencies
        error_mock = AsyncMock(side_effect=Exception("Simulated LLM service failure"))
        with patch("semantic_kernel.kernel.Kernel.invoke", error_mock):
            test_args = [
                "llm-ci-runner",
                "--template-file",
                str(template_file),
                "--template-vars",
                str(template_vars_file),
                "--output-file",
                str(output_file),
                "--log-level",
                "DEBUG",
            ]

            with patch("sys.argv", test_args):
                # then - verify error handling causes SystemExit (CLI behavior)
                with pytest.raises(SystemExit) as exc_info:
                    await main()

                # Verify it exits with error code 1 (proper error handling)
                assert exc_info.value.code == 1

        # Verify the external call was attempted (behavior-focused assertion)
        error_mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_sk_template_file_validation(self, temp_integration_workspace):
        """Test Semantic Kernel template file validation behavior."""
        # given
        nonexistent_template = Path("tests/integration/data/nonexistent-template.yaml")
        template_vars_file = Path("tests/integration/data/sk-simple-question/template-vars.yaml")
        output_file = temp_integration_workspace / "output" / "sk_validation_output.json"

        # when - attempt to use nonexistent template file
        test_args = [
            "llm-ci-runner",
            "--template-file",
            str(nonexistent_template),
            "--template-vars",
            str(template_vars_file),
            "--output-file",
            str(output_file),
            "--log-level",
            "DEBUG",
        ]

        with patch("sys.argv", test_args):
            # then - verify file validation error causes SystemExit (CLI behavior)
            with pytest.raises(SystemExit) as exc_info:
                await main()

            # Verify it exits with error code 1
            assert exc_info.value.code == 1

    @pytest.mark.asyncio
    async def test_sk_template_vars_validation(self, temp_integration_workspace):
        """Test Semantic Kernel template variable validation behavior."""
        # given
        template_file = Path("tests/integration/data/sk-simple-question/template.yaml")
        nonexistent_vars = Path("tests/integration/data/nonexistent-vars.yaml")
        output_file = temp_integration_workspace / "output" / "sk_vars_validation_output.json"

        # when - attempt to use nonexistent template vars file
        test_args = [
            "llm-ci-runner",
            "--template-file",
            str(template_file),
            "--template-vars",
            str(nonexistent_vars),
            "--output-file",
            str(output_file),
            "--log-level",
            "DEBUG",
        ]

        with patch("sys.argv", test_args):
            # then - verify template vars validation error causes SystemExit (CLI behavior)
            with pytest.raises(SystemExit) as exc_info:
                await main()

            # Verify it exits with error code 1
            assert exc_info.value.code == 1

    @pytest.mark.asyncio
    async def test_sk_template_integration_with_real_file_operations(
        self, temp_integration_workspace, sk_mock_kernel_invoke
    ):
        """Test end-to-end Semantic Kernel integration with real file I/O operations."""
        # given - create temporary template files in workspace
        workspace_template_dir = temp_integration_workspace / "templates"
        workspace_template_dir.mkdir()

        template_file = workspace_template_dir / "test_template.yaml"
        template_vars_file = workspace_template_dir / "test_vars.yaml"
        output_file = temp_integration_workspace / "output" / "integration_output.json"

        # Create actual template files for real file operations
        template_content = """name: IntegrationTest
description: Integration test template
template_format: semantic-kernel
template: |
  You are a {{$role}} assistant.
  Answer: {{$question}}

input_variables:
  - name: role
    description: Assistant role
    default: "helpful"
    is_required: false
  - name: question
    description: Question to answer
    is_required: true

execution_settings:
  azure_openai:
    temperature: 0.5
    max_tokens: 300"""

        vars_content = """role: test assistant
question: What is integration testing?"""

        with open(template_file, "w") as f:
            f.write(template_content)

        with open(template_vars_file, "w") as f:
            f.write(vars_content)

        # when - Test end-to-end behavior with real file I/O and SK template processing
        # Mock only the external LLM call, let all file operations and SK processing run naturally
        with patch("semantic_kernel.kernel.Kernel.invoke", sk_mock_kernel_invoke):
            test_args = [
                "llm-ci-runner",
                "--template-file",
                str(template_file),
                "--template-vars",
                str(template_vars_file),
                "--output-file",
                str(output_file),
                "--log-level",
                "INFO",
            ]

            with patch("sys.argv", test_args):
                await main()

        # then - verify end-to-end integration behavior
        assert output_file.exists()
        with open(output_file) as f:
            result = json.load(f)

        # Verify successful end-to-end execution
        assert result["success"] is True
        assert isinstance(result["response"], str)
        assert "metadata" in result

        # Verify the external dependency was called (behavior-focused testing)
        sk_mock_kernel_invoke.assert_called_once()

        # Verify file operations worked by checking the template was processed
        # (The fact that we got a successful response means files were read and processed correctly)

        # Verify template files were created and are readable
        assert template_file.exists()
        assert template_vars_file.exists()

        with open(template_file) as f:
            saved_template = f.read()
        assert "IntegrationTest" in saved_template

        with open(template_vars_file) as f:
            saved_vars = f.read()
        assert "test assistant" in saved_vars
