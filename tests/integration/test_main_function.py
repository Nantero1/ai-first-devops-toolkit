"""
Integration tests for main() function using the IntegrationTestHelper.

Tests the main() function directly with various input scenarios
while maintaining clarity and following the Given-When-Then pattern.
"""

from __future__ import annotations

import pytest

try:
    from integration_helpers import CommonTestData
except ImportError:
    from tests.integration.integration_helpers import CommonTestData


class TestMainFunctionIntegration:
    """Integration tests for main() function using helper utilities."""

    @pytest.mark.asyncio
    async def test_main_with_simple_text_input(self, integration_helper, mock_azure_openai_responses):
        """Test main() with simple text input and output."""
        # given
        input_content = CommonTestData.simple_chat_input()

        # when
        result = await integration_helper.run_integration_test(
            input_content=input_content,
            input_filename="simple_input.json",
            output_filename="simple_output.json",
            log_level="ERROR",
        )

        # then
        integration_helper.assert_successful_response(
            result,
            expected_response_type="str",
            expected_content_substring="This is a mock response from the test Azure service",
        )

    @pytest.mark.asyncio
    async def test_main_with_structured_output(self, integration_helper, mock_azure_openai_responses):
        """Test main() with structured output schema."""
        # given
        input_content = CommonTestData.sentiment_analysis_input()
        schema_content = CommonTestData.sentiment_analysis_schema()

        # when
        result = await integration_helper.run_integration_test(
            input_content=input_content,
            schema_content=schema_content,
            input_filename="sentiment_input.json",
            output_filename="sentiment_output.json",
            schema_filename="sentiment_schema.json",
            log_level="DEBUG",
        )

        # then
        integration_helper.assert_structured_response(
            result,
            required_fields=["sentiment", "confidence", "summary", "key_points"],
            expected_values={"sentiment": "neutral", "confidence": 0.85},
        )

    @pytest.mark.asyncio
    async def test_main_with_template_workflow(self, integration_helper, mock_azure_openai_responses):
        """Test main() with Handlebars template workflow."""
        # given
        template_content = CommonTestData.handlebars_template()
        template_vars = CommonTestData.template_variables()

        # Create template and variables files
        template_file = integration_helper.create_template_file("test_template", template_content, "handlebars")
        vars_file = integration_helper.create_template_vars_file("test_vars", template_vars, "yaml")
        output_file = integration_helper.output_dir / "template_output.json"

        # Build CLI args for template workflow
        args = integration_helper.build_cli_args(
            template_file=template_file, template_vars_file=vars_file, output_file=output_file, log_level="ERROR"
        )

        # when
        await integration_helper.execute_main_with_args(args)
        result = integration_helper.load_output_file(output_file)

        # then
        integration_helper.assert_successful_response(
            result,
            expected_response_type="str",
            expected_content_substring="This is a mock response from the test Azure service",
        )

    @pytest.mark.asyncio
    async def test_main_with_yaml_constraint_validation(self, integration_helper, mock_azure_openai_responses):
        """Test main() properly rejects YAML files with messages due to constraint."""
        # given
        input_content = CommonTestData.simple_chat_input()
        input_content["context"] = {"session_id": "test-yaml-123"}

        input_file = integration_helper.create_input_file("test_input.yaml", input_content, file_format="yaml")
        output_file = integration_helper.output_dir / "test_output.yaml"

        # Build CLI args
        args = integration_helper.build_cli_args(input_file=input_file, output_file=output_file, log_level="ERROR")

        # when/then - expect the YAML constraint to be enforced
        with pytest.raises(SystemExit) as exc_info:  # CLI should exit with error due to YAML constraint
            await integration_helper.execute_main_with_args(args)

        # Verify it exits with error code 1 (indicating validation failure)
        assert exc_info.value.code == 1

    @pytest.mark.asyncio
    async def test_main_error_handling_missing_file(self, integration_helper, mock_azure_openai_responses):
        """Test main() handles missing input file gracefully."""
        # given
        nonexistent_file = integration_helper.input_dir / "nonexistent.json"
        output_file = integration_helper.output_dir / "error_output.json"

        args = integration_helper.build_cli_args(
            input_file=nonexistent_file, output_file=output_file, log_level="ERROR"
        )

        # when/then
        with pytest.raises(SystemExit) as exc_info:  # CLI should exit with error code on missing file
            await integration_helper.execute_main_with_args(args)

        # Verify it exits with error code 1 (indicating failure)
        assert exc_info.value.code == 1


