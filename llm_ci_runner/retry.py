"""
Retry utilities for LLM CI Runner.

Provides retry mechanisms for external API calls to handle transient failures.
Uses exponential backoff with jitter to prevent thundering herd problems and
selectively retries only transient errors while avoiding permanent failures.
"""

from __future__ import annotations

import logging

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
from tenacity import (
    after_log,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_random_exponential,
)

LOGGER = logging.getLogger(__name__)

# Default retry configuration constants
DEFAULT_MAX_RETRIES = 3
DEFAULT_MIN_WAIT = 1  # seconds
DEFAULT_MAX_WAIT = 30  # seconds
DEFAULT_EXPONENTIAL_MULTIPLIER = 1


def should_retry_openai_exception(exception: BaseException) -> bool:
    """Determine if an OpenAI exception should be retried.

    Args:
        exception: The exception to check

    Returns:
        True if the exception is retriable, False otherwise
    """
    # Retry connection errors, timeouts, and rate limits
    if isinstance(exception, APIConnectionError | APITimeoutError | RateLimitError):
        return True

    # Retry 500-level server errors from API
    if isinstance(exception, APIError) and hasattr(exception, "status_code"):
        status_code = getattr(exception, "status_code", None)
        if status_code is not None and isinstance(status_code, int):
            return bool(500 <= status_code < 600)
        return False

    return False


def should_retry_azure_exception(exception: BaseException) -> bool:
    """Determine if an Azure exception should be retried.

    Args:
        exception: The exception to check

    Returns:
        True if the exception is retriable, False otherwise
    """
    # Don't retry authentication/credential errors
    if isinstance(exception, ClientAuthenticationError):
        return False

    # Retry general service request/response errors
    if isinstance(exception, ServiceRequestError | ServiceResponseError):
        return True

    # Retry specific HTTP response status codes (transient errors)
    if isinstance(exception, HttpResponseError):
        if hasattr(exception, "status_code"):
            # 408: Request Timeout, 429: Too Many Requests, 5xx: Server Errors
            status_code = getattr(exception, "status_code", None)
            if status_code is not None and isinstance(status_code, int):
                return bool(status_code in (408, 429, 500, 502, 503, 504))
            return False
        return False

    return False


def should_retry_network_exception(exception: BaseException) -> bool:
    """Determine if a general network exception should be retried.

    Combines both OpenAI and Azure retry conditions for unified network error handling.

    Args:
        exception: The exception to check

    Returns:
        True if the exception is retriable, False otherwise
    """
    return should_retry_openai_exception(exception) or should_retry_azure_exception(exception)


# Create retry decorator for network operations

retry_network_operation = retry(
    retry=retry_if_exception(should_retry_network_exception),
    stop=stop_after_attempt(DEFAULT_MAX_RETRIES),
    wait=wait_random_exponential(
        multiplier=DEFAULT_EXPONENTIAL_MULTIPLIER,
        min=DEFAULT_MIN_WAIT,
        max=DEFAULT_MAX_WAIT,
    ),
    after=after_log(LOGGER, logging.WARNING),
    reraise=True,
)
