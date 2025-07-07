"""Pytest fixtures for acceptance testing.

This module provides shared fixtures and utilities for LLM-as-judge acceptance tests.
Follows our testing best practices with Rich formatting and reusable components.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import pytest
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


@pytest.fixture(scope="session")
def environment_check():
    """Check that Azure OpenAI environment is properly configured."""
    required_vars = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_MODEL",
        "AZURE_OPENAI_API_KEY",
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        console.print(
            Panel(
                f"❌ Missing environment variables: {', '.join(missing_vars)}\n"
                "Please set these before running acceptance tests.",
                title="Environment Check Failed",
                style="red",
            )
        )
        pytest.skip(f"Missing environment variables: {missing_vars}")

    console.print(
        Panel(
            "✅ Environment properly configured",
            title="Environment Check",
            style="green",
        )
    )
    return True


@pytest.fixture
def temp_files():
    """Manage temporary files for test isolation."""
    files = []

    def _create_temp_file(content: str = "", suffix: str = ".json") -> str:
        """Create a temporary file with given content."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False) as f:
            if content:
                f.write(content)
            files.append(f.name)
            return f.name

    yield _create_temp_file

    # Cleanup
    for file_path in files:
        try:
            Path(file_path).unlink(missing_ok=True)
        except Exception:
            pass


@pytest.fixture
def llm_ci_runner():
    """Execute LLM runner with proper error handling and logging."""

    def _run_llm_ci_runner(
        input_file: str, output_file: str, schema_file: str = None, timeout: int = 60
    ) -> tuple[int, str, str]:
        """Run the LLM runner and return result code, stdout, stderr."""
        cmd = [
            "uv",
            "run",
            "llm_ci_runner.py",
            "--input-file",
            input_file,
            "--output-file",
            output_file,
            "--log-level",
            "ERROR",  # Minimize noise in tests
        ]

        if schema_file:
            cmd.extend(["--schema-file", schema_file])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return -1, "", str(e)

    return _run_llm_ci_runner


@pytest.fixture
def judgment_schema_path():
    """Path to the judgment schema for structured LLM-as-judge responses."""
    return "acceptance/judgment_schema.json"


@pytest.fixture
def llm_judge(llm_ci_runner, temp_files, judgment_schema_path):
    """LLM-as-judge evaluator using structured output."""

    async def _evaluate_response(query: str, response: str, criteria: str, input_context: str = "") -> dict[str, Any]:
        """Evaluate a response using LLM-as-judge with structured output."""

        # Create judgment prompt with structured output instructions
        judgment_input = {
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an expert AI judge tasked with evaluating AI responses. "
                        "Provide detailed, objective assessments based on the given criteria. "
                        "You must respond with a structured JSON object containing numeric scores, "
                        "boolean pass/fail decision, and detailed reasoning."
                    ),
                },
                {
                    "role": "user",
                    "content": f"""Please evaluate the following AI response:

ORIGINAL QUERY: {query}

INPUT CONTEXT: {input_context}

AI RESPONSE TO EVALUATE:
{response}

EVALUATION CRITERIA:
{criteria}

Provide your assessment as a JSON object with the following structure:
- relevance: integer score 1-10 (How well does the response address the query?)
- accuracy: integer score 1-10 (How factually correct is the response?)
- completeness: integer score 1-10 (How complete is the response?)
- clarity: integer score 1-10 (How clear and well-structured is the response?)
- overall: integer score 1-10 (Overall assessment of response quality)
- pass: boolean (Does this response meet acceptable quality standards?)
- strengths: array of strings (Main strengths of the response)
- weaknesses: array of strings (Main weaknesses or areas for improvement)  
- reasoning: string (Detailed reasoning for the pass/fail decision)

Use objective criteria and provide specific reasoning for your assessment.""",
                },
            ]
        }

        # Create temporary files for judgment
        judgment_input_file = temp_files(json.dumps(judgment_input, indent=2))
        judgment_output_file = temp_files()

        # Run LLM runner with structured output
        returncode, stdout, stderr = llm_ci_runner(judgment_input_file, judgment_output_file, judgment_schema_path)

        if returncode != 0:
            return {"error": f"Judgment failed: {stderr}", "pass": False}

        # Load structured judgment result
        try:
            with open(judgment_output_file) as f:
                judgment_result = json.load(f)

            structured_judgment = judgment_result.get("response", {})

            # Validate structure
            if not isinstance(structured_judgment, dict):
                return {
                    "error": "Judgment response is not a structured object",
                    "pass": False,
                }

            required_fields = [
                "relevance",
                "accuracy",
                "completeness",
                "clarity",
                "overall",
                "pass",
                "reasoning",
            ]
            missing_fields = [field for field in required_fields if field not in structured_judgment]

            if missing_fields:
                return {
                    "error": f"Missing required judgment fields: {missing_fields}",
                    "pass": False,
                }

            return structured_judgment

        except Exception as e:
            return {"error": f"Failed to parse structured judgment: {e}", "pass": False}

    return _evaluate_response


