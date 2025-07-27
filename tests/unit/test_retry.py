"""
Unit tests for retry utilities in llm_ci_runner.

Tests retry logic for OpenAI and Azure API exceptions, ensuring proper retry behavior
for transient errors while avoiding retries for permanent failures.

Enhanced with comprehensive timeout + retry interaction tests.
"""

import asyncio
from unittest.mock import Mock, patch

import pytest
from azure.core.exceptions import (
    ClientAuthenticationError,
    HttpResponseError,
    ServiceRequestError,
    ServiceResponseError,
)
from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    RateLimitError,
)

from llm_ci_runner.retry import (
    create_retry_with_timeout_decorator,
    get_timeout_from_env,
    should_retry_azure_exception,
    should_retry_llm_exception,
    should_retry_openai_exception,
)


class TestShouldRetryOpenAIException:
    """Tests for OpenAI exception retry logic."""

    def test_should_retry_connection_error(self):
        """Test that APIConnectionError should be retried."""
        # given
        exception = Mock(spec=APIConnectionError)

        # when
        result = should_retry_openai_exception(exception)

        # then
        assert result is True

    def test_should_retry_timeout_error(self):
        """Test that APITimeoutError should be retried."""
        # given
        exception = Mock(spec=APITimeoutError)

        # when
        result = should_retry_openai_exception(exception)

        # then
        assert result is True

    def test_should_retry_rate_limit_error(self):
        """Test that RateLimitError should be retried."""
        # given
        exception = Mock(spec=RateLimitError)

        # when
        result = should_retry_openai_exception(exception)

        # then
        assert result is True

    @pytest.mark.parametrize(
        "status_code, expected",
        [
            pytest.param(500, True, id="internal_server_error"),
            pytest.param(502, True, id="bad_gateway"),
            pytest.param(503, True, id="service_unavailable"),
            pytest.param(504, True, id="gateway_timeout"),
            pytest.param(599, True, id="network_connect_timeout"),
        ],
    )
    def test_should_retry_server_errors(self, status_code, expected):
        """Test that 5xx server errors should be retried."""
        # given
        exception = Mock(spec=APIError)
        exception.status_code = status_code

        # when
        result = should_retry_openai_exception(exception)

        # then
        assert result is expected

    @pytest.mark.parametrize(
        "status_code, expected",
        [
            pytest.param(400, False, id="bad_request"),
            pytest.param(401, False, id="unauthorized"),
            pytest.param(403, False, id="forbidden"),
            pytest.param(404, False, id="not_found"),
            pytest.param(422, False, id="unprocessable_entity"),
        ],
    )
    def test_should_not_retry_client_errors(self, status_code, expected):
        """Test that 4xx client errors should not be retried."""
        # given
        exception = Mock(spec=APIError)
        exception.status_code = status_code

        # when
        result = should_retry_openai_exception(exception)

        # then
        assert result is expected

    def test_should_not_retry_api_error_without_status_code(self):
        """Test that APIError without status_code should not be retried."""
        # given
        exception = Mock(spec=APIError)
        # Don't set status_code attribute to test the missing attribute case

        # when
        result = should_retry_openai_exception(exception)

        # then
        assert result is False

    def test_should_not_retry_unknown_exception(self):
        """Test that unknown exceptions should not be retried."""
        # given
        exception = ValueError("Unknown error")

        # when
        result = should_retry_openai_exception(exception)

        # then
        assert result is False


class TestShouldRetryAzureException:
    """Tests for Azure exception retry logic."""

    def test_should_not_retry_authentication_error(self):
        """Test that ClientAuthenticationError should not be retried."""
        # given
        exception = ClientAuthenticationError("Authentication failed")

        # when
        result = should_retry_azure_exception(exception)

        # then
        assert result is False

    def test_should_retry_service_request_error(self):
        """Test that ServiceRequestError should be retried."""
        # given
        exception = ServiceRequestError("Service request failed")

        # when
        result = should_retry_azure_exception(exception)

        # then
        assert result is True

    def test_should_retry_service_response_error(self):
        """Test that ServiceResponseError should be retried."""
        # given
        exception = ServiceResponseError("Service response failed")

        # when
        result = should_retry_azure_exception(exception)

        # then
        assert result is True

    @pytest.mark.parametrize(
        "status_code, expected",
        [
            pytest.param(408, True, id="request_timeout"),
            pytest.param(429, True, id="too_many_requests"),
            pytest.param(500, True, id="internal_server_error"),
            pytest.param(502, True, id="bad_gateway"),
            pytest.param(503, True, id="service_unavailable"),
            pytest.param(504, True, id="gateway_timeout"),
        ],
    )
    def test_should_retry_http_response_errors_with_retriable_status(self, status_code, expected):
        """Test that HttpResponseError with retriable status codes should be retried."""
        # given
        exception = HttpResponseError("HTTP error")
        exception.status_code = status_code

        # when
        result = should_retry_azure_exception(exception)

        # then
        assert result is expected

    @pytest.mark.parametrize(
        "status_code, expected",
        [
            pytest.param(400, False, id="bad_request"),
            pytest.param(401, False, id="unauthorized"),
            pytest.param(403, False, id="forbidden"),
            pytest.param(404, False, id="not_found"),
            pytest.param(422, False, id="unprocessable_entity"),
        ],
    )
    def test_should_not_retry_http_response_errors_with_client_status(self, status_code, expected):
        """Test that HttpResponseError with client error status codes should not be retried."""
        # given
        exception = HttpResponseError("HTTP client error")
        exception.status_code = status_code

        # when
        result = should_retry_azure_exception(exception)

        # then
        assert result is expected

    def test_should_not_retry_http_response_error_without_status_code(self):
        """Test that HttpResponseError without status_code should not be retried."""
        # given
        exception = HttpResponseError("HTTP error")

        # when
        result = should_retry_azure_exception(exception)

        # then
        assert result is False

    def test_should_not_retry_unknown_exception(self):
        """Test that unknown exceptions should not be retried."""
        # given
        exception = ValueError("Unknown error")

        # when
        result = should_retry_azure_exception(exception)

        # then
        assert result is False


