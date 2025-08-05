"""
Unit tests for core helper functions in llm_ci_runner/core.py

Tests _extract_model_id_from_yaml, _create_azure_service_with_model,
_load_template_variables, _detect_template_format, _template_requires_json_output,
and cli_main functions with heavy mocking following the Given-When-Then pattern.
"""

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from llm_ci_runner.core import (
    _create_azure_service_with_model,
    _detect_template_format,
    _extract_model_id_from_yaml,
    _load_template_variables,
    _process_template_unified,
    _template_requires_json_output,
    cli_main,
)
from llm_ci_runner.exceptions import SchemaValidationError


class TestExtractModelIdFromYaml:
    """Tests for _extract_model_id_from_yaml function."""

    def test_extract_model_id_success_with_valid_yaml_function(self):
        """Test successful model_id extraction from YAML function."""
        # given
        mock_yaml_function = Mock()
        mock_yaml_function.prompt_execution_settings = {"azure_openai": Mock()}
        mock_azure_settings = mock_yaml_function.prompt_execution_settings["azure_openai"]
        mock_azure_settings.extension_data = {"model_id": "gpt-4.1-stable"}

        # when
        result = _extract_model_id_from_yaml(mock_yaml_function)

        # then
        assert result == "gpt-4.1-stable"

    def test_extract_model_id_with_non_string_model_id(self):
        """Test extraction when model_id is not a string."""
        # given
        mock_yaml_function = Mock()
        mock_yaml_function.prompt_execution_settings = {"azure_openai": Mock()}
        mock_azure_settings = mock_yaml_function.prompt_execution_settings["azure_openai"]
        mock_azure_settings.extension_data = {"model_id": 123}  # Non-string value

        # when
        result = _extract_model_id_from_yaml(mock_yaml_function)

        # then
        assert result is None

    def test_extract_model_id_no_prompt_execution_settings(self):
        """Test extraction when no prompt_execution_settings attribute."""
        # given
        mock_yaml_function = Mock()
        # Mock hasattr to return False for prompt_execution_settings
        with patch("builtins.hasattr", return_value=False):
            # when
            result = _extract_model_id_from_yaml(mock_yaml_function)

        # then
        assert result is None

    def test_extract_model_id_no_azure_openai_settings(self):
        """Test extraction when no azure_openai in settings."""
        # given
        mock_yaml_function = Mock()
        mock_yaml_function.prompt_execution_settings = {
            "openai": Mock()  # Different provider
        }

        # when
        result = _extract_model_id_from_yaml(mock_yaml_function)

        # then
        assert result is None

    def test_extract_model_id_no_extension_data(self):
        """Test extraction when azure_openai has no extension_data."""
        # given
        mock_yaml_function = Mock()
        mock_yaml_function.prompt_execution_settings = {"azure_openai": Mock()}
        # Mock hasattr to return False for extension_data
        with patch("builtins.hasattr", return_value=False):
            # when
            result = _extract_model_id_from_yaml(mock_yaml_function)

        # then
        assert result is None

    def test_extract_model_id_no_model_id_in_extension_data(self):
        """Test extraction when extension_data has no model_id."""
        # given
        mock_yaml_function = Mock()
        mock_yaml_function.prompt_execution_settings = {"azure_openai": Mock()}
        mock_azure_settings = mock_yaml_function.prompt_execution_settings["azure_openai"]
        mock_azure_settings.extension_data = {"temperature": 0.7}  # No model_id

        # when
        result = _extract_model_id_from_yaml(mock_yaml_function)

        # then
        assert result is None

    def test_extract_model_id_exception_handling(self):
        """Test exception handling in model_id extraction."""
        # given
        mock_yaml_function = Mock()
        mock_yaml_function.prompt_execution_settings = Mock()
        # Mock to raise exception when accessing get method
        mock_yaml_function.prompt_execution_settings.get.side_effect = AttributeError("Test error")

        # when
        with patch("llm_ci_runner.core.LOGGER") as mock_logger:
            result = _extract_model_id_from_yaml(mock_yaml_function)

        # then
        assert result is None
        mock_logger.warning.assert_called_once()
        assert "Error extracting model_id from YAML" in mock_logger.warning.call_args[0][0]


