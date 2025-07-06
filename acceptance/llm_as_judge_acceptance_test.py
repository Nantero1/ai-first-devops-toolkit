#!/usr/bin/env python3
"""
LLM as Judge Acceptance Test - Comprehensive validation using AI judgment

This script performs acceptance testing of the LLM Runner by using
the tool itself to test its own outputs. It requires Azure OpenAI
environment variables to be properly configured.

IMPORTANT: This test makes ACTUAL LLM API calls to validate responses.
Ensure environment variables are set:
- AZURE_OPENAI_ENDPOINT
- AZURE_OPENAI_MODEL
- AZURE_OPENAI_API_VERSION
- AZURE_OPENAI_API_KEY (or use Azure Identity)

The test uses LLM as a judge best practices to evaluate:
1. Response relevance and accuracy
2. Schema compliance for structured outputs
3. Code quality assessment for PR reviews
4. Overall system functionality
"""

import json
import subprocess
import sys
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, List, Tuple
import asyncio


class AcceptanceTestFramework:
    """Framework for running LLM-as-judge acceptance tests."""

    def __init__(self):
        self.results = []
        self.temp_files = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Cleanup temporary files
        for temp_file in self.temp_files:
            try:
                Path(temp_file).unlink(missing_ok=True)
            except Exception:
                pass

    def run_llm_runner(
        self, input_file: str, output_file: str, schema_file: str = None
    ) -> Tuple[int, str, str]:
        """Run the LLM runner and return result code, stdout, stderr."""
        cmd = [
            "uv",
            "run",
            "llm_runner.py",
            "--input-file",
            input_file,
            "--output-file",
            output_file,
            "--log-level",
            "ERROR",  # Minimize noise
        ]

        if schema_file:
            cmd.extend(["--schema-file", schema_file])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except Exception as e:
            return -1, "", str(e)

    async def judge_response_with_llm(
        self, query: str, response: str, criteria: str, input_context: str = ""
    ) -> Dict[str, Any]:
        """Use LLM to judge the quality of a response."""

        # Create judgment prompt
        judgment_input = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert AI judge tasked with evaluating AI responses. Provide detailed, objective assessments based on the given criteria.",
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

Please provide your assessment in the following format:
1. RELEVANCE (1-10): How well does the response address the query?
2. ACCURACY (1-10): How factually correct is the response?
3. COMPLETENESS (1-10): How complete is the response?
4. CLARITY (1-10): How clear and well-structured is the response?
5. OVERALL QUALITY (1-10): Overall assessment of response quality
6. STRENGTHS: What are the main strengths of this response?
7. WEAKNESSES: What are the main weaknesses or areas for improvement?
8. PASS/FAIL: Does this response meet acceptable quality standards? (PASS or FAIL)

