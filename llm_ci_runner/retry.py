"""
Retry utilities for LLM CI Runner.

Provides retry mechanisms for external API calls to handle transient failures.
Uses exponential backoff with jitter to prevent thundering herd problems and
selectively retries only transient errors while avoiding permanent failures.

Enhanced with integrated timeout protection to prevent indefinite hangs during
network operations, with configurable timeout values via environment variables.
"""

from __future__ import annotations

import asyncio
import functools
import logging
import os
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

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
    before_sleep_log,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_random_exponential,
)

LOGGER = logging.getLogger(__name__)

# Type variable for generic async functions
F = TypeVar("F", bound=Callable[..., Awaitable[Any]])

# Default retry configuration constants
DEFAULT_MAX_RETRIES = 3
DEFAULT_MIN_WAIT = 1  # seconds
DEFAULT_MAX_WAIT = 30  # seconds
DEFAULT_EXPONENTIAL_MULTIPLIER = 1

# Default timeout configuration (in seconds)
DEFAULT_TIMEOUT = 120  # 2 minutes for all operations


def get_timeout_from_env(env_var: str, default: int) -> int:
    """Get timeout value from environment variable with validation and fallback.

    Args:
        env_var: Environment variable name
        default: Default timeout value if env var is invalid/missing

    Returns:
        Validated timeout value in seconds
    """
    try:
        value = os.getenv(env_var)
        if value is not None:
            parsed = int(value)
            if parsed > 0:
                return parsed
            else:
                LOGGER.warning(f"Invalid {env_var} value (must be positive): {parsed}, using default: {default}s")
        return default
    except (ValueError, TypeError) as e:
        LOGGER.warning(f"Invalid {env_var} value: {value}, using default: {default}s - {e}")
        return default


# Load timeout configuration from environment variable
TIMEOUT = get_timeout_from_env("LLM_TIMEOUT", DEFAULT_TIMEOUT)


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
        return False  # pragma: no cover

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
        return False  # pragma: no cover

    return False


def should_retry_llm_exception(exception: BaseException) -> bool:
    """Determine if an LLM-related exception should be retried.

    Combines OpenAI, Azure, and schema validation retry conditions for unified
    LLM error handling. Includes timeout errors and JSON parsing failures as
    retriable since they are transient failures that can be resolved with a new
    LLM invocation.

    Args:
        exception: The exception to check

    Returns:
        True if the exception is retriable, False otherwise
    """
    # Retry timeout errors (transient failures)
    if isinstance(exception, asyncio.TimeoutError | TimeoutError):
        return True

    # Retry schema validation errors (LLM can produce better JSON on retry)
    from .exceptions import SchemaValidationError

    if isinstance(exception, SchemaValidationError):
        return True

    return should_retry_openai_exception(exception) or should_retry_azure_exception(exception)


def create_retry_with_timeout_decorator(
    timeout_seconds: int = TIMEOUT,
    max_retries: int = DEFAULT_MAX_RETRIES,
    min_wait: int = DEFAULT_MIN_WAIT,
    max_wait: int = DEFAULT_MAX_WAIT,
) -> Callable[[F], F]:
    """Create unified retry + timeout decorator for async functions.

    Integrates timeout protection with retry logic to provide comprehensive
    resilience for network operations. The timeout is applied to each retry
    attempt, and timeout errors are treated as retriable.

    Args:
        timeout_seconds: Timeout value in seconds for each attempt
        max_retries: Maximum number of retry attempts
        min_wait: Minimum wait time between retries (seconds)
        max_wait: Maximum wait time between retries (seconds)

    Returns:
        Decorator function that applies timeout + retry to async functions
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Apply timeout to each retry attempt
            async def timeout_wrapper() -> Any:
                try:
                    return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout_seconds)
                except TimeoutError as e:
                    operation_name = func.__name__.replace("_", " ").replace("async ", "").title()
                    raise TimeoutError(
                        f"{operation_name} timed out after {timeout_seconds}s. "
                        f"Consider increasing timeout via LLM_TIMEOUT environment variable."
                    ) from e

            # Apply retry to timeout wrapper
            retry_decorator = retry(
                retry=retry_if_exception(should_retry_llm_exception),
                stop=stop_after_attempt(max_retries),
                wait=wait_random_exponential(
                    multiplier=DEFAULT_EXPONENTIAL_MULTIPLIER,
                    min=min_wait,
                    max=max_wait,
                ),
                before_sleep=before_sleep_log(LOGGER, logging.WARNING),
                reraise=True,
            )

            return await retry_decorator(timeout_wrapper)()

        return wrapper  # type: ignore

    return decorator


# Create unified retry + timeout decorator for all network operations
retry_network_operation = create_retry_with_timeout_decorator()