class TestCreateAzureServiceWithModel:
    """Tests for _create_azure_service_with_model function."""

    @pytest.mark.asyncio
    async def test_create_azure_service_with_api_key(self, mock_environment_variables):
        """Test service creation with API key authentication."""
        # given
        model_id = "gpt-4.1-stable"

        with patch(
            "semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion.AzureChatCompletion"
        ) as mock_azure_completion:
            mock_service = AsyncMock()
            mock_azure_completion.return_value = mock_service

            # when
            result = await _create_azure_service_with_model(model_id)

            # then
            service, credential = result
            assert service == mock_service
            assert credential is None  # API key auth returns None for credential
            mock_azure_completion.assert_called_once_with(
                service_id="azure_openai",
                endpoint="https://test.openai.azure.com/",
                api_key="test-api-key",
                deployment_name=model_id,
                api_version="2024-12-01-preview",
            )

    @pytest.mark.asyncio
    async def test_create_azure_service_with_rbac_auth(self, monkeypatch, mock_environment_variables):
        """Test service creation with RBAC authentication."""
        # given
        model_id = "gpt-4.1-nano"
        monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://test.openai.azure.com/")
        monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)  # Remove API key

        with (
            patch(
                "semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion.AzureChatCompletion"
            ) as mock_azure_completion,
            patch("azure.identity.aio.DefaultAzureCredential") as mock_credential,
            patch("azure.identity.aio.get_bearer_token_provider") as mock_token_provider,
        ):
            mock_service = AsyncMock()
            mock_azure_completion.return_value = mock_service
            mock_cred_instance = AsyncMock()
            mock_credential.return_value = mock_cred_instance
            mock_token_prov_instance = AsyncMock()
            mock_token_provider.return_value = mock_token_prov_instance

            # when
            result = await _create_azure_service_with_model(model_id)

            # then
            service, credential = result
            assert service == mock_service
            assert credential == mock_cred_instance  # RBAC auth returns the credential instance
            mock_credential.assert_called_once()
            mock_token_provider.assert_called_once_with(
                mock_cred_instance, "https://cognitiveservices.azure.com/.default"
            )
            mock_azure_completion.assert_called_once_with(
                service_id="azure_openai",
                endpoint="https://test.openai.azure.com/",
                deployment_name=model_id,
                api_version="2024-12-01-preview",
                ad_token_provider=mock_token_prov_instance,
            )

    @pytest.mark.asyncio
    async def test_create_azure_service_missing_endpoint_raises_error(self, monkeypatch):
        """Test service creation error when endpoint is missing."""
        # given
        model_id = "gpt-4.1-stable"
        monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)  # Remove endpoint

        # when & then
        with pytest.raises(ValueError, match="AZURE_OPENAI_ENDPOINT environment variable is required"):
            await _create_azure_service_with_model(model_id)

    @pytest.mark.asyncio
    async def test_create_azure_service_with_custom_api_version(self, monkeypatch):
        """Test service creation with custom API version."""
        # given
        model_id = "gpt-4.1-mini"
        custom_api_version = "2024-10-01-preview"
        monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://test.openai.azure.com/")
        monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("AZURE_OPENAI_API_VERSION", custom_api_version)

        with patch(
            "semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion.AzureChatCompletion"
        ) as mock_azure_completion:
            mock_service = AsyncMock()
            mock_azure_completion.return_value = mock_service

            # when
            result = await _create_azure_service_with_model(model_id)

            # then
            service, credential = result
            assert credential is None  # API key auth returns None for credential
            call_args = mock_azure_completion.call_args[1]
            assert call_args["api_version"] == custom_api_version