class TestShouldRetryNetworkException:
    """Tests for network exception retry logic."""

    def test_should_retry_openai_retriable_exception(self):
        """Test that OpenAI retriable exceptions are retried via network logic."""
        # given
        exception = Mock(spec=APIConnectionError)

        # when
        result = should_retry_llm_exception(exception)

        # then
        assert result is True

    def test_should_retry_azure_retriable_exception(self):
        """Test that Azure retriable exceptions are retried via network logic."""
        # given
        exception = ServiceRequestError("Service request failed")

        # when
        result = should_retry_llm_exception(exception)

        # then
        assert result is True

    def test_should_not_retry_non_retriable_exception(self):
        """Test that non-retriable exceptions are not retried via network logic."""
        # given
        exception = Mock(spec=ValueError)

        # when
        result = should_retry_llm_exception(exception)

        # then
        assert result is False

    def test_should_retry_schema_validation_error(self):
        """Test that SchemaValidationError should be retried to allow LLM to fix JSON."""
        # given
        from llm_ci_runner.exceptions import SchemaValidationError

        exception = SchemaValidationError("Invalid JSON schema")

        # when
        result = should_retry_llm_exception(exception)

        # then
        assert result is True  # Covers line 159 in retry.py

    def test_should_not_retry_unknown_exception(self):
        """Test that unknown exceptions are not retried via network logic."""
        # given
        exception = ValueError("Unknown error")

        # when
        result = should_retry_llm_exception(exception)

        # then
        assert result is False


class TestRetryDecorators:
    """Tests for retry decorator configuration and behavior."""

    def test_retry_decorators_exist(self):
        """Test that the retry decorator is available."""
        # given
        from llm_ci_runner.retry import retry_network_operation

        # when / then
        assert retry_network_operation is not None

    def test_retry_decorator_configuration(self):
        """Test that retry decorators have proper configuration."""
        # given
        from llm_ci_runner.retry import (
            DEFAULT_EXPONENTIAL_MULTIPLIER,
            DEFAULT_MAX_RETRIES,
            DEFAULT_MAX_WAIT,
            DEFAULT_MIN_WAIT,
        )

        # when / then
        assert DEFAULT_MAX_RETRIES == 3
        assert DEFAULT_MIN_WAIT == 1
        assert DEFAULT_MAX_WAIT == 30
        assert DEFAULT_EXPONENTIAL_MULTIPLIER == 1


class TestTimeoutConfiguration:
    """Tests for timeout configuration and environment variable handling."""

    def test_get_timeout_from_env_with_valid_value(self):
        """Test getting timeout from environment variable with valid value."""
        # given
        with patch.dict("os.environ", {"TEST_TIMEOUT": "60"}):
            # when
            result = get_timeout_from_env("TEST_TIMEOUT", 30)

            # then
            assert result == 60

    def test_get_timeout_from_env_with_missing_variable(self):
        """Test getting timeout from environment variable when variable is missing."""
        # given
        with patch.dict("os.environ", {}, clear=True):
            # when
            result = get_timeout_from_env("MISSING_TIMEOUT", 45)

            # then
            assert result == 45

    def test_get_timeout_from_env_with_invalid_value(self):
        """Test getting timeout from environment variable with invalid value."""
        # given
        with patch.dict("os.environ", {"INVALID_TIMEOUT": "not_a_number"}):
            # when
            result = get_timeout_from_env("INVALID_TIMEOUT", 30)

            # then
            assert result == 30

    def test_get_timeout_from_env_with_negative_value(self):
        """Test getting timeout from environment variable with negative value."""
        # given
        with patch.dict("os.environ", {"NEGATIVE_TIMEOUT": "-10"}):
            # when
            result = get_timeout_from_env("NEGATIVE_TIMEOUT", 30)

            # then
            assert result == 30

    def test_get_timeout_from_env_with_zero_value(self):
        """Test getting timeout from environment variable with zero value."""
        # given
        with patch.dict("os.environ", {"ZERO_TIMEOUT": "0"}):
            # when
            result = get_timeout_from_env("ZERO_TIMEOUT", 30)

            # then
            assert result == 30