class TestMainFunctionAdvancedScenarios:
    """Advanced integration test scenarios using helper utilities."""

    @pytest.mark.asyncio
    async def test_code_review_workflow(self, integration_helper, mock_azure_openai_responses):
        """Test complete code review workflow with structured output."""
        # given
        input_content = CommonTestData.code_review_input()
        schema_content = CommonTestData.code_review_schema()

        # when
        result = await integration_helper.run_integration_test(
            input_content=input_content,
            schema_content=schema_content,
            input_filename="code_review_input.json",
            output_filename="code_review_output.json",
            schema_filename="code_review_schema.json",
            log_level="DEBUG",
        )

        # then
        integration_helper.assert_structured_response(
            result,
            required_fields=["overall_rating", "summary"],
            expected_values=None,  # Don't check specific values for this mock
        )

    @pytest.mark.asyncio
    async def test_jinja2_template_workflow(self, integration_helper, mock_azure_openai_responses):
        """Test Jinja2 template processing workflow."""
        # given
        template_content = CommonTestData.jinja2_template()
        template_vars = CommonTestData.template_variables()

        template_file = integration_helper.create_template_file("jinja_template", template_content, "jinja2")
        vars_file = integration_helper.create_template_vars_file("jinja_vars", template_vars, "json")
        output_file = integration_helper.output_dir / "jinja_output.json"

        args = integration_helper.build_cli_args(
            template_file=template_file, template_vars_file=vars_file, output_file=output_file, log_level="INFO"
        )

        # when
        await integration_helper.execute_main_with_args(args)
        result = integration_helper.load_output_file(output_file)

        # then
        integration_helper.assert_successful_response(result, expected_response_type="str")

    @pytest.mark.asyncio
    async def test_semantic_kernel_template_workflow(self, integration_helper, mock_azure_openai_responses):
        """Test Semantic Kernel YAML template workflow."""
        # given
        template_content = CommonTestData.semantic_kernel_template()
        template_vars = {"input_text": "This is test content for analysis"}

        template_file = integration_helper.create_template_file("sk_template", template_content, "semantic-kernel")
        vars_file = integration_helper.create_template_vars_file("sk_vars", template_vars, "yaml")
        output_file = integration_helper.output_dir / "sk_output.json"

        args = integration_helper.build_cli_args(
            template_file=template_file, template_vars_file=vars_file, output_file=output_file, log_level="INFO"
        )

        # when
        await integration_helper.execute_main_with_args(args)
        result = integration_helper.load_output_file(output_file)

        # then
        integration_helper.assert_successful_response(result, expected_response_type="str")

    @pytest.mark.parametrize(
        "scenario_name,input_data,schema_data,expected_type,expected_substring",
        [
            pytest.param(
                "simple_chat",
                CommonTestData.simple_chat_input(),
                None,
                "str",
                "mock response",
                id="simple_chat_text_output",
            ),
            pytest.param(
                "sentiment_analysis",
                CommonTestData.sentiment_analysis_input(),
                CommonTestData.sentiment_analysis_schema(),
                "dict",
                None,
                id="sentiment_analysis_structured_output",
            ),
            pytest.param(
                "code_review",
                CommonTestData.code_review_input(),
                CommonTestData.code_review_schema(),
                "dict",
                None,
                id="code_review_structured_output",
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_multiple_scenarios_parametrized(
        self,
        integration_helper,
        mock_azure_openai_responses,
        scenario_name,
        input_data,
        schema_data,
        expected_type,
        expected_substring,
    ):
        """Test multiple scenarios using parametrized tests for better reporting."""
        # given
        # All test data is provided via parametrization

        # when
        result = await integration_helper.run_integration_test(
            input_content=input_data,
            schema_content=schema_data,
            input_filename=f"{scenario_name}_input.json",
            output_filename=f"{scenario_name}_output.json",
            schema_filename=f"{scenario_name}_schema.json" if schema_data else None,
            log_level="ERROR",
        )

        # then
        integration_helper.assert_successful_response(
            result,
            expected_response_type=expected_type,
            expected_content_substring=expected_substring,
        )
