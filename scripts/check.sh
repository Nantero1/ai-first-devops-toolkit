#!/bin/bash

echo -e "\033[32mChecking for errors...\033[0m"

echo -e "\033[32mInstalling dependencies...\033[0m"
uv sync --group dev

echo -e "\033[32mChecking for formatting errors...\033[0m"
uv run ruff format .
uv run ruff check --fix llm_ci_runner/

echo -e "\033[32mChecking for type errors...\033[0m"
uv run mypy llm_ci_runner/

echo -e "\033[32mRunning unit tests...\033[0m"
uv run pytest tests/

echo -e ""
echo -e "\033[32mWill now run acceptance tests...\033[0m"
echo -e "\033[33mPress Ctrl+C to stop the tests...\033[0m"
read -n 1 -s -r -p "Press Enter to continue..."

echo -e "\033[32mRunning acceptance tests...\033[0m"
uv run pytest acceptance/ -s -v --smoke-test

echo -e "\033[32mAll checks passed!\033[0m"