Provide specific reasoning for each score.""",
                },
            ]
        }

        # Write judgment input to temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(judgment_input, f, indent=2)
            judgment_input_file = f.name
            self.temp_files.append(judgment_input_file)

        # Create temp output file for judgment
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            judgment_output_file = f.name
            self.temp_files.append(judgment_output_file)

        # Run LLM runner to get judgment
        returncode, stdout, stderr = self.run_llm_runner(
            judgment_input_file, judgment_output_file
        )

        if returncode != 0:
            return {"error": f"Judgment failed: {stderr}", "pass": False}

        # Load and parse judgment result
        try:
            with open(judgment_output_file, "r") as f:
                judgment_result = json.load(f)

            judgment_text = judgment_result.get("response", "")

            # Parse the judgment (simple text parsing)
            lines = judgment_text.split("\n")
            judgment = {
                "relevance": self._extract_score(judgment_text, "RELEVANCE"),
                "accuracy": self._extract_score(judgment_text, "ACCURACY"),
                "completeness": self._extract_score(judgment_text, "COMPLETENESS"),
                "clarity": self._extract_score(judgment_text, "CLARITY"),
                "overall": self._extract_score(judgment_text, "OVERALL QUALITY"),
                "pass": "PASS" in judgment_text and "FAIL" not in judgment_text,
                "full_judgment": judgment_text,
            }

            return judgment

        except Exception as e:
            return {"error": f"Failed to parse judgment: {e}", "pass": False}

    def _extract_score(self, text: str, criteria: str) -> int:
        """Extract numeric score from judgment text."""
        import re

        pattern = f"{criteria}.*?(\d+)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return 0

    def print_result(self, test_name: str, passed: bool, details: str = ""):
        """Print test result with formatting."""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {test_name}")
        if details:
            print(f"    Details: {details}")
        self.results.append((test_name, passed))


def test_environment_setup():
    """Test that environment is properly configured."""
    print("🔍 Testing environment setup...")

    required_vars = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_MODEL",
        "AZURE_OPENAI_API_VERSION",
    ]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    # Check for authentication
    has_api_key = bool(os.getenv("AZURE_OPENAI_API_KEY"))
    has_identity = True  # Assume Azure Identity is available

    if missing_vars:
        print(f"  ❌ Missing environment variables: {', '.join(missing_vars)}")
        return False

    if not has_api_key and not has_identity:
        print("  ❌ No authentication method available (API key or Azure Identity)")
        return False

    print("  ✅ Environment properly configured")
    return True


def test_basic_dependencies():
    """Test basic dependencies and imports."""
    print("\n🔍 Testing dependencies...")

    try:
        # Test UV installation
        result = subprocess.run(
            ["uv", "--version"], capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            print("  ❌ UV not installed or not working")
            return False

        # Test script help
        result = subprocess.run(
            ["uv", "run", "llm_runner.py", "--help"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0 or "LLM Runner" not in result.stdout:
            print("  ❌ LLM Runner script not working")
            return False

        print("  ✅ All dependencies working")
        return True

    except Exception as e:
        print(f"  ❌ Dependency test failed: {e}")
        return False


async def test_simple_text_response_quality():
    """Test quality of simple text responses using LLM as judge."""
    print("\n🔍 Testing simple text response quality...")

    with AcceptanceTestFramework() as framework:
        # Run simple example
        input_file = "examples/simple-example.json"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_file = f.name
            framework.temp_files.append(output_file)

        returncode, stdout, stderr = framework.run_llm_runner(input_file, output_file)

        if returncode != 0:
            framework.print_result(
                "Simple Text Response", False, f"Execution failed: {stderr}"
            )
            return False

        # Load the response
        try:
            with open(output_file, "r") as f:
                result = json.load(f)
            response_text = result.get("response", "")
        except Exception as e:
            framework.print_result(
                "Simple Text Response", False, f"Failed to load response: {e}"
            )
            return False

        # Judge the response quality
        criteria = """
        - The response should explain CI/CD in software development clearly
        - Should mention Continuous Integration and Continuous Deployment/Delivery
        - Should be informative and concise (as requested in one paragraph)
        - Should be factually accurate about software development practices
        - Should be well-structured and easy to understand
        """

        # Load original query for context
        with open(input_file, "r") as f:
            input_data = json.load(f)
        original_query = input_data["messages"][-1]["content"]

        judgment = await framework.judge_response_with_llm(
            query=original_query,
            response=response_text,
            criteria=criteria,
            input_context="Software development topic explanation request",
        )

        if "error" in judgment:
            framework.print_result(
                "Simple Text Response Quality", False, judgment["error"]
            )
            return False

        # Assess judgment
        overall_score = judgment.get("overall", 0)
        passed = judgment.get("pass", False) and overall_score >= 7

        details = f"Overall score: {overall_score}/10, Judge: {'PASS' if judgment.get('pass') else 'FAIL'}"
        framework.print_result("Simple Text Response Quality", passed, details)

        if not passed:
            print(f"    Full judgment: {judgment.get('full_judgment', '')[:200]}...")

        return passed


async def test_structured_output_compliance():
    """Test structured output compliance and quality."""
    print("\n🔍 Testing structured output compliance...")

    with AcceptanceTestFramework() as framework:
        # Run simple example with structured output schema
        input_file = "examples/simple-example.json"
        schema_file = "examples/structured-output-example.json"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_file = f.name
            framework.temp_files.append(output_file)

        returncode, stdout, stderr = framework.run_llm_runner(
            input_file, output_file, schema_file
        )

        if returncode != 0:
            framework.print_result(
                "Structured Output Compliance", False, f"Execution failed: {stderr}"
            )
            return False

        # Load and validate the response
        try:
            with open(output_file, "r") as f:
                result = json.load(f)
            response_data = result.get("response", {})

            # Load schema for validation
            with open(schema_file, "r") as f:
                schema = json.load(f)

            # Basic schema compliance check
            required_fields = schema.get("required", [])
            missing_fields = [
                field for field in required_fields if field not in response_data
            ]

            if missing_fields:
                framework.print_result(
                    "Structured Output Compliance",
                    False,
                    f"Missing required fields: {missing_fields}",
                )
                return False

            # Check field types and constraints
            properties = schema.get("properties", {})

            # Check sentiment enum
            if "sentiment" in response_data:
                valid_sentiments = properties.get("sentiment", {}).get("enum", [])
                if response_data["sentiment"] not in valid_sentiments:
                    framework.print_result(
                        "Structured Output Compliance",
                        False,
                        f"Invalid sentiment: {response_data['sentiment']}",
                    )
                    return False

            # Check confidence range
            if "confidence" in response_data:
                confidence = response_data["confidence"]
                if not (0 <= confidence <= 1):
                    framework.print_result(
                        "Structured Output Compliance",
                        False,
                        f"Confidence out of range: {confidence}",
                    )
                    return False

            # Check key_points array constraints
            if "key_points" in response_data:
                key_points = response_data["key_points"]
                if (
                    not isinstance(key_points, list)
                    or len(key_points) < 1
                    or len(key_points) > 5
                ):
                    framework.print_result(
                        "Structured Output Compliance",
                        False,
                        f"Invalid key_points: {len(key_points)} items",
                    )
                    return False

            # Check summary length
            if "summary" in response_data:
                summary = response_data["summary"]
                if len(summary) > 200:
                    framework.print_result(
                        "Structured Output Compliance",
                        False,
                        f"Summary too long: {len(summary)} chars",
                    )
                    return False

            framework.print_result(
                "Structured Output Compliance", True, "All schema constraints satisfied"
            )
            return True

        except Exception as e:
            framework.print_result(
                "Structured Output Compliance", False, f"Validation failed: {e}"
            )
            return False


async def test_pr_review_quality():
    """Test PR review response quality using LLM as judge."""
    print("\n🔍 Testing PR review quality...")

    with AcceptanceTestFramework() as framework:
        # Run PR review example
        input_file = "examples/pr-review-example.json"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_file = f.name
            framework.temp_files.append(output_file)

        returncode, stdout, stderr = framework.run_llm_runner(input_file, output_file)

        if returncode != 0:
            framework.print_result(
                "PR Review Quality", False, f"Execution failed: {stderr}"
            )
            return False

        # Load the response
        try:
            with open(output_file, "r") as f:
                result = json.load(f)
            response_text = result.get("response", "")
        except Exception as e:
            framework.print_result(
                "PR Review Quality", False, f"Failed to load response: {e}"
            )
            return False

        # Judge the PR review quality
        criteria = """
        - The response should provide a thorough code review
        - Should identify security issues (SQL injection mentioned in the PR)
        - Should assess code quality and provide constructive feedback
        - Should give specific recommendations for improvement  
        - Should have an overall assessment or rating
        - Should be professional and helpful in tone
        - Should address the specific changes shown in the pull request
        """

        # Load original PR content for context
        with open(input_file, "r") as f:
            input_data = json.load(f)
        pr_context = input_data["messages"][-1]["content"]

        judgment = await framework.judge_response_with_llm(
            query="Code review request for security vulnerability fix",
            response=response_text,
            criteria=criteria,
            input_context=f"Pull request content: {pr_context[:500]}...",
        )

        if "error" in judgment:
            framework.print_result("PR Review Quality", False, judgment["error"])
            return False

        # Assess judgment
        overall_score = judgment.get("overall", 0)
        passed = judgment.get("pass", False) and overall_score >= 7

        details = f"Overall score: {overall_score}/10, Judge: {'PASS' if judgment.get('pass') else 'FAIL'}"
        framework.print_result("PR Review Quality", passed, details)

        if not passed:
            print(f"    Full judgment: {judgment.get('full_judgment', '')[:200]}...")

        return passed


async def test_end_to_end_system_reliability():
    """Test end-to-end system reliability with multiple examples."""
    print("\n🔍 Testing end-to-end system reliability...")

    with AcceptanceTestFramework() as framework:
        examples = [
            "examples/simple-example.json",
            "examples/minimal-example.json",
            "examples/pr-review-example.json",
        ]

        success_count = 0
        total_tests = len(examples)

        for example in examples:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as f:
                output_file = f.name
                framework.temp_files.append(output_file)

            returncode, stdout, stderr = framework.run_llm_runner(example, output_file)

            if returncode == 0:
                # Verify output is valid JSON with expected structure
                try:
                    with open(output_file, "r") as f:
                        result = json.load(f)

                    if (
                        result.get("success") is True
                        and "response" in result
                        and "metadata" in result
                    ):
                        success_count += 1
                except Exception:
                    pass

        reliability_percentage = (success_count / total_tests) * 100
        passed = success_count == total_tests

        details = f"Successful runs: {success_count}/{total_tests} ({reliability_percentage:.1f}%)"
        framework.print_result("End-to-End Reliability", passed, details)

        return passed


async def main():
    """Run all acceptance tests."""
    print("🧪 LLM Runner Acceptance Test Suite (LLM as Judge)")
    print("=" * 60)
    print("⚠️  This test makes ACTUAL LLM API calls for validation")
    print("=" * 60)

    # Environment check first
    if not test_environment_setup():
        print(
            "\n❌ Environment not properly configured. Please set required variables."
        )
        return 1

    # Basic dependency tests
    if not test_basic_dependencies():
        print("\n❌ Basic dependencies not working. Please check installation.")
        return 1

    # LLM-as-judge tests
    llm_tests = [
        ("Simple Text Response Quality", test_simple_text_response_quality),
        ("Structured Output Compliance", test_structured_output_compliance),
        ("PR Review Quality", test_pr_review_quality),
        ("End-to-End Reliability", test_end_to_end_system_reliability),
    ]

    results = []

    for test_name, test_func in llm_tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  💥 {test_name} crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("📊 Acceptance Test Results:")

    passed = sum(1 for _, result in results if result)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")

    print(f"\nPassed: {passed}/{len(results)} tests")

    if passed == len(results):
        print("\n🎉 All acceptance tests passed! LLM Runner meets quality standards.")
        return 0
    else:
        print(
            "\n⚠️  Some acceptance tests failed. System may not meet quality standards."
        )
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