class TestTemplateUtilities:
    """Tests for _load_template_variables and _detect_template_format functions."""

    def test_load_template_variables_with_file(self, temp_dir):
        """Test loading template variables from file."""
        # given
        vars_file = temp_dir / "test_vars.yaml"
        vars_file.write_text("key: value\ntest: data")

        with patch("llm_ci_runner.core.load_template_vars") as mock_load_vars:
            mock_load_vars.return_value = {"key": "value", "test": "data"}

            # when
            result = _load_template_variables(str(vars_file))

            # then
            assert result == {"key": "value", "test": "data"}
            mock_load_vars.assert_called_once_with(Path(str(vars_file)))

    def test_load_template_variables_without_file(self):
        """Test loading template variables with no file specified."""
        # given
        template_vars_file = None

        with patch("llm_ci_runner.core.LOGGER") as mock_logger:
            # when
            result = _load_template_variables(template_vars_file)

            # then
            assert result == {}
            mock_logger.info.assert_called_once_with("📝 No template variables provided - using defaults")

    @pytest.mark.parametrize(
        "extension, expected_format",
        [
            pytest.param(".yaml", "semantic-kernel", id="yaml_extension"),
            pytest.param(".yml", "semantic-kernel", id="yml_extension"),
            pytest.param(".hbs", "handlebars", id="handlebars_extension"),
            pytest.param(".j2", "jinja2", id="jinja2_extension"),
            pytest.param(".jinja", "jinja2", id="jinja_extension"),
        ],
    )
    def test_detect_template_format_known_extensions(self, extension, expected_format):
        """Test template format detection for known extensions."""
        # given
        template_file = f"test{extension}"

        # when
        result = _detect_template_format(template_file)

        # then
        assert result == expected_format

    def test_detect_template_format_unknown_extension_defaults_to_handlebars(self):
        """Test template format detection fallback for unknown extensions."""
        # given
        template_file = "test.unknown"

        # when
        result = _detect_template_format(template_file)

        # then
        assert result == "handlebars"

    def test_detect_template_format_no_extension_defaults_to_handlebars(self):
        """Test template format detection fallback for no extension."""
        # given
        template_file = "test_template"

        # when
        result = _detect_template_format(template_file)

        # then
        assert result == "handlebars"


class TestTemplateRequiresJsonOutput:
    """Tests for _template_requires_json_output function."""

    def test_template_requires_json_with_azure_json_schema(self):
        """Test JSON requirement detection with Azure json_schema."""
        # given
        mock_template = Mock()
        mock_template.prompt_execution_settings = {"azure_openai": Mock()}
        mock_azure_settings = mock_template.prompt_execution_settings["azure_openai"]
        mock_azure_settings.extension_data = {
            "response_format": {"type": "json_schema", "json_schema": {"name": "test_schema"}}
        }

        # when
        result = _template_requires_json_output(mock_template)

        # then
        assert result is True

    def test_template_requires_json_with_openai_json_schema(self):
        """Test JSON requirement detection with OpenAI json_schema."""
        # given
        mock_template = Mock()
        mock_template.prompt_execution_settings = {"openai": Mock()}
        mock_openai_settings = mock_template.prompt_execution_settings["openai"]
        mock_openai_settings.extension_data = {
            "response_format": {"type": "json_schema", "json_schema": {"name": "test_schema"}}
        }

        # when
        result = _template_requires_json_output(mock_template)

        # then
        assert result is True

    def test_template_requires_json_no_json_schema_type(self):
        """Test when response_format type is not json_schema."""
        # given
        mock_template = Mock()
        mock_template.prompt_execution_settings = {"azure_openai": Mock()}
        mock_azure_settings = mock_template.prompt_execution_settings["azure_openai"]
        mock_azure_settings.extension_data = {
            "response_format": {
                "type": "text"  # Not json_schema
            }
        }

        # when
        result = _template_requires_json_output(mock_template)

        # then
        assert result is False

    def test_template_requires_json_no_prompt_execution_settings(self):
        """Test when template has no prompt_execution_settings."""
        # given
        mock_template = Mock()
        # Mock hasattr to return False
        with patch("builtins.hasattr", return_value=False):
            # when
            result = _template_requires_json_output(mock_template)

        # then
        assert result is False

    def test_template_requires_json_no_response_format(self):
        """Test when extension_data has no response_format."""
        # given
        mock_template = Mock()
        mock_template.prompt_execution_settings = {"azure_openai": Mock()}
        mock_azure_settings = mock_template.prompt_execution_settings["azure_openai"]
        mock_azure_settings.extension_data = {
            "temperature": 0.7  # No response_format
        }

        # when
        result = _template_requires_json_output(mock_template)

        # then
        assert result is False

    def test_template_requires_json_exception_handling(self):
        """Test exception handling in JSON detection."""
        # given
        mock_template = Mock()
        # Mock to raise exception
        with patch("builtins.hasattr", side_effect=AttributeError("Test error")):
            # when
            result = _template_requires_json_output(mock_template)

        # then
        assert result is False

    def test_template_requires_json_no_json_schema_key(self):
        """Test when response_format has json_schema type but no json_schema key."""
        # given
        mock_template = Mock()
        mock_template.prompt_execution_settings = {"azure_openai": Mock()}
        mock_azure_settings = mock_template.prompt_execution_settings["azure_openai"]
        mock_azure_settings.extension_data = {
            "response_format": {
                "type": "json_schema"
                # Missing json_schema key
            }
        }

        # when
        result = _template_requires_json_output(mock_template)

        # then
        assert result is False


