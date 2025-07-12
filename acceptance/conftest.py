"""Pytest fixtures for acceptance testing.

This module provides shared fixtures and utilities for LLM-as-judge acceptance tests.
Follows our testing best practices with Rich formatting and reusable components.

⚠️  Uses real Azure OpenAI API calls
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


def pytest_addoption(parser):
    """Add custom command line options for pytest."""
    parser.addoption(
        "--smoke-test",
        action="store_true",
        default=False,
        help="Run smoke tests only (skip expensive LLM-as-judge tests)",
    )


@pytest.fixture(scope="session")
def smoke_test_mode(request):
    """Fixture to determine if running in smoke test mode."""
    return request.config.getoption("--smoke-test")


@pytest.fixture(scope="session")
def skip_if_not_smoke_test(smoke_test_mode):
    """Skip test if not in smoke test mode - for LLM-as-judge tests."""
    if not smoke_test_mode:
        return False  # Don't skip
    pytest.skip("Skipping expensive LLM-as-judge test in smoke test mode")


@pytest.fixture(scope="session")
def skip_if_smoke_test(smoke_test_mode):
    """Skip test if in smoke test mode - for expensive LLM-as-judge tests."""
    if smoke_test_mode:
        pytest.skip("Skipping expensive LLM-as-judge test in smoke test mode")


@pytest.fixture(scope="session")
def environment_check(smoke_test_mode):
    """Check that Azure OpenAI environment is properly configured."""
    console.print("")  # New line to make sure boxes are not next to each other
    if smoke_test_mode:
        console.print(
            Panel(
                "🚀 Running in SMOKE TEST mode - no LLM calls will be made",
                title="Smoke Test Mode",
                style="blue",
            )
        )
        return True  # Skip environment check in smoke test mode

    required_vars = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_MODEL",
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        console.print(
            Panel(
                f"❌ Missing environment variables: {', '.join(missing_vars)}\n"
                "Please set these before running acceptance tests.\n\n"
                "💡 TIP: Use --smoke-test flag to do less LLM calls (faster, skip LLM-as-judge tests)",
                title="Environment Check Failed",
                style="red",
            )
        )
        pytest.skip(f"Missing environment variables: {missing_vars}")

    console.print(
        Panel(
            "✅ Environment properly configured for LLM calls",
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
        """Run the LLM runner and return result code, stdout, stderr.

        Supports both input-file mode and template-file mode:
        - If input_file ends with .json: uses --input-file mode
        - If input_file ends with .hbs/.jinja/.j2: uses --template-file mode (with optional template-vars)
        """
        from pathlib import Path

        input_path = Path(input_file)

        # Determine mode based on file extension
        if input_path.suffix.lower() in [".hbs", ".jinja", ".j2"]:
            # Template mode: --template-file template.hbs/jinja/j2 [--template-vars vars.yaml] --schema-file schema.yaml
            cmd = [
                "llm-ci-runner",
                "--template-file",
                input_file,
                "--output-file",
                output_file,
                "--log-level",
                "ERROR",  # Minimize noise in tests
            ]

            # Check for template-vars file in same directory
            template_vars_yaml = input_path.parent / "template-vars.yaml"
            template_vars_json = input_path.parent / "template-vars.json"

            if template_vars_yaml.exists():
                cmd.extend(["--template-vars", str(template_vars_yaml)])
            elif template_vars_json.exists():
                cmd.extend(["--template-vars", str(template_vars_json)])

            # Schema file is required for template mode
            if schema_file:
                cmd.extend(["--schema-file", schema_file])
        else:
            # Input file mode: --input-file input.json [--schema-file schema.json]
            cmd = [
                "llm-ci-runner",
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
def examples_dir():
    """Get path to examples directory."""
    return Path("examples")


@pytest.fixture
def discovered_examples(examples_dir):
    """Auto-discover examples based on folder structure convention."""

    def _discover_examples() -> list[tuple[Path, Path | None, str]]:
        """
        Recursively discover all example folders under examples/ containing input.json.
        If schema.json exists in the same folder, it's used for validation.
        Returns: List of (input_file, schema_file, example_name) tuples
        """
        examples = []
        for input_file in examples_dir.rglob("input.json"):
            folder = input_file.parent
            schema_file = folder / "schema.json"
            schema = schema_file if schema_file.exists() else None
            # Example name: relative path from examples_dir, with / replaced by _
            example_name = str(folder.relative_to(examples_dir)).replace(os.sep, "_")
            examples.append((input_file, schema, example_name))
        return examples

    return _discover_examples()


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


@pytest.fixture
def generic_llm_judge(llm_ci_runner, temp_files, judgment_schema_path):
    """Generic LLM-as-judge evaluator that works with any example type.

    This fixture provides a generic evaluation approach that can assess any example
    based on its input, schema, and output without requiring specific criteria.
    """

    async def _evaluate_generic(
        input_file: Path,
        schema_file: Path | None,
        output_result: dict,
        example_name: str,
    ) -> dict[str, Any]:
        """Evaluate any example using generic criteria based on input, schema, and output.

        Args:
            input_file: Path to input file (JSON or template)
            schema_file: Optional path to schema file
            output_result: The actual output from the LLM
            example_name: Name of the example for context

        Returns:
            Structured judgment result with scores and reasoning
        """

        # Determine example type and context
        input_path = Path(input_file)
        is_template = input_path.suffix.lower() in [".hbs", ".jinja", ".j2"]

        # Load input context
        if is_template:
            # For templates, read the template content
            with open(input_file) as f:
                input_content = f.read()
            input_context = f"Template-based example: {example_name}. Template content: {input_content[:300]}..."
            evaluation_query = f"Template-based generation using: {input_content[:200]}..."
        else:
            # For JSON examples, load the messages
            try:
                with open(input_file) as f:
                    input_data = json.load(f)
                last_message = input_data.get("messages", [{}])[-1]
                evaluation_query = last_message.get("content", "Unknown query")
                input_context = f"JSON-based example: {example_name}. Query: {evaluation_query[:200]}..."
            except Exception as e:
                evaluation_query = f"JSON input from {example_name}"
                input_context = f"JSON-based example: {example_name}. Error loading input: {e}"

        # Load schema context if available
        schema_context = ""
        if schema_file:
            try:
                with open(schema_file) as f:
                    schema_data = json.load(f)
                schema_context = f"Expected schema: {json.dumps(schema_data, indent=2)}"
            except Exception:
                try:
                    import yaml

                    with open(schema_file) as f:
                        schema_data = yaml.safe_load(f)
                    schema_context = f"Expected schema: {yaml.dump(schema_data, default_flow_style=False)}"
                except Exception as e:
                    schema_context = f"Schema file exists but could not be parsed: {e}"

        # Format output for evaluation
        if isinstance(output_result, dict):
            response_text = json.dumps(output_result, indent=2)
        else:
            response_text = str(output_result)

        # Generate generic evaluation criteria based on available information
        criteria = _generate_generic_criteria(
            example_name=example_name,
            is_template=is_template,
            has_schema=bool(schema_file),
            schema_context=schema_context,
        )

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

ORIGINAL QUERY: {evaluation_query}

INPUT CONTEXT: {input_context}

{schema_context}

AI RESPONSE TO EVALUATE:
{response_text}

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

    def _generate_generic_criteria(
        example_name: str,
        is_template: bool,
        has_schema: bool,
        schema_context: str,
    ) -> str:
        """Generate generic evaluation criteria based on example characteristics."""

        criteria_parts = []

        # Base criteria for all examples
        criteria_parts.append("""
        - Should provide clear, accurate, and well-structured responses
        - Should demonstrate understanding of the input requirements
        - Should be relevant to the given query or template purpose
        - Should be complete and comprehensive in addressing the request
        """)

        # Template-specific criteria
        if is_template:
            criteria_parts.append("""
        - Should properly utilize template variables and features
        - Should generate content that fulfills the template's intended purpose
        - Should maintain appropriate formatting and structure
        - Should demonstrate understanding of template syntax and capabilities
            """)

        # Schema-specific criteria
        if has_schema:
            criteria_parts.append("""
        - Should adhere to the expected output schema structure
        - Should include all required fields specified in the schema
        - Should use appropriate data types as defined in the schema
        - Should follow any constraints or validation rules specified
            """)

        # Example type-specific hints (based on name patterns)
        name_lower = example_name.lower()

        if "code-review" in name_lower or "review" in name_lower:
            criteria_parts.append("""
        - Should provide thorough technical analysis and constructive feedback
        - Should identify potential issues, bugs, or improvements
        - Should assess security implications where relevant
        - Should be professional and helpful in tone
            """)

        elif "security" in name_lower or "vulnerability" in name_lower:
            criteria_parts.append("""
        - Should identify security vulnerabilities accurately
        - Should assess risk levels appropriately
        - Should provide actionable remediation steps
        - Should demonstrate understanding of security principles
            """)

        elif "sentiment" in name_lower:
            criteria_parts.append("""
        - Should analyze sentiment accurately based on the input text
        - Should provide appropriate confidence scores
        - Should identify relevant key points from the text
        - Should demonstrate understanding of sentiment analysis concepts
            """)

        elif "changelog" in name_lower:
            criteria_parts.append("""
        - Should create well-structured changelog entries
        - Should categorize changes appropriately
        - Should follow changelog conventions
        - Should prioritize important changes
            """)

        elif "pr-description" in name_lower or "pull-request" in name_lower:
            criteria_parts.append("""
        - Should provide clear, comprehensive PR description
        - Should summarize changes effectively
        - Should identify key impacts and considerations
        - Should follow good PR description practices
            """)

        elif "autonomous" in name_lower or "development-plan" in name_lower:
            criteria_parts.append("""
        - Should provide comprehensive development planning
        - Should demonstrate understanding of software architecture
        - Should include realistic timelines and milestones
        - Should consider quality gates and risk assessment
            """)

        # Generic quality standards
        criteria_parts.append("""
        - Should be factually accurate and reliable
        - Should be well-organized and easy to understand
        - Should provide value and actionable insights
        - Should demonstrate appropriate depth and breadth of knowledge
        """)

        return "\n".join(criteria_parts)

    return _evaluate_generic
