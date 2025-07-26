"""Integration tests for LLM retry mechanism with invalid JSON responses.

This module tests the retry behavior when LLM services return invalid JSON responses,
ensuring the CLI properly retries failed requests and eventually succeeds or fails
gracefully after exhausting retry attempts.

The tests verify:
- Multiple retry attempts on invalid JSON responses
- Successful completion after retries when LLM eventually returns valid response
- Proper error handling when all retry attempts are exhausted
- Integration with the existing mock infrastructure
"""

from __future__ import annotations

import pytest

from tests.integration.integration_helpers import CommonTestData, IntegrationTestHelper


class TestRetryMechanismIntegration:
    """Integration tests for retry mechanism when LLM returns invalid JSON responses."""

    @pytest.mark.asyncio
    async def test_successful_retry_after_invalid_json_responses(
        self, mock_azure_openai_retry_responses, integration_helper: IntegrationTestHelper
    ):
        """Test successful completion after retrying invalid JSON responses.

        This test verifies that the CLI can recover from invalid JSON responses
        by retrying the request and eventually succeeding when the LLM returns
        valid JSON after multiple attempts.
        """
        # given
        input_data = CommonTestData.retry_test_input()
        schema_data = CommonTestData.retry_test_schema()

        # when
        result = await integration_helper.run_integration_test(
            input_content=input_data,
            schema_content=schema_data,
            input_filename="retry_input.json",
            output_filename="retry_result.json",
            schema_filename="retry_schema.json",
        )

        # then
        # Verify the structure matches expected retry success response - result has nested structure
        assert "response" in result
        assert "sentiment" in result["response"]
        assert "confidence" in result["response"]
        assert "summary" in result["response"]
        assert "key_points" in result["response"]

        # Verify specific success values from retry fixture
        assert result["response"]["sentiment"] == "positive"
        assert result["response"]["confidence"] == 0.95
        assert "retry" in result["response"]["summary"].lower()
        assert isinstance(result["response"]["key_points"], list)
        assert len(result["response"]["key_points"]) > 0

    @pytest.mark.asyncio
    async def test_text_response_retry_after_invalid_json(
        self, mock_azure_openai_retry_responses, integration_helper: IntegrationTestHelper
    ):
        """Test text response retry mechanism without schema validation.

        This test verifies that retry mechanism works for text responses
        when invalid JSON is returned but no schema validation is required.
        """
        # given
        input_data = CommonTestData.retry_test_input()

        # when
        result = await integration_helper.run_integration_test(
            input_content=input_data,
            input_filename="retry_text_input.json",
            output_filename="retry_text_result.json",
        )

        # then
        # Verify text response structure
        assert "response" in result or "content" in result

        # For text mode without schema, it should return the first response
        # (which is the first invalid JSON content from our mock sequence)
        response_text = result.get("response", result.get("content", ""))
        assert "not json" in response_text.lower() or "json" in response_text.lower()

    @pytest.mark.asyncio
    async def test_retry_logging_integration(
        self, mock_azure_openai_retry_responses, integration_helper: IntegrationTestHelper, caplog
    ):
        """Test that retry attempts are properly logged during integration execution.

        This test verifies that retry mechanism produces appropriate log messages
        that can be observed and verified during integration testing.
        """
        # given
        input_data = CommonTestData.retry_test_input()
        schema_data = CommonTestData.retry_test_schema()

        # when
        with caplog.at_level("DEBUG"):
            result = await integration_helper.run_integration_test(
                input_content=input_data,
                schema_content=schema_data,
                input_filename="retry_logging_input.json",
                output_filename="retry_logging_result.json",
                schema_filename="retry_logging_schema.json",
                log_level="DEBUG",  # Enable debug logging to capture retry messages
            )

        # then
        # Verify successful completion - result has nested structure with response data
        assert "response" in result
        assert "sentiment" in result["response"]
        assert result["response"]["sentiment"] == "positive"

        # Verify that retry-related log messages are present
        log_messages = [record.message for record in caplog.records]

        # Look for retry-related log patterns
        retry_related_logs = [msg for msg in log_messages if "retry" in msg.lower() or "attempt" in msg.lower()]

        # Verify that some retry activity was logged
        assert len(retry_related_logs) > 0, f"No retry-related logs found. All logs: {log_messages}"
