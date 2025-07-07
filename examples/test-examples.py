#!/usr/bin/env python3
"""
Automatic example discovery and validation test framework.

Beware this acts as a smoke test and does not mock anyting, real LLM calls are made.

This framework automatically discovers examples based on the convention:
- examples/**/input.json
- examples/**/schema.json

For each example found, it runs the example and validates output.
If a schema.json exists, it validates schema compliance.
"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pytest
import os


class ExampleTestResult:
    """Test result container for example validation."""

    def __init__(
        self,
        name: str,
        success: bool,
        output: Optional[Dict] = None,
        error: Optional[str] = None,
    ):
        self.name = name
        self.success = success
        self.output = output
        self.error = error


@pytest.fixture
def temp_output_dir():
    """Create temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def llm_ci_runner_path():
    """Get path to llm_ci_runner.py."""
    return Path("llm_ci_runner.py")


@pytest.fixture
def examples_dir():
    """Get path to examples directory."""
    return Path("examples")


class ExampleTestFramework:
    """Core framework for running and validating examples."""

    @staticmethod
    def run_example(llm_ci_runner_path: Path, input_file: Path, output_file: Path) -> ExampleTestResult:
        """Run example without schema enforcement."""
        try:
            cmd = [
                "uv",
                "run",
                str(llm_ci_runner_path),
                "--input-file",
                str(input_file),
                "--output-file",
                str(output_file),
                "--log-level",
                "ERROR",  # Reduce noise in tests
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                with open(output_file, "r") as f:
                    output = json.load(f)
                return ExampleTestResult(input_file.name, True, output)
            else:
                return ExampleTestResult(input_file.name, False, error=result.stderr)

        except subprocess.TimeoutExpired:
            return ExampleTestResult(input_file.name, False, error="Timeout")
        except Exception as e:
            return ExampleTestResult(input_file.name, False, error=str(e))

    @staticmethod
    def run_example_with_schema(
        llm_ci_runner_path: Path, input_file: Path, output_file: Path, schema_file: Path
    ) -> ExampleTestResult:
        """Run example with schema enforcement."""
        try:
            cmd = [
                "uv",
                "run",
                str(llm_ci_runner_path),
                "--input-file",
                str(input_file),
                "--output-file",
                str(output_file),
                "--schema-file",
                str(schema_file),
                "--log-level",
                "ERROR",  # Reduce noise in tests
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                with open(output_file, "r") as f:
                    output = json.load(f)
                return ExampleTestResult(input_file.name, True, output)
            else:
                return ExampleTestResult(input_file.name, False, error=result.stderr)

        except subprocess.TimeoutExpired:
            return ExampleTestResult(input_file.name, False, error="Timeout")
        except Exception as e:
            return ExampleTestResult(input_file.name, False, error=str(e))


def discover_examples(examples_dir: Path) -> List[Tuple[Path, Optional[Path], str]]:
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


def validate_basic_output(output: Dict) -> bool:
    """Basic validation that output has expected structure."""
    if not isinstance(output, dict):
        return False

    if "response" not in output:
        return False

    return True


def validate_schema_compliance(output: Dict, schema_file: Path) -> bool:
    """Validate output against schema if schema exists."""
    if not schema_file.exists():
        return True  # No schema to validate against

    try:
        with open(schema_file, "r") as f:
            schema = json.load(f)

        # Basic schema validation - check required fields
        response = output.get("response", {})
        required_fields = schema.get("required", [])

        for field in required_fields:
            if field not in response:
                return False

        # Check enum constraints
        for field_name, field_schema in schema.get("properties", {}).items():
            if field_name in response:
                value = response[field_name]

                # Check enum constraints
                if "enum" in field_schema:
                    if value not in field_schema["enum"]:
                        return False

                # Check string length constraints
                if isinstance(value, str) and "maxLength" in field_schema:
                    if len(value) > field_schema["maxLength"]:
                        return False

                # Check numeric range constraints
                if isinstance(value, (int, float)):
                    if "minimum" in field_schema and value < field_schema["minimum"]:
                        return False
                    if "maximum" in field_schema and value > field_schema["maximum"]:
                        return False

                # Check array constraints
                if isinstance(value, list):
                    if "minItems" in field_schema and len(value) < field_schema["minItems"]:
                        return False
                    if "maxItems" in field_schema and len(value) > field_schema["maxItems"]:
                        return False

        return True

    except Exception:
        return False  # If schema validation fails, consider it invalid


class TestExamples:
    """Automatically discovered example tests."""

    # This class is used as a namespace for dynamically generated test functions
    # No methods needed since pytest doesn't instantiate test classes
    pass


# Generate test functions dynamically based on discovered examples
def generate_example_tests():
    """Generate test functions for discovered examples."""

    def create_test_function(input_file: Path, schema_file: Optional[Path], example_name: str):
        """Create a test function for a specific example."""

        def test_example(temp_output_dir, llm_ci_runner_path, examples_dir):
            """Test a specific example."""
            # given
            output_file = temp_output_dir / f"{input_file.stem}-output.json"

            # when
            if schema_file and schema_file.exists():
                result = ExampleTestFramework.run_example_with_schema(
                    llm_ci_runner_path, input_file, output_file, schema_file
                )
            else:
                result = ExampleTestFramework.run_example(llm_ci_runner_path, input_file, output_file)

            # then
            assert result.success, f"{example_name} failed: {result.error}"
            assert result.output is not None, f"{example_name}: No output generated"
            assert validate_basic_output(result.output), f"{example_name}: Invalid output structure"

            if schema_file and schema_file.exists():
                assert validate_schema_compliance(result.output, schema_file), (
                    f"{example_name}: Schema validation failed"
                )

        # Set the test function name and docstring
        test_example.__name__ = f"test_{example_name.lower().replace('-', '_').replace(' ', '_')}"
        test_example.__doc__ = f"Test {example_name} example"

        return test_example

    # Discover examples and create test functions
    examples_dir = Path("examples")
    discovered_examples = discover_examples(examples_dir)

    # Add test functions to the global module namespace
    for input_file, schema_file, example_name in discovered_examples:
        test_func = create_test_function(input_file, schema_file, example_name)
        globals()[test_func.__name__] = test_func


# Generate the test functions when the module is imported
generate_example_tests()


# Add a simple test to verify discovery works
def test_example_discovery(examples_dir):
    """Test that example discovery finds examples."""
    discovered = discover_examples(examples_dir)
    assert len(discovered) > 0, "No examples discovered"

    # Check that we have examples from different categories
    example_names = [name for _, _, name in discovered]
    # Just verify we have examples, no specific category requirements
    assert len(example_names) >= 1, "Should have at least one example"


def test_example_files_exist(examples_dir):
    """Test that discovered example files actually exist."""
    discovered = discover_examples(examples_dir)

    for input_file, schema_file, example_name in discovered:
        assert input_file.exists(), f"Input file for {example_name} does not exist: {input_file}"
        if schema_file:
            assert schema_file.exists(), f"Schema file for {example_name} does not exist: {schema_file}"


if __name__ == "__main__":
    # This allows running the tests directly
    pytest.main([__file__, "-v"])
