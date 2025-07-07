"""LLM Runner Quality Acceptance Tests.

This module contains pytest-based acceptance tests for validating LLM runner
quality using the LLM-as-judge pattern with structured output. No mocking is used.

Tests follow Given-When-Then pattern and use Rich formatting for beautiful output.
Remember, this test does real API calls to Azure OpenAI, so it will cost money.
"""

from __future__ import annotations

import json

import pytest
from rich.console import Console

console = Console()


class TestTextResponseQuality:
    """Test quality of text responses using LLM-as-judge evaluation."""

    @pytest.mark.asyncio
    async def test_simple_text_response_quality(
        self,
        environment_check,
        llm_ci_runner,
        temp_files,
        llm_judge,
        example_files,
        load_example_file,
        assert_execution_success,
        assert_judgment_passed,
        rich_test_output,
    ):
        """Test that simple text responses meet quality standards."""
        console.print("\n🔍 Testing simple text response quality...", style="blue")

        # given
        input_file = example_files["simple"]
        output_file = temp_files()
        original_query = load_example_file(input_file)["messages"][-1]["content"]

        criteria = """
        - The response should explain CI/CD in software development clearly
        - Should mention Continuous Integration and Continuous Deployment/Delivery
        - Should be informative and concise (as requested in one paragraph)
        - Should be factually accurate about software development practices
        - Should be well-structured and easy to understand
        """

        # when
        returncode, stdout, stderr = llm_ci_runner(input_file, output_file)

        # then
        assert_execution_success(returncode, stdout, stderr, "Simple Text Response")

        # Load and evaluate response
        with open(output_file) as f:
            result = json.load(f)
        response_text = result.get("response", "")

        # Judge the response quality
        judgment = await llm_judge(
            query=original_query,
            response=response_text,
            criteria=criteria,
            input_context="Software development topic explanation request",
        )

        assert_judgment_passed(judgment, "Simple Text Response", rich_output=rich_test_output)


class TestStructuredOutputCompliance:
    """Test structured output compliance and schema validation."""

    def test_structured_output_schema_compliance(
        self,
        environment_check,
        llm_ci_runner,
        temp_files,
        example_files,
        assert_execution_success,
    ):
        """Test that structured output complies with JSON schema constraints."""
        console.print("\n🔍 Testing structured output compliance...", style="blue")

        # given
        input_file = example_files["simple"]
        schema_file = example_files["structured_schema"]
        output_file = temp_files()

        # when
        returncode, stdout, stderr = llm_ci_runner(input_file, output_file, schema_file)

        # then
        assert_execution_success(returncode, stdout, stderr, "Structured Output")

        # Load and validate the response
        with open(output_file) as f:
            result = json.load(f)
        response_data = result.get("response", {})

        # Load schema for validation
        with open(schema_file) as f:
            schema = json.load(f)

        # Basic schema compliance checks
        required_fields = schema.get("required", [])
        missing_fields = [field for field in required_fields if field not in response_data]

        assert not missing_fields, f"Missing required fields: {missing_fields}"

        # Validate specific constraints
        properties = schema.get("properties", {})

        # Check sentiment enum
        if "sentiment" in response_data:
            valid_sentiments = properties.get("sentiment", {}).get("enum", [])
            assert response_data["sentiment"] in valid_sentiments, f"Invalid sentiment: {response_data['sentiment']}"

        # Check confidence range
        if "confidence" in response_data:
            confidence = response_data["confidence"]
            assert 0 <= confidence <= 1, f"Confidence out of range: {confidence}"

        # Check key_points array constraints
        if "key_points" in response_data:
            key_points = response_data["key_points"]
            assert isinstance(key_points, list), "key_points must be an array"
            assert 1 <= len(key_points) <= 5, f"Invalid key_points count: {len(key_points)}"

        # Check summary length
        if "summary" in response_data:
            summary = response_data["summary"]
            assert len(summary) <= 200, f"Summary too long: {len(summary)} chars"

        console.print("✅ All schema constraints satisfied", style="green")


