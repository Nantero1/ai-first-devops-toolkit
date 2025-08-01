# Integration Tests

Integration tests for LLM CI Runner that test complete workflows with real internal logic and mocked external dependencies.

## Testing Philosophy

Integration tests validate **end-to-end behavior** by running the complete application pipeline while only mocking external API calls. This approach ensures:

- **Real business logic testing**: All internal components run normally
- **Realistic workflows**: Tests mirror actual user interactions  
- **External isolation**: Only HTTP APIs are mocked for reliability
- **Comprehensive coverage**: Full pipeline from CLI input to file output

## What We Mock vs What We Test

| **Mocked (External Dependencies)** | **Real (Internal Logic)** |
|-----------------------------------|--------------------------|
| Azure OpenAI HTTP API calls      | Service initialization   |
| Environment variables             | Template processing      |
| Command line arguments            | Schema validation        |
|                                   | File I/O operations      |
|                                   | Error handling           |
|                                   | All business logic       |

## Test Structure

```
tests/integration/
├── conftest.py                     # Fixtures and HTTP mocking setup
├── integration_helpers.py          # Helper classes and test data
├── test_cli_interface.py          # CLI argument parsing and validation
├── test_examples_integration.py   # End-to-end workflow testing
├── test_main_function.py          # Direct main() function testing  
├── test_string_template_integration.py # Template processing workflows
└── data/                          # Test data files
```

## Helper Classes

### IntegrationTestHelper
Provides common test functionality:

```python
# File creation with format support
input_file = helper.create_input_file("test.json", content)
schema_file = helper.create_schema_file("schema.json", schema)

# CLI command building
args = helper.build_cli_args(input_file=input_file, output_file=output_file)

# Complete test execution
result = await helper.run_integration_test(
    input_content=content,
    input_filename="input.json", 
    output_filename="output.json"
)

# Result validation
helper.assert_successful_response(result, expected_response_type="str")
```

### CommonTestData
Centralized test data:

```python
# Standard test inputs
input_data = CommonTestData.simple_chat_input()
schema = CommonTestData.sentiment_analysis_schema()

# Template data
template = CommonTestData.handlebars_template()
variables = CommonTestData.template_variables()
```

## Running Tests

```bash
# Run all integration tests
uv run pytest tests/integration/ -v

# Run specific test file
uv run pytest tests/integration/test_examples_integration.py -v

# Run with detailed output
uv run pytest tests/integration/ -v -s
```

## Writing Integration Tests

### Basic Test Pattern

```python
@pytest.mark.asyncio
async def test_feature_workflow(self, integration_helper, mock_azure_openai_responses):
    """Test complete feature workflow."""
    # given
    input_content = CommonTestData.simple_chat_input()
    
    # when
    result = await integration_helper.run_integration_test(
        input_content=input_content,
        input_filename="test_input.json",
        output_filename="test_output.json"
    )
    
    # then
    integration_helper.assert_successful_response(
        result, 
        expected_response_type="str",
        expected_content_substring="expected content"
    )
```

### Parametrized Testing

Use `pytest.mark.parametrize` for testing multiple scenarios:

```python
@pytest.mark.parametrize(
    "input_format,output_format",
    [
        pytest.param("json", "json", id="json_to_json"),
        pytest.param("json", "yaml", id="json_to_yaml"),
        pytest.param("yaml", "json", id="yaml_to_json"),
    ],
)
@pytest.mark.asyncio
async def test_format_combinations(self, integration_helper, mock_azure_openai_responses, input_format, output_format):
    """Test various input/output format combinations."""
    # Test implementation...
```

### CLI Interface Testing

```python
def test_cli_argument_validation(self, integration_helper):
    """Test CLI argument parsing."""
    # given
    command = integration_helper.build_cli_args(input_file="test.json", log_level="INVALID")
    
    # when
    result = integration_helper.run_cli_subprocess(command)
    
    # then
    assert result.returncode == 2  # Argument parsing error
    assert "invalid choice" in result.stderr.lower()
```

## Best Practices

1. **Use Given-When-Then structure** - All tests follow this pattern
2. **Leverage helper methods** - Reduce code duplication with `IntegrationTestHelper`
3. **Use parametrization** - Test multiple scenarios efficiently with `pytest.mark.parametrize`
4. **Test behavior, not implementation** - Focus on user-facing outcomes
5. **Mock only external dependencies** - Let internal logic run normally
6. **Use descriptive test names** - Clearly explain what is being tested
7. **Group related tests in classes** - Organize tests by functionality

## Fixtures Available

- `integration_helper` - Instance of `IntegrationTestHelper`
- `mock_azure_openai_responses` - HTTP mocking for Azure OpenAI API
- `temp_integration_workspace` - Temporary directory for test files

All tests follow the Given-When-Then pattern and focus on end-to-end behavior validation.

## Parametrized Testing with pytest.mark.parametrize

The refactored tests now use `pytest.mark.parametrize` with human-readable IDs for better test organization and reporting:

### Benefits of Parametrized Tests
- **Individual test reporting**: Each parameter combination shows as a separate test
- **Better failure isolation**: When one scenario fails, others continue running
- **Improved test discovery**: Each scenario has a descriptive ID for easy identification  
- **Enhanced debugging**: Clear test names make debugging specific scenarios easier
- **Cleaner output**: pytest shows detailed results for each parameter combination

### Example: Multiple Scenarios Parametrized
```python
@pytest.mark.parametrize(
    "scenario_name,input_data,schema_data,expected_type,expected_substring",
    [
        pytest.param(
            "simple_chat",
            CommonTestData.simple_chat_input(),
            None,
            "str",
            "mock response",
            id="simple_chat_text_output"
        ),
        pytest.param(
            "sentiment_analysis", 
            CommonTestData.sentiment_analysis_input(),
            CommonTestData.sentiment_analysis_schema(),
            "dict",
            None,
            id="sentiment_analysis_structured_output"
        ),
    ]
)
@pytest.mark.asyncio
async def test_multiple_scenarios_parametrized(
    self, integration_helper, mock_azure_openai_responses, 
    scenario_name, input_data, schema_data, expected_type, expected_substring
):
    """Test multiple scenarios using parametrized tests for better reporting."""
    # when
    result = await integration_helper.run_integration_test(
        input_content=input_data,
        schema_content=schema_data,
        input_filename=f"{scenario_name}_input.json",
        output_filename=f"{scenario_name}_output.json",
        schema_filename=f"{scenario_name}_schema.json" if schema_data else None,
    )
    
    # then
    integration_helper.assert_successful_response(
        result, expected_response_type=expected_type,
        expected_content_substring=expected_substring
    )
```


All tests follow the Given-When-Then pattern and focus on end-to-end behavior validation with significantly reduced maintenance overhead.