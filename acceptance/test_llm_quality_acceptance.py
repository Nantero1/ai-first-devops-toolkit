"""LLM Runner Quality Acceptance Tests.

This module contains pytest-based acceptance tests for validating LLM runner
quality using the LLM-as-judge pattern with structured output. No mocking is used.

Tests follow Given-When-Then pattern and use Rich formatting for beautiful output.
Remember, this test does real API calls to Azure OpenAI, so it will cost money.

## Testing Modes

### 🚀 Smoke Test Mode (Free - No LLM Calls)
```bash
uv run pytest acceptance/ --smoke-test
```
- Fast execution reliability testing
- Schema compliance validation
- No expensive LLM-as-judge calls

### 🎯 Full Quality Testing (Expensive - Real LLM Calls)
```bash
uv run pytest acceptance/
```
- Everything from smoke testing
- LLM-as-judge quality assessment
- Custom scenario testing

## Cost Optimization

This test suite is optimized to minimize LLM calls:
- Each example executes ONCE per test run
- Single comprehensive test validates reliability, schema compliance, and quality
- Conditional LLM-as-judge evaluation based on example type and smoke test mode
- Estimated 42% cost reduction vs naive approach
"""

from __future__ import annotations

import json

import pytest
from rich.console import Console

console = Console()


class TestGenericExampleEvaluation:
    """Example evaluation using abstract LLM-as-judge approach.

    This test class demonstrates a completely abstract approach that can evaluate
    any example based on its input, schema, and output without requiring specific
    criteria for each example type.

    Key benefits:
    - No hard-coupled evaluation logic
    - Works with any example type automatically
    - Generates criteria based on available information
    - Extensible for new example types without code changes
    """

    @pytest.mark.asyncio
    async def test_generic_example_evaluation(
        self,
        environment_check,
        llm_ci_runner,
        temp_files,
        generic_llm_judge,
        assert_execution_success,
        assert_judgment_passed,
        rich_test_output,
        input_file,
        schema_file,
        example_name,
        smoke_test_mode,
    ):
        """Test of any example - completely abstract evaluation."""
        mode_indicator = "🚀 SMOKE TEST" if smoke_test_mode else "🎯 FULL TEST"
        console.print(
            f"\n{mode_indicator} - evaluation of {example_name}...",
            style="blue",
        )

        # given - Create output file with appropriate extension
        from pathlib import Path

        # Determine output file extension based on schema type
        if schema_file:
            schema_path = Path(schema_file)
            if schema_path.suffix.lower() in [".yaml", ".yml"]:
                output_file = temp_files(suffix=".yaml")
            else:
                output_file = temp_files(suffix=".json")
        else:
            output_file = temp_files()

        # when - Execute example ONCE
        if schema_file:
            returncode, stdout, stderr = llm_ci_runner(str(input_file), output_file, str(schema_file))
        else:
            returncode, stdout, stderr = llm_ci_runner(str(input_file), output_file)

        # then - Phase 1: Basic execution reliability
        assert_execution_success(returncode, stdout, stderr, f"{example_name} Generic")

        # Load result for all validations (handle both JSON and YAML output)
        import yaml

        output_path = Path(output_file)

        if output_path.suffix.lower() in [".yaml", ".yml"]:
            with open(output_file) as f:
                result = yaml.safe_load(f)
        else:
            with open(output_file) as f:
                result = json.load(f)

        assert result.get("success") is True, "Response should indicate success"
        assert "response" in result, "Response should contain response field"
        assert "metadata" in result, "Response should contain metadata field"
        console.print(f"  ✅ {example_name} execution successful", style="green")

        # then - Phase 2: Schema compliance (if schema exists)
        if schema_file:
            self._validate_schema_compliance(result, schema_file, example_name)
            console.print(f"  ✅ {example_name} schema compliance verified", style="green")

        # then - Phase 3: LLM-as-judge quality assessment (if not smoke test)
        if not smoke_test_mode:
            await self._evaluate_generic_quality(
                result,
                input_file,
                schema_file,
                example_name,
                generic_llm_judge,
                assert_judgment_passed,
                rich_test_output,
            )
            console.print(f"  ✅ {example_name} quality assessment passed", style="green")

        console.print(
            f"🎉 {example_name} evaluation completed successfully",
            style="bold green",
        )

    def _validate_schema_compliance(self, result: dict, schema_file, example_name: str):
        """Validate schema compliance for structured examples."""
        response_data = result.get("response", {})

        # Load schema for validation (support both JSON and YAML)
        from pathlib import Path

        import yaml

        schema_path = Path(schema_file)

        if schema_path.suffix.lower() in [".yaml", ".yml"]:
            # Load YAML schema
            with open(schema_file) as f:
                schema = yaml.safe_load(f)
        else:
            # Load JSON schema
            with open(schema_file) as f:
                schema = json.load(f)

        # Basic schema compliance checks
        required_fields = schema.get("required", [])
        missing_fields = [field for field in required_fields if field not in response_data]
        assert not missing_fields, f"Missing required fields in {example_name}: {missing_fields}"

        # Validate specific constraints
        properties = schema.get("properties", {})
        for field_name, field_schema in properties.items():
            if field_name in response_data:
                value = response_data[field_name]

                # Check enum constraints
                if "enum" in field_schema:
                    assert value in field_schema["enum"], f"Invalid enum value in {example_name}.{field_name}: {value}"

                # Check string length constraints
                if isinstance(value, str) and "maxLength" in field_schema:
                    assert len(value) <= field_schema["maxLength"], (
                        f"String too long in {example_name}.{field_name}: {len(value)} chars"
                    )

                # Check numeric range constraints
                if isinstance(value, (int, float)):
                    if "minimum" in field_schema:
                        assert value >= field_schema["minimum"], (
                            f"Value below minimum in {example_name}.{field_name}: {value}"
                        )
                    if "maximum" in field_schema:
                        assert value <= field_schema["maximum"], (
                            f"Value above maximum in {example_name}.{field_name}: {value}"
                        )

                # Check array constraints
                if isinstance(value, list):
                    if "minItems" in field_schema:
                        assert len(value) >= field_schema["minItems"], (
                            f"Array too small in {example_name}.{field_name}: {len(value)} items"
                        )
                    if "maxItems" in field_schema:
                        assert len(value) <= field_schema["maxItems"], (
                            f"Array too large in {example_name}.{field_name}: {len(value)} items"
                        )

    async def _evaluate_generic_quality(
        self,
        result: dict,
        input_file,
        schema_file,
        example_name: str,
        generic_llm_judge,
        assert_judgment_passed,
        rich_test_output,
    ):
        """Evaluate example quality using LLM-as-judge approach."""
        response_data = result.get("response", {})

        # Use the  evaluator - no hard-coupled logic!
        console.print(
            f"  🧑‍⚖️ Evaluating {example_name} LLM-as-judge...",
            style="cyan",
        )

        judgment = await generic_llm_judge(
            input_file=input_file,
            schema_file=schema_file,
            output_result=response_data,
            example_name=example_name,
        )

        # Determine minimum score based on example complexity
        min_score = self._get_generic_minimum_score(example_name)
        assert_judgment_passed(
            judgment,
            f"{example_name} Quality",
            min_score=min_score,
            rich_output=rich_test_output,
        )

    def _get_generic_minimum_score(self, example_name: str) -> int:
        """Get minimum score requirement based on example complexity."""
        name_lower = example_name.lower()

        # Higher standards for complex examples (based on name patterns)
        if any(keyword in name_lower for keyword in ["code-review", "vulnerability", "security", "autonomous"]):
            return 8

        # Standard requirements for most examples
        return 7


