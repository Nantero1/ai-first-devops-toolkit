"""
Entry point for running llm_ci_runner as a module.

Allows: python -m llm_ci_runner
"""

from .core import cli_main

if __name__ == "__main__":
    cli_main()
