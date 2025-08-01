"""
Unit tests for string-based template functions in LLM CI Runner.

Tests the run_llm_task function with template_content, template_format,
and template_vars parameters, following behavior-focused testing principles.
"""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from llm_ci_runner import (
    InputValidationError,
    load_template_from_string,
    run_llm_task,
)


class TestRunLlmTaskStringTemplates:
    """Tests for run_llm_task function with string-based template parameters."""

    @pytest.mark.asyncio
    async def test_run_llm_task_validation_requires_input_method(self):
        """Test that run_llm_task requires at least one input method."""
        # given
        # No input parameters provided

        # when & then
        with pytest.raises(
            InputValidationError,
            match="Either template_content, template_file, or input file must be specified",
        ):
            await run_llm_task()

    @pytest.mark.asyncio
    async def test_run_llm_task_validation_mutually_exclusive_inputs(self):
        """Test that template inputs are mutually exclusive."""
        # given
        template_file = "template.hbs"
        template_content = "Hello {{name}}"

        # when & then
        with pytest.raises(
            InputValidationError,
            match="Cannot specify multiple input sources",
        ):
            await run_llm_task(
                template_file=template_file,
                template_content=template_content,
                template_format="handlebars",
            )

    @pytest.mark.asyncio
    async def test_run_llm_task_validation_template_format_required(self):
        """Test that template_format is required when using templates."""
        # given
        template_content = "Hello {{name}}"

        # when & then
        with pytest.raises(
            InputValidationError,
            match="template_format is required when using templates",
        ):
            await run_llm_task(template_content=template_content)

    @pytest.mark.asyncio
    async def test_run_llm_task_validation_smart_template_vars_working(self, tmp_path):
        """Test that smart auto-detection for template_vars works (no validation error)."""
        # given
        template_content = "Hello {{name}}"
        template_format = "handlebars"

        # This should NOT raise an error because template_vars supports both dict and string
        # Testing that the new unified API accepts both formats
        with patch("llm_ci_runner.core.setup_llm_service") as mock_setup:
            mock_service = Mock()
            mock_credential = Mock()
            mock_setup.return_value = (mock_service, mock_credential)

            with patch("llm_ci_runner.core._process_template_unified") as mock_process:
                mock_process.return_value = "mocked response"

                # when - should work with dict
                result1 = await run_llm_task(
                    template_content=template_content,
                    template_format=template_format,
                    template_vars={"name": "World"},  # Dict format
                )

                # when - should work with string (file path) - create temp file
                temp_vars_file = tmp_path / "vars.yaml"
                temp_vars_file.write_text("name: World\n")

                result2 = await run_llm_task(
                    template_content=template_content,
                    template_format=template_format,
                    template_vars=str(temp_vars_file),  # String format (file path)
                )

                # then
                assert result1 == "mocked response"
                assert result2 == "mocked response"

    @pytest.mark.asyncio
    async def test_run_llm_task_validation_mutually_exclusive_template_vars(self, mock_environment_variables):
        """Test that the unified API accepts both dict and file path for template_vars."""
        # given
        template_content = "Hello {{name}}"
        template_format = "handlebars"

        with patch("llm_ci_runner.core._process_template_unified") as mock_process:
            mock_process.return_value = "mocked response"

            # when - Test with dict (should work)
            result1 = await run_llm_task(
                template_content=template_content,
                template_format=template_format,
                template_vars={"name": "World"},  # Dict format
            )

            # then
            assert result1 == "mocked response"

    @pytest.mark.asyncio
    async def test_run_llm_task_validation_invalid_template_format(self):
        """Test that invalid template_format values are rejected."""
        # given
        template_content = "Hello {{name}}"
        template_format = "invalid_format"

        # when & then
        with pytest.raises(
            InputValidationError,
            match="Invalid template_format.*Must be one of: handlebars, jinja2, semantic-kernel",
        ):
            await run_llm_task(
                template_content=template_content,
                template_format=template_format,
            )

    @pytest.mark.asyncio
    @patch("llm_ci_runner.core.setup_llm_service")
    @patch("llm_ci_runner.core.load_template_from_string")
    @patch("llm_ci_runner.core.render_template")
    @patch("llm_ci_runner.core.parse_rendered_template_to_chat_history")
    @patch("llm_ci_runner.core._convert_chat_history_to_list")
    @patch("llm_ci_runner.core.execute_llm_with_chat_history")
    async def test_run_llm_task_handlebars_template_string_workflow(
        self,
        mock_execute_llm,
        mock_convert_chat,
        mock_parse_rendered,
        mock_render_template,
        mock_load_template,
        mock_setup_service,
    ):
        """Test successful run_llm_task with Handlebars template content."""
        # given
        template_content = "Hello {{name}}!"
        template_format = "handlebars"
        template_vars = {"name": "World"}
        expected_response = "Hello World!"

        # Mock service setup
        mock_service = Mock()
        mock_credential = Mock()
        mock_setup_service.return_value = (mock_service, mock_credential)
        mock_credential.close = AsyncMock()

        # Mock template loading
        mock_template = Mock()
        mock_load_template.return_value = mock_template

        # Mock template processing
        mock_rendered_content = "Hello World!"
        mock_render_template.return_value = mock_rendered_content

        mock_chat_history_raw = Mock()
        mock_parse_rendered.return_value = mock_chat_history_raw

        mock_chat_history = [{"role": "user", "content": "Hello World!"}]
        mock_convert_chat.return_value = mock_chat_history

        # Mock LLM execution
        mock_execute_llm.return_value = expected_response

        # when
        result = await run_llm_task(
            template_content=template_content,
            template_format=template_format,
            template_vars=template_vars,
        )

        # then
        assert result == expected_response

        # Verify workflow steps
        mock_setup_service.assert_called_once()
        mock_load_template.assert_called_once_with(template_content, template_format)
        mock_render_template.assert_called_once()
        mock_parse_rendered.assert_called_once_with(mock_rendered_content)
        mock_convert_chat.assert_called_once_with(mock_chat_history_raw)
        mock_execute_llm.assert_called_once_with(mock_service, mock_chat_history, None, None)
        mock_credential.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("llm_ci_runner.core.setup_llm_service")
    @patch("llm_ci_runner.core.load_template_from_string")
    @patch("llm_ci_runner.core.execute_llm_with_chat_history")
    async def test_run_llm_task_sk_yaml_template_string_workflow(
        self,
        mock_execute_llm,
        mock_load_template,
        mock_setup_service,
    ):
        """Test successful run_llm_task with SK YAML template content."""
        # given
        template_content = """
name: analyze_template
description: Analyze input text
template: "Analyze: {{input_text}}"
input_variables:
  - name: input_text
    description: Text to analyze
execution_settings:
  azure_openai:
    temperature: 0.1
"""
        template_format = "semantic-kernel"
        template_vars = {"input_text": "Sample data"}
        expected_response = {"analysis": "positive", "confidence": 0.8}

        # Mock service setup
        mock_service = Mock()
        mock_credential = Mock()
        mock_setup_service.return_value = (mock_service, mock_credential)
        mock_credential.close = AsyncMock()

        # Mock template loading - SK YAML returns KernelFunctionFromPrompt
        from semantic_kernel.functions.kernel_function_from_prompt import (
            KernelFunctionFromPrompt,
        )

        mock_template = Mock(spec=KernelFunctionFromPrompt)
        mock_load_template.return_value = mock_template

        # Mock kernel execution for SK templates
        with patch("llm_ci_runner.core._create_kernel_with_service") as mock_create_kernel:
            mock_kernel = Mock()
            mock_create_kernel.return_value = mock_kernel

            # Mock kernel.invoke result
            mock_chat_content = Mock()
            mock_chat_content.content = '{"analysis": "positive", "confidence": 0.8}'
            mock_result = Mock()
            mock_result.value = [mock_chat_content]
            mock_kernel.invoke = AsyncMock(return_value=mock_result)

            # Mock JSON output requirement
            with patch("llm_ci_runner.core._template_requires_json_output") as mock_requires_json:
                mock_requires_json.return_value = True

                # when
                result = await run_llm_task(
                    template_content=template_content,
                    template_format=template_format,
                    template_vars=template_vars,
                )

                # then
                assert result == expected_response

                # Verify SK workflow steps
                mock_setup_service.assert_called_once()
                mock_load_template.assert_called_once_with(template_content, template_format)
                mock_create_kernel.assert_called_once_with(mock_service)
                mock_kernel.invoke.assert_called_once()
                mock_credential.close.assert_called_once()