class TestCliMain:
    """Tests for cli_main function."""

    def test_cli_main_success(self):
        """Test successful CLI execution."""
        # given
        mock_main_func = AsyncMock()

        with (
            patch("llm_ci_runner.core.asyncio.run") as mock_run,
            patch("llm_ci_runner.core.main", mock_main_func),
        ):
            mock_run.return_value = None

            # when
            cli_main()

            # then
            mock_run.assert_called_once()
            # Verify that asyncio.run was called with main() - just check it was called

    def test_cli_main_keyboard_interrupt(self):
        """Test CLI handling of keyboard interrupt (Ctrl+C)."""
        # given
        mock_main_func = AsyncMock()

        with (
            patch("llm_ci_runner.core.asyncio.run") as mock_run,
            patch("llm_ci_runner.core.main", mock_main_func),
            patch("builtins.print") as mock_print,
            patch("sys.exit") as mock_exit,
        ):
            mock_run.side_effect = KeyboardInterrupt()

            # when
            cli_main()

            # then
            mock_print.assert_called_once_with("\n⏹️  Interrupted by user")
            mock_exit.assert_called_once_with(130)

    def test_cli_main_exception_handling(self):
        """Test CLI error handling for general exceptions."""
        # given
        test_error = Exception("Test error")
        mock_main_func = AsyncMock()

        with (
            patch("llm_ci_runner.core.asyncio.run") as mock_run,
            patch("llm_ci_runner.core.main", mock_main_func),
            patch("builtins.print") as mock_print,
            patch("sys.exit") as mock_exit,
        ):
            mock_run.side_effect = test_error

            # when
            cli_main()

            # then
            mock_print.assert_called_once_with("❌ Fatal error: Test error")
            mock_exit.assert_called_once_with(1)