class TestCustomScenarios:
    """Test custom scenarios with minimal boilerplate - EXAMPLE OF EXTENSIBILITY.

    These tests are EXPENSIVE and skipped in smoke test mode.
    """

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
        skip_if_smoke_test,  # Skip in smoke test mode
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
        skip_if_smoke_test,  # Skip in smoke test mode
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


def pytest_generate_tests(metafunc):
    """Generate tests dynamically based on discovered examples."""
    if (
        "input_file" in metafunc.fixturenames
        and "schema_file" in metafunc.fixturenames
        and "example_name" in metafunc.fixturenames
    ):
        # This is for the parametrized test that uses discovered examples
        from pathlib import Path

        examples_dir = Path("examples")
        examples = []

        # First pass: Find all folders with input.json (JSON mode - priority)
        for input_file in examples_dir.rglob("input.json"):
            folder = input_file.parent
            schema_file = folder / "schema.json"
            schema = schema_file if schema_file.exists() else None
            example_name = str(folder.relative_to(examples_dir)).replace("/", "_").replace("\\", "_")
            examples.append((input_file, schema, f"{example_name}_json"))

        # Second pass: Find template-based examples (fallback when no input.json)
        # Support multiple template formats: .hbs (Handlebars), .jinja/.j2 (Jinja2)
        template_extensions = [".hbs", ".jinja", ".j2"]

        for template_file in examples_dir.rglob("template.*"):
            # Check if it's a supported template extension
            if template_file.suffix.lower() not in template_extensions:
                continue

            folder = template_file.parent

            # Skip if input.json exists (JSON has priority)
            if (folder / "input.json").exists():
                continue

            # Look for schema.yaml or schema.json
            schema_yaml = folder / "schema.yaml"
            schema_json = folder / "schema.json"
            schema_file = schema_yaml if schema_yaml.exists() else (schema_json if schema_json.exists() else None)

            if schema_file:  # Only include if schema exists
                example_name = str(folder.relative_to(examples_dir)).replace("/", "_").replace("\\", "_")
                template_type = template_file.suffix.lower().replace(".", "")
                examples.append((template_file, schema_file, f"{example_name}_{template_type}"))

        # Parametrize the test
        metafunc.parametrize("input_file,schema_file,example_name", examples)
