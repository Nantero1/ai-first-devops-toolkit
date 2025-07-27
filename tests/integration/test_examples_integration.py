"""
Integration tests for example workflows using the IntegrationTestHelper.

Demonstrates how to eliminate repetitive patterns while maintaining
comprehensive test coverage and clear Given-When-Then structure.
"""

from __future__ import annotations

import pytest

try:
    from integration_helpers import CommonTestData
except ImportError:
    from tests.integration.integration_helpers import CommonTestData


class TestExamplesIntegration:
    """Integration tests for example workflows."""

    @pytest.mark.asyncio
    async def test_simple_example_with_text_output(self, integration_helper, mock_azure_openai_responses):
        """Test simple example with text output using helper."""
        # given
        input_content = CommonTestData.simple_chat_input()

        # when
        result = await integration_helper.run_integration_test(
            input_content=input_content,
            input_filename="simple_text_input.json",
            output_filename="simple_text_output.json",
            log_level="INFO",
        )

        # then
        integration_helper.assert_successful_response(
            result,
            expected_response_type="str",
            expected_content_substring="This is a mock response from the test Azure service",
        )
        assert "metadata" in result

    @pytest.mark.asyncio
    async def test_simple_example_with_structured_output(self, integration_helper, mock_azure_openai_responses):
        """Test simple example with structured output schema using helper."""
        # given
        input_content = CommonTestData.simple_chat_input()
        schema_content = CommonTestData.sentiment_analysis_schema()

        # when
        result = await integration_helper.run_integration_test(
            input_content=input_content,
            schema_content=schema_content,
            input_filename="simple_structured_input.json",
            output_filename="simple_structured_output.json",
            schema_filename="simple_structured_schema.json",
            log_level="INFO",
        )

        # then
        integration_helper.assert_structured_response(
            result,
            required_fields=["sentiment", "confidence", "key_points", "summary"],
            expected_values={"sentiment": "neutral", "confidence": 0.85},
        )

    @pytest.mark.asyncio
    async def test_code_review_example_workflow(self, integration_helper, mock_azure_openai_responses):
        """Test complete code review workflow using helper."""
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
            expected_values=None,  # Allow any values for this test
        )


