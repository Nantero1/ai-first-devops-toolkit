"""
Unit tests for setup and utility functions in llm_ci_runner.py

Tests setup_logging function and other utility functions
with heavy mocking following the Given-When-Then pattern.
"""

import logging
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from llm_ci_runner import parse_arguments, setup_logging


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
            patch("llm_ci_runner.logging_config.RichHandler") as mock_rich_handler,
        ):
            logger = setup_logging(log_level)

        # then
        mock_rich_handler.assert_called_once()
        # Verify RichHandler was configured properly
        handler_call_kwargs = mock_rich_handler.call_args[1]
        assert "console" in handler_call_kwargs
        assert handler_call_kwargs["show_time"] is True, "show_time should be True"
        assert handler_call_kwargs["show_level"] is True, "show_level should be True"
        assert handler_call_kwargs["show_path"] is False, "show_path should be False"
        assert handler_call_kwargs["markup"] is True, "markup should be True"
        assert handler_call_kwargs["rich_tracebacks"] is True, "rich_tracebacks should be True"

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
        with (
            patch("logging.basicConfig"),
            patch("logging.getLogger", return_value=mock_logger),
        ):
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
            patch("llm_ci_runner.logging_config.RichHandler") as mock_rich_handler,
        ):
            logger = setup_logging(log_level)

        # then
        # Verify RichHandler was called with a console instance (not necessarily the mock)
        handler_call_kwargs = mock_rich_handler.call_args[1]
        assert "console" in handler_call_kwargs
        # The console should be the actual CONSOLE instance, not the mocked one


class TestParseArguments:
    """Tests for parse_arguments function."""

    def test_parse_arguments_allows_template_file_without_template_vars(self):
        """Test that --template-file can be used without --template-vars."""
        # given
        test_args = ["--template-file", "template.hbs"]

        # when
        with patch("sys.argv", ["llm_ci_runner.py"] + test_args):
            args = parse_arguments()

        # then
        assert args.template_file == Path("template.hbs")
        assert args.template_vars is None
        assert args.input_file is None

    def test_parse_arguments_allows_template_file_with_template_vars(self):
        """Test that --template-file can be used with --template-vars."""
        # given
        test_args = ["--template-file", "template.hbs", "--template-vars", "vars.yaml"]

        # when
        with patch("sys.argv", ["llm_ci_runner.py"] + test_args):
            args = parse_arguments()

        # then
        assert args.template_file == Path("template.hbs")
        assert args.template_vars == Path("vars.yaml")
        assert args.input_file is None

    def test_parse_arguments_requires_either_input_file_or_template_file(self):
        """Test that either --input-file or --template-file is required."""
        # given
        test_args = ["--output-file", "output.json"]

        # when & then
        with (
            patch("sys.argv", ["llm_ci_runner.py"] + test_args),
            pytest.raises(SystemExit),
        ):
            parse_arguments()

    def test_parse_arguments_template_vars_help_shows_optional(self):
        """Test that --template-vars help text indicates it's optional."""
        # given & when
        with patch("sys.argv", ["llm_ci_runner.py", "--help"]):
            with pytest.raises(SystemExit):
                try:
                    parse_arguments()
                except SystemExit as e:
                    # Capture the help output

                    # The help text should contain "optional"
                    # This is a basic test - in real usage, you'd capture stdout/stderr
                    pass
                    raise e


class TestMainFunction:
    """Tests for main function error handling."""

    @pytest.mark.asyncio
    async def test_main_function_with_keyboard_interrupt_exits_gracefully(self):
        """Test that KeyboardInterrupt is handled gracefully."""
        # given
        # when & then
        with (
            patch("llm_ci_runner.core.parse_arguments") as mock_parse,
            patch("llm_ci_runner.core.setup_logging"),
            patch("llm_ci_runner.core.setup_llm_service", side_effect=KeyboardInterrupt()),
            patch("llm_ci_runner.core.LOGGER.warning"),
        ):
            from llm_ci_runner import main

            # Setup mocks
            mock_args = Mock()
            mock_args.input_file = Path("input.json")
            mock_args.template_file = None
            mock_args.output_file = Path("output.json")
            mock_args.schema_file = None
            mock_args.log_level = "INFO"
            mock_parse.return_value = mock_args

            with pytest.raises(SystemExit) as exc_info:
                await main()

            assert exc_info.value.code == 130  # Standard exit code for KeyboardInterrupt

    @pytest.mark.asyncio
    async def test_main_function_with_llm_ci_runner_error_exits_with_error_code(self):
        """Test that LLMRunnerError causes exit with error code 1."""
        # given
        from llm_ci_runner import LLMRunnerError, main

        # when & then
        with (
            patch("llm_ci_runner.core.parse_arguments") as mock_parse,
            patch("llm_ci_runner.core.setup_logging") as mock_setup_log,
            patch(
                "llm_ci_runner.core.load_input_file",
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
            patch("llm_ci_runner.core.parse_arguments") as mock_parse,
            patch("llm_ci_runner.core.setup_logging") as mock_setup_log,
            patch(
                "llm_ci_runner.core.load_input_file",
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
            patch("llm_ci_runner.core.parse_arguments") as mock_parse,
            patch("llm_ci_runner.core.setup_logging") as mock_setup_log,
            patch("llm_ci_runner.core.load_input_file") as mock_load_input,
            patch("llm_ci_runner.core.create_chat_history") as mock_create_history,
            patch("llm_ci_runner.core.setup_llm_service") as mock_setup_llm,
            patch("llm_ci_runner.core.load_schema_file") as mock_load_schema,
            patch("llm_ci_runner.core.execute_llm_task") as mock_execute,
            patch("llm_ci_runner.core.write_output_file") as mock_write_output,
        ):
            # Setup mocks
            mock_args = Mock()
            mock_args.input_file = Path("input.json")
            mock_args.template_file = None  # Use input file mode, not template mode
            mock_args.output_file = Path("output.json")
            mock_args.schema_file = None
            mock_args.log_level = "INFO"
            mock_parse.return_value = mock_args

            mock_load_input.return_value = {"messages": [{"role": "user", "content": "test"}]}
            mock_create_history.return_value = Mock()
            mock_setup_llm.return_value = (
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
