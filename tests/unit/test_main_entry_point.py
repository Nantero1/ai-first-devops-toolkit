"""
Unit tests for __main__.py entry point.

Tests the module entry point functionality to ensure proper CLI invocation
when running the package as a module with python -m llm_ci_runner.
"""

import subprocess
import sys
from unittest.mock import patch

import pytest


class TestMainEntryPoint:
    """Tests for __main__.py module entry point."""

    @patch("llm_ci_runner.core.cli_main")
    def test_main_entry_point_execution(self, mock_cli_main):
        """Test that __main__.py executes cli_main when invoked as module."""
        # given - We'll test the actual execution path by running the module

        # when - Run the module as a subprocess to trigger the if __name__ == "__main__" block
        # This covers line 7 in __main__.py
        result = subprocess.run(
            [sys.executable, "-m", "llm_ci_runner", "--help"], capture_output=True, text=True, timeout=10
        )

        # then - Should execute without import errors and show help
        # The fact that it runs without ImportError means line 7 is covered
        assert result.returncode in [0, 2]  # 0 for success, 2 for argparse help exit

    def test_main_module_imports_correctly(self):
        """Test that __main__.py module can be imported without issues."""
        # given/when - import the module
        import llm_ci_runner.__main__

        # then - should import successfully and have expected attributes
        assert hasattr(llm_ci_runner.__main__, "cli_main")
        assert llm_ci_runner.__main__.__doc__ is not None
        assert "Entry point for running llm_ci_runner as a module" in llm_ci_runner.__main__.__doc__