class TestTemplateWorkflows:
    """Tests for template-based workflows."""

    @pytest.mark.asyncio
    async def test_handlebars_template_integration(self, integration_helper, mock_azure_openai_responses):
        """Test Handlebars template workflow with reduced boilerplate."""
        # given
        template_content = CommonTestData.handlebars_template()
        template_vars = CommonTestData.template_variables()

        template_file = integration_helper.create_template_file("handlebars_test", template_content, "handlebars")
        vars_file = integration_helper.create_template_vars_file("handlebars_vars", template_vars, "yaml")
        output_file = integration_helper.output_dir / "handlebars_output.json"

        args = integration_helper.build_cli_args(
            template_file=template_file, template_vars_file=vars_file, output_file=output_file, log_level="INFO"
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
    async def test_jinja2_template_integration(self, integration_helper, mock_azure_openai_responses):
        """Test Jinja2 template workflow with reduced boilerplate."""
        # given
        template_content = CommonTestData.jinja2_template()
        template_vars = CommonTestData.template_variables()

        template_file = integration_helper.create_template_file("jinja2_test", template_content, "jinja2")
        vars_file = integration_helper.create_template_vars_file("jinja2_vars", template_vars, "json")
        output_file = integration_helper.output_dir / "jinja2_output.json"

        args = integration_helper.build_cli_args(
            template_file=template_file, template_vars_file=vars_file, output_file=output_file, log_level="INFO"
        )

        # when
        await integration_helper.execute_main_with_args(args)
        result = integration_helper.load_output_file(output_file)

        # then
        integration_helper.assert_successful_response(result, expected_response_type="str")

    @pytest.mark.asyncio
    async def test_semantic_kernel_template_integration(self, integration_helper, mock_azure_openai_responses):
        """Test Semantic Kernel template workflow with reduced boilerplate."""
        # given
        template_content = CommonTestData.semantic_kernel_template()
        template_vars = {"input_text": "This is test content for SK analysis"}

        template_file = integration_helper.create_template_file("sk_test", template_content, "semantic-kernel")
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


class TestBatchProcessingScenarios:
    """Test multiple scenarios efficiently using helper utilities."""

    @pytest.mark.parametrize(
        "input_format,output_format",
        [
            pytest.param("json", "json", id="json_to_json"),
            pytest.param("json", "yaml", id="json_to_yaml"),
            # NOTE: YAML input with messages is forbidden by design constraint
            # pytest.param("yaml", "json", id="yaml_to_json"),
            # pytest.param("yaml", "yaml", id="yaml_to_yaml"),
        ],
    )
    @pytest.mark.asyncio
    async def test_multiple_input_formats_parametrized(
        self, integration_helper, mock_azure_openai_responses, input_format, output_format
    ):
        """Test multiple input/output format combinations using parametrization."""
        # given
        base_content = CommonTestData.simple_chat_input()
        input_file = integration_helper.create_input_file(
            f"format_input.{input_format}", base_content, file_format=input_format
        )
        output_file = integration_helper.output_dir / f"format_output.{output_format}"

        args = integration_helper.build_cli_args(input_file=input_file, output_file=output_file, log_level="ERROR")

        # when
        await integration_helper.execute_main_with_args(args)
        result = integration_helper.load_output_file(output_file)

        # then
        integration_helper.assert_successful_response(
            result, expected_response_type="str", expected_content_substring="mock response"
        )

    @pytest.mark.asyncio
    async def test_yaml_constraint_validation(self, integration_helper, mock_azure_openai_responses):
        """Test that YAML files with messages are properly rejected."""
        # given
        input_content = CommonTestData.simple_chat_input()
        input_file = integration_helper.create_input_file("yaml_input.yaml", input_content, file_format="yaml")
        output_file = integration_helper.output_dir / "yaml_output.json"

        args = integration_helper.build_cli_args(input_file=input_file, output_file=output_file, log_level="ERROR")

        # when/then - expect the YAML constraint to be enforced
        with pytest.raises(SystemExit) as exc_info:
            await integration_helper.execute_main_with_args(args)

        # Verify it exits with error code 1 (indicating validation failure)
        assert exc_info.value.code == 1

    @pytest.mark.parametrize(
        "scenario_name,input_data,schema_data,expected_type,log_level",
        [
            pytest.param(
                "simple_chat",
                CommonTestData.simple_chat_input(),
                None,
                "str",
                "INFO",
                id="simple_chat_with_info_logging",
            ),
            pytest.param(
                "sentiment_analysis",
                CommonTestData.sentiment_analysis_input(),
                CommonTestData.sentiment_analysis_schema(),
                "dict",
                "ERROR",
                id="sentiment_analysis_with_error_logging",
            ),
            pytest.param(
                "code_review",
                CommonTestData.code_review_input(),
                CommonTestData.code_review_schema(),
                "dict",
                "DEBUG",
                id="code_review_with_debug_logging",
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_comprehensive_scenarios_parametrized(
        self,
        integration_helper,
        mock_azure_openai_responses,
        scenario_name,
        input_data,
        schema_data,
        expected_type,
        log_level,
    ):
        """Test comprehensive scenarios with different data types using parametrization."""
        # given
        # All test data is provided via parametrization

        # when
        result = await integration_helper.run_integration_test(
            input_content=input_data,
            schema_content=schema_data,
            input_filename=f"{scenario_name}_input.json",
            output_filename=f"{scenario_name}_output.json",
            schema_filename=f"{scenario_name}_schema.json" if schema_data else None,
            log_level=log_level,
        )

        # then
        integration_helper.assert_successful_response(result, expected_response_type=expected_type)

        # Additional structured response validation for dict responses
        if expected_type == "dict":
            assert isinstance(result["response"], dict)
            assert len(result["response"]) > 0


class TestErrorHandlingScenarios:
    """Test error handling scenarios with reduced duplication."""

    @pytest.mark.parametrize(
        "scenario_name,input_filename",
        [
            pytest.param("nonexistent_input", "nonexistent_input.json", id="missing_input_file"),
        ],
    )
    @pytest.mark.asyncio
    async def test_file_not_found_scenarios_parametrized(self, integration_helper, scenario_name, input_filename):
        """Test various file-not-found scenarios consistently using parametrization."""
        # given
        output_file = integration_helper.output_dir / "error_output.json"
        args = integration_helper.build_cli_args(input_file=input_filename, output_file=output_file, log_level="ERROR")

        # when/then
        with pytest.raises(SystemExit) as exc_info:  # main() calls sys.exit(1) on errors
            await integration_helper.execute_main_with_args(args)

        # Verify it's the expected error exit code
        assert exc_info.value.code == 1

    @pytest.mark.parametrize(
        "scenario_name,content,filename",
        [
            pytest.param("invalid_json", "{ invalid json content", "invalid.json", id="malformed_json_content"),
            pytest.param("empty_file", "", "empty.json", id="empty_file_content"),
        ],
    )
    @pytest.mark.asyncio
    async def test_invalid_file_content_scenarios_parametrized(
        self, integration_helper, scenario_name, content, filename
    ):
        """Test invalid file content scenarios consistently using parametrization."""
        # given
        # Create invalid file manually
        invalid_file = integration_helper.input_dir / filename
        with open(invalid_file, "w") as f:
            f.write(content)

        output_file = integration_helper.output_dir / f"{scenario_name}_output.json"
        args = integration_helper.build_cli_args(input_file=invalid_file, output_file=output_file, log_level="ERROR")

        # when/then
        with pytest.raises(SystemExit) as exc_info:  # main() calls sys.exit(1) on errors
            await integration_helper.execute_main_with_args(args)

        # Verify it's the expected error exit code
        assert exc_info.value.code == 1
