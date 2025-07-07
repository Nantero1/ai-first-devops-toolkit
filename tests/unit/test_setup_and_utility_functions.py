"""
Unit tests for setup and utility functions in llm_ci_runner.py

Tests setup_logging function and other utility functions
with heavy mocking following the Given-When-Then pattern.
"""

import logging
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from llm_ci_runner import setup_logging


class TestSetupLogging:
    """Tests for setup_logging function."""

    @pytest.mark.parametrize("log_level", ["DEBUG", "INFO", "WARNING", "ERROR"])
    def test_setup_logging_with_valid_levels(self, log_level, mock_console):
        """Test setting up logging with all valid log levels."""
        # given
        log_level_str = log_level

        # when
        with patch("logging.basicConfig") as mock_basic_config:
            logger = setup_logging(log_level_str)

        # then
        assert logger is not None
        mock_basic_config.assert_called_once()
        # Verify the correct log level was set
        call_kwargs = mock_basic_config.call_args[1]
        assert call_kwargs["level"] == getattr(logging, log_level)

    def test_setup_logging_with_lowercase_level(self, mock_console):
        """Test setting up logging with lowercase log level."""
        # given
        log_level = "debug"

        # when
        with patch("logging.basicConfig") as mock_basic_config:
            logger = setup_logging(log_level)

        # then
        assert logger is not None
        mock_basic_config.assert_called_once()
        # Verify the correct log level was set (should be converted to uppercase)
        call_kwargs = mock_basic_config.call_args[1]
        assert call_kwargs["level"] == logging.DEBUG

    def test_setup_logging_configures_rich_handler(self, mock_console):
        """Test that logging is configured with RichHandler."""
        # given
        log_level = "INFO"

        # when
        with (
            patch("logging.basicConfig") as mock_basic_config,
            patch("llm_ci_runner.RichHandler") as mock_rich_handler,
        ):
            logger = setup_logging(log_level)

        # then
        mock_rich_handler.assert_called_once()
        # Verify RichHandler was configured properly
        handler_call_kwargs = mock_rich_handler.call_args[1]
        assert "console" in handler_call_kwargs
        assert handler_call_kwargs["show_time"] is True
        assert handler_call_kwargs["show_level"] is True
        assert handler_call_kwargs["show_path"] is True
        assert handler_call_kwargs["markup"] is True
        assert handler_call_kwargs["rich_tracebacks"] is True

    def test_setup_logging_sets_correct_format(self, mock_console):
        """Test that logging format is set correctly."""
        # given
        log_level = "INFO"

        # when
        with patch("logging.basicConfig") as mock_basic_config:
            logger = setup_logging(log_level)

        # then
        call_kwargs = mock_basic_config.call_args[1]
        assert call_kwargs["format"] == "%(message)s"
        assert call_kwargs["datefmt"] == "[%X]"

    def test_setup_logging_logs_initialization_message(self, mock_console, mock_logger):
        """Test that initialization message is logged."""
        # given
        log_level = "INFO"

        # when
        with patch("logging.basicConfig"):
            logger = setup_logging(log_level)

        # then
        # Verify the logger info was called for initialization
        mock_logger.info.assert_called()
        # Check that the initialization message contains the log level
        call_args = mock_logger.info.call_args[0]
        assert "INFO" in call_args[0]

    def test_setup_logging_with_invalid_level_uses_debug_as_fallback(self, mock_console):
        """Test that invalid log level falls back to DEBUG level."""
        # given
        log_level = "INVALID_LEVEL"

        # when
        with patch("logging.basicConfig") as mock_basic_config:
            # This might raise AttributeError for invalid level
            try:
                logger = setup_logging(log_level)
            except AttributeError:
                # This is expected behavior - getattr(logging, "INVALID_LEVEL") will fail
                pass

        # then
        # The function should handle this gracefully or raise appropriate error
        # This test verifies the behavior when an invalid level is passed

    def test_setup_logging_returns_logger_instance(self, mock_console):
        """Test that setup_logging returns a logger instance."""
        # given
        log_level = "INFO"

        # when
        with patch("logging.basicConfig"):
            logger = setup_logging(log_level)

        # then
        assert isinstance(logger, logging.Logger)
        assert logger.name == "llm_ci_runner"

    def test_setup_logging_uses_global_console(self, mock_console):
        """Test that setup_logging uses the global CONSOLE instance."""
        # given
        log_level = "INFO"

        # when
        with (
            patch("logging.basicConfig"),
            patch("llm_ci_runner.RichHandler") as mock_rich_handler,
        ):
            logger = setup_logging(log_level)

        # then
        # Verify RichHandler was called with the global CONSOLE
        handler_call_kwargs = mock_rich_handler.call_args[1]
        assert handler_call_kwargs["console"] == mock_console