@pytest.fixture
def rich_test_output():
    """Rich formatting utilities for test output."""

    def _format_judgment_table(judgment: dict[str, Any]) -> Table:
        """Format judgment results as a Rich table."""
        table = Table(title="🧑‍⚖️ LLM Judge Results")

        table.add_column("Metric", style="cyan")
        table.add_column("Score", style="magenta")
        table.add_column("Status", style="green" if judgment.get("pass") else "red")

        metrics = ["relevance", "accuracy", "completeness", "clarity", "overall"]
        for metric in metrics:
            score = judgment.get(metric, 0)
            table.add_row(metric.title(), f"{score}/10", "✅" if score >= 7 else "❌")

        # Add overall pass/fail
        table.add_row("Overall Decision", "", "✅ PASS" if judgment.get("pass") else "❌ FAIL")

        return table

    def _format_strengths_weaknesses(judgment: dict[str, Any]) -> str:
        """Format strengths and weaknesses as formatted text."""
        output = []

        strengths = judgment.get("strengths", [])
        if strengths:
            output.append("💪 **Strengths:**")
            for strength in strengths:
                output.append(f"  • {strength}")

        weaknesses = judgment.get("weaknesses", [])
        if weaknesses:
            output.append("\n⚠️ **Weaknesses:**")
            for weakness in weaknesses:
                output.append(f"  • {weakness}")

        reasoning = judgment.get("reasoning", "")
        if reasoning:
            output.append(f"\n🧠 **Reasoning:**\n{reasoning}")

        return "\n".join(output)

    return {
        "format_judgment_table": _format_judgment_table,
        "format_strengths_weaknesses": _format_strengths_weaknesses,
    }


@pytest.fixture
def example_files():
    """Paths to example input files."""
    return {
        "simple": "examples/simple-example.json",
        "minimal": "examples/minimal-example.json",
        "pr_review": "examples/pr-review-example.json",
        "structured_schema": "examples/structured-output-example.json",
        "code_review_schema": "examples/code_review_schema.json",
    }


@pytest.fixture
def load_example_file():
    """Load and return content of example files."""

    def _load_file(file_path: str) -> dict[str, Any]:
        """Load JSON content from file."""
        with open(file_path) as f:
            return json.load(f)

    return _load_file


@pytest.fixture
def assert_execution_success():
    """Assert that LLM runner execution was successful."""

    def _assert_success(returncode: int, stdout: str, stderr: str, test_name: str):
        """Assert execution success with rich error display."""
        if returncode != 0:
            console.print(
                Panel(
                    f"❌ {test_name} execution failed\nReturn code: {returncode}\nStderr: {stderr}\nStdout: {stdout}",
                    title="Execution Error",
                    style="red",
                )
            )
            pytest.fail(f"{test_name} execution failed with code {returncode}: {stderr}")

    return _assert_success


@pytest.fixture
def assert_judgment_passed():
    """Assert that LLM judge evaluation passed."""

    def _assert_judgment(judgment: dict[str, Any], test_name: str, min_score: int = 7, rich_output=None):
        """Assert judgment passed with detailed Rich output."""
        if "error" in judgment:
            console.print(
                Panel(
                    f"❌ {test_name} judgment failed\n{judgment['error']}",
                    title="Judgment Error",
                    style="red",
                )
            )
            pytest.fail(f"{test_name} judgment failed: {judgment['error']}")

        overall_score = judgment.get("overall", 0)
        judge_pass = judgment.get("pass", False)

        # Display results with Rich
        if rich_output:
            table = rich_output["format_judgment_table"](judgment)
            console.print(table)

            details = rich_output["format_strengths_weaknesses"](judgment)
            if details:
                console.print(Panel(details, title="📊 Detailed Assessment"))

        # Assert conditions
        if not judge_pass or overall_score < min_score:
            console.print(
                Panel(
                    f"❌ {test_name} failed quality standards\n"
                    f"Overall Score: {overall_score}/10 (minimum: {min_score})\n"
                    f"Judge Decision: {'PASS' if judge_pass else 'FAIL'}\n"
                    f"Reasoning: {judgment.get('reasoning', 'No reasoning provided')}",
                    title="Quality Standards Not Met",
                    style="red",
                )
            )
            pytest.fail(
                f"{test_name} failed: Overall score {overall_score}/10 < {min_score} "
                f"or Judge decision: {'PASS' if judge_pass else 'FAIL'}"
            )

        console.print(
            Panel(
                f"✅ {test_name} passed quality standards\nOverall Score: {overall_score}/10\nJudge Decision: PASS",
                title="Quality Standards Met",
                style="green",
            )
        )

    return _assert_judgment