class TestTimeoutRetryIntegration:
    """Tests for timeout + retry integration functionality."""

    @pytest.mark.asyncio
    async def test_timeout_then_success_on_retry(self):
        """Test timeout on first attempt, success on retry."""
        # given
        call_count = 0

        async def slow_then_fast_operation():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                await asyncio.sleep(0.2)  # Will timeout with 0.1s limit
            return "success"

        decorator = create_retry_with_timeout_decorator(timeout_seconds=0.1, max_retries=2)
        decorated_func = decorator(slow_then_fast_operation)

        # when
        result = await decorated_func()

        # then
        assert result == "success"
        assert call_count == 2  # First timeout, second success

    @pytest.mark.asyncio
    async def test_timeout_on_all_retries(self):
        """Test timeout on all retry attempts."""
        # given
        call_count = 0

        async def always_slow_operation():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.2)  # Always times out with 0.1s limit
            return "should not reach"

        decorator = create_retry_with_timeout_decorator(timeout_seconds=0.1, max_retries=2)
        decorated_func = decorator(always_slow_operation)

        # when / then
        with pytest.raises(TimeoutError, match="Always Slow Operation timed out after 0.1s"):
            await decorated_func()

        assert call_count == 2  # Both attempts should timeout and retry

    @pytest.mark.asyncio
    async def test_no_timeout_normal_operation(self):
        """Test normal operation without timeout."""

        # given
        async def fast_operation():
            await asyncio.sleep(0.01)  # Very fast, well under timeout
            return "fast_result"

        decorator = create_retry_with_timeout_decorator(timeout_seconds=1.0)
        decorated_func = decorator(fast_operation)

        # when
        result = await decorated_func()

        # then
        assert result == "fast_result"

    @pytest.mark.asyncio
    async def test_timeout_error_message_includes_env_var_suggestion(self):
        """Test timeout error message includes environment variable suggestion."""

        # given
        async def slow_operation():
            await asyncio.sleep(0.2)
            return "should not reach"

        decorator = create_retry_with_timeout_decorator(timeout_seconds=0.1)
        decorated_func = decorator(slow_operation)

        # when / then
        with pytest.raises(TimeoutError) as exc_info:
            await decorated_func()

        error_message = str(exc_info.value)
        assert "timed out after 0.1s" in error_message
        assert "LLM_TIMEOUT environment variable" in error_message

    @pytest.mark.asyncio
    async def test_multiple_timeout_attempts_then_success(self):
        """Test multiple timeout attempts followed by success."""
        # given
        call_count = 0

        async def slow_then_success_operation():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                await asyncio.sleep(0.2)  # First two calls timeout
            return "final_success"  # Third call succeeds

        decorator = create_retry_with_timeout_decorator(timeout_seconds=0.1, max_retries=3)
        decorated_func = decorator(slow_then_success_operation)

        # when
        result = await decorated_func()

        # then
        assert result == "final_success"
        assert call_count == 3  # Two timeouts, then success

    @pytest.mark.asyncio
    async def test_create_decorator_with_custom_configuration(self):
        """Test creating decorator with custom timeout and retry configuration."""

        # given
        async def test_operation():
            return "configured_result"

        decorator = create_retry_with_timeout_decorator(timeout_seconds=5, max_retries=5, min_wait=2, max_wait=10)
        decorated_func = decorator(test_operation)

        # when
        result = await decorated_func()

        # then
        assert result == "configured_result"


class TestTimeoutExceptionRetry:
    """Tests for timeout exception retry behavior."""

    def test_should_retry_asyncio_timeout_error(self):
        """Test that asyncio.TimeoutError should be retried."""
        # given
        exception = TimeoutError()

        # when
        result = should_retry_llm_exception(exception)

        # then
        assert result is True

    def test_should_retry_timeout_error(self):
        """Test that TimeoutError should be retried."""
        # given
        exception = TimeoutError("Operation timed out")

        # when
        result = should_retry_llm_exception(exception)

        # then
        assert result is True

    def test_timeout_error_combined_with_openai_error(self):
        """Test timeout error retry logic doesn't interfere with OpenAI error logic."""
        # given
        openai_exception = Mock(spec=APIConnectionError)
        timeout_exception = TimeoutError("Timeout")

        # when
        openai_result = should_retry_llm_exception(openai_exception)
        timeout_result = should_retry_llm_exception(timeout_exception)

        # then
        assert openai_result is True
        assert timeout_result is True


class TestTimeoutEnvironmentVariables:
    """Tests for timeout environment variable loading."""

    def test_default_timeout_constants(self):
        """Test default timeout constant values."""
        # given
        from llm_ci_runner.retry import DEFAULT_TIMEOUT

        # when / then
        assert DEFAULT_TIMEOUT == 120  # 2 minutes for all operations

    @patch.dict("os.environ", {"LLM_TIMEOUT": "180"})
    def test_timeout_from_environment(self):
        """Test timeout loading from environment variable."""
        # given / when - Import after environment is patched
        from importlib import reload

        from llm_ci_runner import retry

        reload(retry)

        # then
        assert retry.TIMEOUT == 180