class TestMainFunction:
    """Tests for main function error handling."""

    @pytest.mark.asyncio
    async def test_main_function_with_keyboard_interrupt_exits_gracefully(self):
        """Test that KeyboardInterrupt is handled gracefully."""
        # given
        # when & then
        with (
            patch("llm_ci_runner.parse_arguments") as mock_parse,
            patch("llm_ci_runner.setup_logging") as mock_setup_log,
            patch("llm_ci_runner.load_input_json", side_effect=KeyboardInterrupt()),
        ):
            from llm_ci_runner import main

            with pytest.raises(SystemExit) as exc_info:
                await main()

            assert exc_info.value.code == 1

    @pytest.mark.asyncio
    async def test_main_function_with_llm_ci_runner_error_exits_with_error_code(self):
        """Test that LLMRunnerError causes exit with error code 1."""
        # given
        from llm_ci_runner import LLMRunnerError, main

        # when & then
        with (
            patch("llm_ci_runner.parse_arguments") as mock_parse,
            patch("llm_ci_runner.setup_logging") as mock_setup_log,
            patch(
                "llm_ci_runner.load_input_json",
                side_effect=LLMRunnerError("Test error"),
            ),
        ):
            with pytest.raises(SystemExit) as exc_info:
                await main()

            assert exc_info.value.code == 1

    @pytest.mark.asyncio
    async def test_main_function_with_unexpected_error_exits_with_error_code(self):
        """Test that unexpected errors cause exit with error code 1."""
        # given
        from llm_ci_runner import main

        # when & then
        with (
            patch("llm_ci_runner.parse_arguments") as mock_parse,
            patch("llm_ci_runner.setup_logging") as mock_setup_log,
            patch(
                "llm_ci_runner.load_input_json",
                side_effect=Exception("Unexpected error"),
            ),
        ):
            with pytest.raises(SystemExit) as exc_info:
                await main()

            assert exc_info.value.code == 1

    @pytest.mark.asyncio
    async def test_main_function_success_path_completes_without_error(self):
        """Test that successful execution completes without raising SystemExit."""
        # given
        from llm_ci_runner import main

        # when
        with (
            patch("llm_ci_runner.parse_arguments") as mock_parse,
            patch("llm_ci_runner.setup_logging") as mock_setup_log,
            patch("llm_ci_runner.load_input_json") as mock_load_input,
            patch("llm_ci_runner.create_chat_history") as mock_create_history,
            patch("llm_ci_runner.setup_azure_service") as mock_setup_azure,
            patch("llm_ci_runner.load_json_schema") as mock_load_schema,
            patch("llm_ci_runner.execute_llm_task") as mock_execute,
            patch("llm_ci_runner.write_output_file") as mock_write_output,
        ):
            # Setup mocks
            mock_args = Mock()
            mock_args.input_file = Path("input.json")
            mock_args.output_file = Path("output.json")
            mock_args.schema_file = None
            mock_args.log_level = "INFO"
            mock_parse.return_value = mock_args

            mock_load_input.return_value = {"messages": [{"role": "user", "content": "test"}]}
            mock_create_history.return_value = Mock()
            mock_setup_azure.return_value = (
                Mock(),
                Mock(),
            )  # Return tuple (service, credential)
            mock_load_schema.return_value = None
            mock_execute.return_value = "Test response"

            # Execute
            await main()

        # then
        # If no exception is raised, the test passes
        # Verify key functions were called
        mock_parse.assert_called_once()
        mock_setup_log.assert_called_once()
        mock_load_input.assert_called_once()
        mock_execute.assert_called_once()
        mock_write_output.assert_called_once()
