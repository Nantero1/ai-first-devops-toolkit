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


class TestExampleComprehensive:
    """Comprehensive testing of discovered examples - single execution per example.

    This test class executes each example once and validates:
    1. Execution reliability (always)
    2. Schema compliance (if schema exists)
    3. LLM-as-judge quality assessment (if not smoke test mode)

    Optimized for cost and time efficiency.
    """

    @pytest.mark.asyncio
    async def test_example_comprehensive(
        self,
        environment_check,
        llm_ci_runner,
        temp_files,
        llm_judge,
        load_example_file,
        assert_execution_success,
        assert_judgment_passed,
        rich_test_output,
        input_file,
        schema_file,
        example_name,
        smoke_test_mode,
    ):
        """Comprehensive test of a single example - execute once, validate everything."""
        mode_indicator = "🚀 SMOKE TEST" if smoke_test_mode else "🎯 FULL TEST"
        console.print(
            f"\n{mode_indicator} - Comprehensive testing of {example_name}...",
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
        assert_execution_success(returncode, stdout, stderr, f"{example_name} Comprehensive")

        # Load result for all validations (handle both JSON and YAML output)
        import yaml

        output_path = Path(output_file)

        if output_path.suffix.lower() in [".yaml", ".yml"]:
            with open(output_file, "r") as f:
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
            await self._evaluate_example_quality(
                result,
                input_file,
                example_name,
                llm_judge,
                load_example_file,
                assert_judgment_passed,
                rich_test_output,
            )
            console.print(f"  ✅ {example_name} quality assessment passed", style="green")

        console.print(
            f"🎉 {example_name} comprehensive test completed successfully",
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
            with open(schema_file, "r") as f:
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

    async def _evaluate_example_quality(
        self,
        result: dict,
        input_file,
        example_name: str,
        llm_judge,
        load_example_file,
        assert_judgment_passed,
        rich_test_output,
    ):
        """Evaluate example quality using LLM-as-judge based on example type."""
        response_data = result.get("response", {})

        from pathlib import Path

        input_path = Path(input_file)

        if input_path.suffix.lower() == ".hbs":
            # Template-based example - use template content as context
            with open(input_file, "r") as f:
                template_content = f.read()

            # For template examples, we evaluate output quality against template purpose
            # rather than query-response relevance
            evaluation_query = f"Template-based generation using: {template_content[:200]}..."
            input_context = f"Template-based example: {example_name}. The AI was asked to process a Handlebars template and generate structured output."
        else:
            # JSON-based example - load from input file
            input_data = load_example_file(str(input_file))
            evaluation_query = input_data["messages"][-1]["content"]
            input_context = f"Standard query-response example: {example_name}"

        # Determine evaluation criteria based on example type
        criteria = self._get_evaluation_criteria(example_name)

        if not criteria:
            console.print(
                f"  ℹ️ {example_name} - no specific quality criteria, skipping LLM-as-judge",
                style="yellow",
            )
            return

        # Format response for judgment
        if isinstance(response_data, dict):
            response_text = json.dumps(response_data, indent=2)
        else:
            response_text = str(response_data)

        # Evaluate with LLM-as-judge
        console.print(
            f"  🧑‍⚖️ Evaluating {example_name} quality with LLM-as-judge...",
            style="cyan",
        )
        judgment = await llm_judge(
            query=evaluation_query,
            response=response_text,
            criteria=criteria,
            input_context=input_context,
        )

        # Determine minimum score based on example complexity
        min_score = self._get_minimum_score(example_name)
        assert_judgment_passed(
            judgment,
            f"{example_name} Quality",
            min_score=min_score,
            rich_output=rich_test_output,
        )

    def _get_evaluation_criteria(self, example_name: str) -> str:
        """Get evaluation criteria based on example type."""
        name_lower = example_name.lower()

        # Template-based example criteria - focus on output quality
        if "static-example" in name_lower and "template" in name_lower:
            return """
            For this template-based example, evaluate the output quality focusing on:
            - Structured output format and completeness
            - Technical accuracy of any analysis provided
            - Appropriate use of template variables and formatting
            - Clarity and usefulness of generated content
            - Adherence to expected output schema
            Note: For template examples, 'relevance' should assess how well the output fulfills the template's intended purpose.
            """

        if "pr-review" in name_lower and "template" in name_lower:
            return """
            For this PR review template example, evaluate the output quality focusing on:
            - Structured PR review format and completeness
            - Technical accuracy of review comments
            - Appropriate use of template variables for PR context
            - Professional tone and constructive feedback
            - Adherence to expected output schema
            Note: For template examples, 'relevance' should assess how well the output fulfills the template's intended purpose.
            """

        # Standard JSON-based example criteria (query-response focused)
        if "sentiment" in name_lower:
            return """
            - Should analyze sentiment accurately based on the input text
            - Should provide appropriate confidence scores (0-1 range)
            - Should identify relevant key points from the text
            - Should generate concise, meaningful summaries
            - Should follow the structured output format correctly
            - Should demonstrate understanding of sentiment analysis concepts
            """

        # Code review criteria
        if "code-review" in name_lower or "review" in name_lower:
            return """
            - Should provide thorough technical analysis of the code
            - Should identify potential issues, bugs, or improvements
            - Should give constructive, actionable feedback
            - Should demonstrate understanding of code quality principles
            - Should assess security implications where relevant
            - Should provide appropriate severity ratings
            - Should be professional and helpful in tone
            """

        # Vulnerability analysis criteria
        if "vulnerability" in name_lower or "security" in name_lower:
            return """
            - Should identify security vulnerabilities accurately
            - Should assess risk levels appropriately
            - Should provide actionable remediation steps
            - Should demonstrate understanding of security principles
            - Should be thorough and systematic in analysis
            """

        # PR description criteria
        if "pr-description" in name_lower or "pull-request" in name_lower:
            return """
            - Should provide clear, comprehensive PR description
            - Should summarize changes effectively
            - Should identify key impacts and considerations
            - Should be well-structured and professional
            - Should follow good PR description practices
            """

        # Changelog criteria
        if "changelog" in name_lower:
            return """
            - Should create well-structured changelog entries
            - Should categorize changes appropriately
            - Should be clear and informative
            - Should follow changelog conventions
            - Should prioritize important changes
            """

        # Autonomous development criteria
        if "autonomous" in name_lower or "development-plan" in name_lower:
            return """
            - Should provide comprehensive development planning
            - Should demonstrate understanding of software architecture
            - Should include realistic timelines and milestones
            - Should consider quality gates and risk assessment
            - Should be actionable and well-structured
            """

        # General criteria for simple examples
        if "simple" in name_lower or "basic" in name_lower:
            return """
            - Should provide clear, accurate explanations
            - Should be well-structured and easy to understand
            - Should demonstrate good knowledge of the topic
            - Should be appropriately concise yet comprehensive
            """

        # Return None if no specific criteria - skip LLM-as-judge
        return None

    def _get_minimum_score(self, example_name: str) -> int:
        """Get minimum score requirement based on example complexity."""
        name_lower = example_name.lower()

        # Higher standards for complex examples
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
        for template_file in examples_dir.rglob("template.hbs"):
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
                examples.append((template_file, schema_file, f"{example_name}_template"))

        # Parametrize the test
        metafunc.parametrize("input_file,schema_file,example_name", examples)
