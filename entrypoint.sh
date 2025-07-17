#!/bin/bash
set -e

# Handle different execution scenarios
if [ $# -eq 0 ]; then
    # No arguments provided, run default command
    exec uv run python -m llm_ci_runner --help
elif [ "$1" = "bash" ] || [ "$1" = "sh" ]; then
    # Interactive shell requested
    exec "$@"
elif [ "$1" = "uv" ]; then
    # UV command, execute directly
    exec "$@"
else
    # Other commands, try to run with uv first, fallback to direct execution
    if command -v "$1" >/dev/null 2>&1; then
        exec "$@"
    else
        exec uv run "$@"
    fi
fi