class TestProcessTemplateUnified:
    """Tests for _process_template_unified function covering missing lines."""

    @pytest.mark.asyncio
    async def test_dynamic_service_creation_fallback_when_no_yaml_model_id(self):
        """Test fallback to environment service when YAML has no model_id (covers lines 296-298)."""
        # given
        mock_template = AsyncMock()
        mock_service = Mock()
        template_vars = {"key": "value"}

        with (
            patch("llm_ci_runner.core._extract_model_id_from_yaml") as mock_extract,
            patch("llm_ci_runner.core._create_kernel_with_service") as mock_create_kernel,
            patch("llm_ci_runner.core.render_template") as mock_render_template,
            patch("llm_ci_runner.core.execute_llm_with_chat_history") as mock_execute,
            patch("llm_ci_runner.core.isinstance") as mock_isinstance,  # Mock isinstance check
            patch("llm_ci_runner.core.LOGGER") as mock_logger,
        ):
            # Mock isinstance to return True for KernelFunctionFromPrompt check
            mock_isinstance.return_value = True
            mock_extract.return_value = None  # No model_id in YAML
            mock_kernel = MagicMock()
            mock_result = Mock()
            mock_result.value = [Mock()]
            mock_result.value[0].content = "test response"
            mock_result.value[0].__str__ = lambda self=mock_result.value[0]: "test response"
            mock_kernel.invoke = AsyncMock(return_value=mock_result)
            mock_create_kernel.return_value = mock_kernel
            # Use proper message format that parse_rendered_template_to_chat_history expects
            mock_render_template.return_value = '<message role="user">Test message</message>'
            mock_execute.return_value = "test response"

            # Mock template requires json check
            with patch("llm_ci_runner.core._template_requires_json_output", return_value=False):
                # when
                result = await _process_template_unified(
                    mock_template, "semantic-kernel", template_vars, mock_service, None, None
                )

            # then - should return kernel response and use environment service (covers lines 296-298)
            assert result == "test response"
            mock_create_kernel.assert_called_once_with(
                mock_service
            )  # Called with env service            # then - should log environment model usage (covers lines 296-298)
            mock_logger.info.assert_any_call("✅ Using environment model")
            mock_create_kernel.assert_called_with(mock_service)

    @pytest.mark.asyncio
    async def test_dynamic_service_creation_exception_handling(self):
        """Test exception handling in dynamic service creation (covers lines 304-307)."""
        # given
        mock_template = AsyncMock()
        mock_service = Mock()
        template_vars = {"key": "value"}

        with (
            patch("llm_ci_runner.core._extract_model_id_from_yaml") as mock_extract,
            patch("llm_ci_runner.core._create_azure_service_with_model") as mock_create_service,
            patch("llm_ci_runner.core._create_kernel_with_service") as mock_create_kernel,
            patch("llm_ci_runner.core.render_template") as mock_render_template,
            patch("llm_ci_runner.core.execute_llm_with_chat_history") as mock_execute,
            patch("llm_ci_runner.core.isinstance") as mock_isinstance,  # Mock isinstance check
            patch("llm_ci_runner.core.LOGGER") as mock_logger,
        ):
            # Mock isinstance to return True for KernelFunctionFromPrompt check
            mock_isinstance.return_value = True
            mock_extract.return_value = "test-model"
            mock_create_service.side_effect = ValueError("Service creation failed")
            # Setup two kernels for dynamic and fallback
            mock_kernel_dynamic = MagicMock()
            mock_kernel_fallback = MagicMock()
            mock_result = Mock()
            mock_result.value = [Mock()]
            mock_result.value[0].content = "test response"
            mock_result.value[0].__str__ = lambda self=mock_result.value[0]: "test response"
            mock_kernel_dynamic.invoke = AsyncMock(return_value=mock_result)
            mock_kernel_fallback.invoke = AsyncMock(return_value=mock_result)
            mock_create_kernel.side_effect = [mock_kernel_dynamic, mock_kernel_fallback]
            # Use proper message format
            mock_render_template.return_value = '<message role="user">Test message</message>'
            mock_execute.return_value = "test response"

            # Mock template requires json check
            with patch("llm_ci_runner.core._template_requires_json_output", return_value=False):
                # when
                result = await _process_template_unified(
                    mock_template, "semantic-kernel", template_vars, mock_service, None, None
                )

            # then - should log warning and fallback (covers lines 304-307)
            assert result == "test response"
            mock_logger.warning.assert_called_once_with(
                "⚠️ Dynamic service creation failed, using environment service: Service creation failed"
            )
            # Should call create_kernel once for fallback
            assert mock_create_kernel.call_count == 1

    @pytest.mark.asyncio
    async def test_sk_template_json_decode_error_handling(self):
        """Test JSON decode error handling in SK template processing (covers lines 324-334)."""
        # given
        mock_template = AsyncMock()
        mock_service = Mock()
        template_vars = {"key": "value"}

        with (
            patch("llm_ci_runner.core._extract_model_id_from_yaml") as mock_extract,
            patch("llm_ci_runner.core._create_kernel_with_service") as mock_create_kernel,
            patch("llm_ci_runner.core._template_requires_json_output") as mock_requires_json,
            patch("llm_ci_runner.core.render_template") as mock_render_template,
            patch("llm_ci_runner.core.isinstance") as mock_isinstance,  # Mock isinstance check
            patch("llm_ci_runner.core.LOGGER") as mock_logger,
        ):
            # Mock isinstance to return True for KernelFunctionFromPrompt check
            mock_isinstance.return_value = True
            mock_extract.return_value = None
            mock_kernel = MagicMock()
            mock_create_kernel.return_value = mock_kernel
            mock_requires_json.return_value = True  # Template expects JSON
            # Use proper message format
            mock_render_template.return_value = '<message role="user">Test message</message>'

            # Mock kernel.invoke to return invalid JSON that will trigger the JSONDecodeError
            mock_result = Mock()
            mock_result.value = [Mock()]
            mock_result.value[0].content = "invalid json content {not valid"
            mock_kernel.invoke = AsyncMock(return_value=mock_result)

            # when
            with pytest.raises(SchemaValidationError, match="Schema enforcement failed: Invalid JSON response"):
                # Should raise SchemaValidationError due to invalid JSON
                result = await _process_template_unified(
                    mock_template, "semantic-kernel", template_vars, mock_service, None, None
                )
