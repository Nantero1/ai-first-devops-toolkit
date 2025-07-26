"""
Integration tests for string-based template functionality in LLM CI Runner.

Tests full workflows using run_llm_task with template_content parameter,
demonstrating real-world usage patterns with mocked external HTTP API calls.
"""

import pytest

from llm_ci_runner import run_llm_task


class TestStringTemplateIntegration:
    """Integration tests for string-based template workflows."""

    @pytest.mark.asyncio
    async def test_handlebars_template_string_integration(
        self,
        mock_azure_openai_responses,
    ):
        """Test complete Handlebars template workflow with string content."""
        # given
        template_content = """
<message role="system">You are a helpful assistant that provides concise responses.</message>
<message role="user">Hello {{name}}! Please analyze this data: {{data}}</message>
"""
        template_vars = {
            "name": "AI Assistant",
            "data": "Customer satisfaction ratings: 4.2/5.0 (based on 150 reviews)",
        }

        # when
        result = await run_llm_task(
            template_content=template_content,
            template_format="handlebars",
            template_vars=template_vars,
        )

        # then
        assert isinstance(result, str)
        assert len(result) > 0
        # The actual response content depends on the HTTP mock

    @pytest.mark.asyncio
    async def test_jinja2_template_string_integration(
        self,
        mock_azure_openai_responses,
    ):
        """Test complete Jinja2 template workflow with string content."""
        # given
        template_content = """
<message role="system">You are a code review assistant.</message>
<message role="user">
Review this code for issues:

{% for file in files %}
File: {{ file.name }}
Language: {{ file.language }}
Lines: {{ file.lines }}

{{ file.content }}

{% endfor %}

Provide a structured analysis.
</message>
"""
        template_vars = {
            "files": [
                {
                    "name": "main.py",
                    "language": "Python",
                    "lines": 25,
                    "content": "def hello_world():\n    print('Hello, World!')\n    return True",
                }
            ]
        }

        # when
        result = await run_llm_task(
            template_content=template_content,
            template_format="jinja2",
            template_vars=template_vars,
        )

        # then
        assert isinstance(result, str)
        assert len(result) > 0
        # The actual response content depends on the HTTP mock

    @pytest.mark.asyncio
    async def test_sk_yaml_template_loading_integration(self):
        """Test that SK YAML template string loading works correctly."""
        # given
        template_content = """
name: sentiment_analyzer
description: Analyze sentiment of input text with structured output
template: |
  Analyze the sentiment of this text: "{{$input_text}}"
  
  Provide your analysis in the specified JSON format.
input_variables:
  - name: input_text
    description: Text to analyze for sentiment
execution_settings:
  azure_openai:
    temperature: 0.1
    max_tokens: 200
    response_format:
      type: json_schema
      json_schema:
        name: sentiment_analysis
        schema:
          type: object
          properties:
            sentiment:
              type: string
              enum: ["positive", "negative", "neutral"]
            confidence:
              type: number
              minimum: 0
              maximum: 1
            reasoning:
              type: string
          required: ["sentiment", "confidence", "reasoning"]
          additionalProperties: false
"""

        # when - test template loading (not full execution)
        from llm_ci_runner import load_template_from_string
        from semantic_kernel.functions.kernel_function_from_prompt import KernelFunctionFromPrompt

        result = await load_template_from_string(template_content, "semantic-kernel")

        # then
        # Verify we get a proper SK template with correct metadata
        assert isinstance(result, KernelFunctionFromPrompt)
        assert result.name == "sentiment_analyzer"
        assert result.description == "Analyze sentiment of input text with structured output"
        assert "azure_openai" in result.prompt_execution_settings

    @pytest.mark.asyncio
    async def test_string_template_validation_integration(self):
        """Test that validation errors are properly handled in integration scenarios."""
        # given
        template_content = "Hello {{name}}!"
        # Missing template_format - should trigger validation error

        # when & then
        with pytest.raises(Exception) as exc_info:  # InputValidationError
            await run_llm_task(
                template_content=template_content,
                # template_format missing
                template_vars={"name": "World"},
            )

        # Verify we get a meaningful error message
        assert "template_format is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_mutually_exclusive_parameters_validation(self):
        """Test validation of mutually exclusive parameters."""
        # when & then
        with pytest.raises(Exception) as exc_info:  # InputValidationError
            await run_llm_task(
                template_content="Hello {{name}}!",
                template_format="handlebars",
                template_vars={"name": "World"},
                template_vars_file="vars.yaml",  # Conflicts with template_vars
            )

        # Verify we get appropriate error message
        assert "mutually exclusive" in str(exc_info.value) or "Cannot specify both" in str(exc_info.value)
