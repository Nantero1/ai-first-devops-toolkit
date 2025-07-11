"""
Custom exceptions for the LLM CI Runner package.

This module defines all custom exception classes used throughout the package
to provide clear error handling and meaningful error messages.
"""


class LLMRunnerError(Exception):
    """Base exception for LLM Runner errors."""

    pass


class InputValidationError(LLMRunnerError):
    """Raised when input validation fails."""

    pass


class AuthenticationError(LLMRunnerError):
    """Raised when Azure authentication fails."""

    pass


class LLMExecutionError(LLMRunnerError):
    """Raised when LLM execution fails."""

    pass


class SchemaValidationError(LLMRunnerError):
    """Raised when JSON schema validation or conversion fails."""

    pass