class TestLoadTemplateFromString:
    """Tests for load_template_from_string helper function."""

    @pytest.mark.asyncio
    async def test_load_handlebars_template_from_string(self):
        """Test loading Handlebars template from string content."""
        # given
        template_content = "Hello {{name}}!"
        template_format = "handlebars"

        # when
        result = await load_template_from_string(template_content, template_format)

        # then
        # Verify we get a HandlebarsPromptTemplate instance
        from semantic_kernel.prompt_template import HandlebarsPromptTemplate

        assert isinstance(result, HandlebarsPromptTemplate)

    @pytest.mark.asyncio
    async def test_load_jinja2_template_from_string(self):
        """Test loading Jinja2 template from string content."""
        # given
        template_content = "Hello {{ name }}!"
        template_format = "jinja2"

        # when
        result = await load_template_from_string(template_content, template_format)

        # then
        # Verify we get a Jinja2PromptTemplate instance
        from semantic_kernel.prompt_template import Jinja2PromptTemplate

        assert isinstance(result, Jinja2PromptTemplate)

    @pytest.mark.asyncio
    async def test_load_sk_yaml_template_from_string(self):
        """Test loading SK YAML template from string content."""
        # given
        template_content = """
name: test_template
description: Test template
template: "Hello {{name}}!"
input_variables:
  - name: name
    description: Name to greet
"""
        template_format = "semantic-kernel"

        # when
        result = await load_template_from_string(template_content, template_format)

        # then
        # Verify we get a KernelFunctionFromPrompt instance
        from semantic_kernel.functions.kernel_function_from_prompt import (
            KernelFunctionFromPrompt,
        )

        assert isinstance(result, KernelFunctionFromPrompt)
        assert result.name == "test_template"

    @pytest.mark.asyncio
    async def test_load_template_from_string_invalid_format(self):
        """Test that invalid template format raises error."""
        # given
        template_content = "Hello {{name}}!"
        template_format = "unsupported_format"

        # when & then
        with pytest.raises(
            InputValidationError,
            match="Unsupported template format: unsupported_format",
        ):
            await load_template_from_string(template_content, template_format)