class TestCodeReviewQuality:
    """Test code review response quality using LLM-as-judge evaluation."""

    @pytest.mark.asyncio
    async def test_pr_review_quality(
        self,
        environment_check,
        llm_ci_runner,
        temp_files,
        llm_judge,
        example_files,
        load_example_file,
        assert_execution_success,
        assert_judgment_passed,
        rich_test_output,
    ):
        """Test that PR review responses meet quality standards."""
        console.print("\n🔍 Testing PR review quality...", style="blue")

        # given
        input_file = example_files["pr_review"]
        output_file = temp_files()
        input_data = load_example_file(input_file)
        pr_context = input_data["messages"][-1]["content"]

        criteria = """
        - The response should provide a thorough code review
        - Should identify security issues (SQL injection mentioned in the PR)
        - Should assess code quality and provide constructive feedback
        - Should give specific recommendations for improvement
        - Should have an overall assessment or rating
        - Should be professional and helpful in tone
        - Should address the specific changes shown in the pull request
        """

        # when
        returncode, stdout, stderr = llm_ci_runner(input_file, output_file)

        # then
        assert_execution_success(returncode, stdout, stderr, "PR Review")

        # Load and evaluate response
        with open(output_file) as f:
            result = json.load(f)
        response_text = result.get("response", "")

        # Judge the PR review quality
        judgment = await llm_judge(
            query="Code review request for security vulnerability fix",
            response=response_text,
            criteria=criteria,
            input_context=f"Pull request content: {pr_context[:500]}...",
        )

        assert_judgment_passed(judgment, "PR Review", rich_output=rich_test_output)


class TestSystemReliability:
    """Test end-to-end system reliability and stability."""

    @pytest.mark.parametrize("example_name", ["simple", "minimal", "pr_review"])
    def test_example_execution_reliability(
        self,
        environment_check,
        llm_ci_runner,
        temp_files,
        example_files,
        assert_execution_success,
        example_name,
    ):
        """Test that all examples execute successfully with valid output structure."""
        console.print(f"\n🔍 Testing {example_name} example reliability...", style="blue")

        # given
        input_file = example_files[example_name]
        output_file = temp_files()

        # when
        returncode, stdout, stderr = llm_ci_runner(input_file, output_file)

        # then
        assert_execution_success(returncode, stdout, stderr, f"{example_name.title()} Example")

        # Verify output structure
        with open(output_file) as f:
            result = json.load(f)

        assert result.get("success") is True, "Response should indicate success"
        assert "response" in result, "Response should contain response field"
        assert "metadata" in result, "Response should contain metadata field"

        console.print(f"✅ {example_name.title()} example executed successfully", style="green")

    def test_concurrent_execution_stability(
        self,
        environment_check,
        llm_ci_runner,
        temp_files,
        example_files,
        assert_execution_success,
    ):
        """Test system stability under concurrent execution scenarios."""
        console.print("\n🔍 Testing concurrent execution stability...", style="blue")

        # given
        examples = ["simple", "minimal", "pr_review"]
        results = []

        # when - execute all examples
        for example_name in examples:
            input_file = example_files[example_name]
            output_file = temp_files()

            returncode, stdout, stderr = llm_ci_runner(input_file, output_file)
            results.append((example_name, returncode, stdout, stderr, output_file))

        # then - verify all succeeded
        for example_name, returncode, stdout, stderr, output_file in results:
            assert_execution_success(returncode, stdout, stderr, f"{example_name.title()} Concurrent")

            # Verify output structure
            with open(output_file) as f:
                result = json.load(f)

            assert result.get("success") is True, f"{example_name} should indicate success"
            assert "response" in result, f"{example_name} should contain response field"

        success_rate = len([r for r in results if r[1] == 0]) / len(results) * 100
        console.print(f"✅ System reliability: {success_rate:.1f}% success rate", style="green")

        assert success_rate == 100.0, f"Expected 100% success rate, got {success_rate:.1f}%"


