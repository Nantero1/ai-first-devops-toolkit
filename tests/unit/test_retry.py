"""
Unit tests for retry utilities in llm_ci_runner.

Tests retry logic for OpenAI and Azure API exceptions, ensuring proper retry behavior
for transient errors while avoiding retries for permanent failures.
"""

from unittest.mock import Mock

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
    should_retry_azure_exception,
    should_retry_network_exception,
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
        result = should_retry_network_exception(exception)

        # then
        assert result is True

    def test_should_retry_azure_retriable_exception(self):
        """Test that Azure retriable exceptions are retried via network logic."""
        # given
        exception = ServiceRequestError("Service request failed")

        # when
        result = should_retry_network_exception(exception)

        # then
        assert result is True

    def test_should_not_retry_non_retriable_exception(self):
        """Test that non-retriable exceptions are not retried via network logic."""
        # given
        exception = ClientAuthenticationError("Authentication failed")

        # when
        result = should_retry_network_exception(exception)

        # then
        assert result is False

    def test_should_not_retry_unknown_exception(self):
        """Test that unknown exceptions are not retried via network logic."""
        # given
        exception = ValueError("Unknown error")

        # when
        result = should_retry_network_exception(exception)

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
            DEFAULT_MAX_RETRIES,
            DEFAULT_MIN_WAIT,
            DEFAULT_MAX_WAIT,
            DEFAULT_EXPONENTIAL_MULTIPLIER,
        )

        # when / then
        assert DEFAULT_MAX_RETRIES == 3
        assert DEFAULT_MIN_WAIT == 1
        assert DEFAULT_MAX_WAIT == 30
        assert DEFAULT_EXPONENTIAL_MULTIPLIER == 1