class TestQualityBenchmarks:
    """Test quality benchmarks and performance standards."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "example_name,min_score",
        [
            ("simple", 7),
            ("pr_review", 8),
        ],
    )
    async def test_quality_benchmarks(
        self,
        environment_check,
        llm_ci_runner,
        temp_files,
        llm_judge,
        example_files,
        load_example_file,
        assert_execution_success,
        assert_judgment_passed,
        rich_test_output,
        example_name,
        min_score,
    ):
        """Test that responses meet specific quality benchmarks."""
        console.print(
            f"\n🔍 Testing {example_name} quality benchmark (min: {min_score}/10)...",
            style="blue",
        )

        # given
        input_file = example_files[example_name]
        output_file = temp_files()
        original_query = load_example_file(input_file)["messages"][-1]["content"]

        # Define criteria based on example type
        criteria_map = {
            "simple": """
            - Should provide clear, accurate explanations
            - Should be well-structured and easy to understand
            - Should demonstrate good knowledge of the topic
            - Should be appropriately concise yet comprehensive
            """,
            "pr_review": """
            - Should provide thorough technical analysis
            - Should identify potential issues and improvements
            - Should give constructive, actionable feedback
            - Should demonstrate deep understanding of code quality
            - Should be professional and helpful in tone
            """,
        }

        criteria = criteria_map.get(example_name, "General quality assessment")

        # when
        returncode, stdout, stderr = llm_ci_runner(input_file, output_file)

        # then
        assert_execution_success(returncode, stdout, stderr, f"{example_name.title()} Benchmark")

        # Load and evaluate response
        with open(output_file) as f:
            result = json.load(f)
        response_text = result.get("response", "")

        # Judge the response quality
        judgment = await llm_judge(
            query=original_query,
            response=response_text,
            criteria=criteria,
            input_context=f"Quality benchmark test for {example_name} example",
        )

        assert_judgment_passed(
            judgment,
            f"{example_name.title()} Quality Benchmark",
            min_score=min_score,
            rich_output=rich_test_output,
        )


class TestCustomScenarios:
    """Test custom scenarios with minimal boilerplate - EXAMPLE OF EXTENSIBILITY."""

    @pytest.mark.asyncio
    async def test_mathematical_reasoning_quality(
        self,
        environment_check,
        llm_ci_runner,
        temp_files,
        llm_judge,
        assert_execution_success,
        assert_judgment_passed,
        rich_test_output,
    ):
        """Test mathematical reasoning quality - EXAMPLE: Only ~20 lines needed!"""
        console.print("\n🧮 Testing mathematical reasoning quality...", style="blue")

        # given
        math_input = {
            "messages": [
                {
                    "role": "user",
                    "content": "Solve this step by step: If a train travels 120 miles in 2 hours, and then 180 miles in 3 hours, what is the average speed for the entire journey?",
                }
            ]
        }
        input_file = temp_files(json.dumps(math_input, indent=2))
        output_file = temp_files()

        criteria = """
        - Should solve the problem step by step
        - Should show clear mathematical reasoning
        - Should arrive at the correct answer (60 mph)
        - Should explain the concept of average speed
        - Should be clear and educational
        """

        # when
        returncode, stdout, stderr = llm_ci_runner(input_file, output_file)

        # then
        assert_execution_success(returncode, stdout, stderr, "Mathematical Reasoning")

        with open(output_file) as f:
            result = json.load(f)
        response_text = result.get("response", "")

        judgment = await llm_judge(
            query="Mathematical word problem requiring step-by-step solution",
            response=response_text,
            criteria=criteria,
            input_context="Average speed calculation problem",
        )

        assert_judgment_passed(judgment, "Mathematical Reasoning", rich_output=rich_test_output)

    @pytest.mark.parametrize(
        "topic,min_score",
        [
            ("python_programming", 8),
            ("data_science", 7),
            ("machine_learning", 8),
        ],
    )
    @pytest.mark.asyncio
    async def test_technical_expertise_topics(
        self,
        environment_check,
        llm_ci_runner,
        temp_files,
        llm_judge,
        assert_execution_success,
        assert_judgment_passed,
        rich_test_output,
        topic,
        min_score,
    ):
        """Test technical expertise across different topics - EXAMPLE: Parametrized testing!"""
        console.print(f"\n🔬 Testing {topic} expertise (min: {min_score}/10)...", style="blue")

        # given - Dynamic test content based on topic
        topic_questions = {
            "python_programming": "Explain the difference between list comprehensions and generator expressions in Python, with examples.",
            "data_science": "What are the key steps in the data science process and how do you handle missing data?",
            "machine_learning": "Explain the bias-variance tradeoff in machine learning and how to address it.",
        }

        technical_input = {"messages": [{"role": "user", "content": topic_questions[topic]}]}
        input_file = temp_files(json.dumps(technical_input, indent=2))
        output_file = temp_files()

        criteria = f"""
        - Should demonstrate deep understanding of {topic.replace("_", " ")}
        - Should provide accurate technical information
        - Should include practical examples where appropriate
        - Should be clear and well-structured
        - Should show expertise level appropriate for the topic
        """

        # when
        returncode, stdout, stderr = llm_ci_runner(input_file, output_file)

        # then
        assert_execution_success(returncode, stdout, stderr, f"{topic.title()} Expertise")

        with open(output_file) as f:
            result = json.load(f)
        response_text = result.get("response", "")

        judgment = await llm_judge(
            query=f"Technical question about {topic.replace('_', ' ')}",
            response=response_text,
            criteria=criteria,
            input_context=f"Technical expertise assessment for {topic}",
        )

        assert_judgment_passed(
            judgment,
            f"{topic.title()} Technical Expertise",
            min_score=min_score,
            rich_output=rich_test_output,
        )
