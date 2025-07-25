"""
Integration test fixtures and configuration for LLM Runner.

This file provides fixtures specific to integration testing with minimal mocking.
These tests focus on testing the interactions between components with
mocked external services (Azure OpenAI) but real internal logic.
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest
import respx
from httpx import Response


# Realistic SK Mock Factory Functions
# Based on README-research-semantic-kernel-realistic_mocks.md

def create_simple_sk_mock_response(content: str, template_name: str = "SimpleQuestion"):
    """Create a simple but effective SK mock response for integration tests."""
    from tests.mock_factory import create_mock_chat_message_content
    from unittest.mock import Mock
    
    # Use existing tested mock factory from the codebase
    chat_content = create_mock_chat_message_content(content=content)
    
    # Create simple FunctionResult-like object that our code can process
    class MockFunctionResult:
        def __init__(self, content_value):
            self.value = [content_value]  # SK returns list of ChatMessageContent
            self.function = Mock()
            self.function.name = template_name
    
    return MockFunctionResult(chat_content)


@pytest.fixture(autouse=True)
def mock_azure_service(monkeypatch):
    """
    Mock Azure environment variables for integration testing.

    This fixture sets up the integration test environment by:
    1. Setting required Azure OpenAI environment variables
    2. Providing realistic test endpoints and credentials

    The actual HTTP calls are mocked by the respx_mock fixture.
    """
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://test-openai.openai.azure.com")
    monkeypatch.setenv("AZURE_OPENAI_MODEL", "gpt-4o")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test-api-key-12345")
    monkeypatch.setenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")


@pytest.fixture
def respx_mock():
    """
    Mock HTTP requests to Azure OpenAI API using respx.

    This fixture provides proper HTTP-level mocking for Azure OpenAI
    requests, replacing the need for test helper classes in production code.
    """
    with respx.mock:
        yield respx


@pytest.fixture
def mock_azure_openai_responses(respx_mock):
    """
    Setup mock responses for Azure OpenAI API endpoints.

    This fixture configures realistic Azure OpenAI API responses for:
    - Chat completions (both text and structured output)
    - Authentication headers
    - Error responses
    """
    # Mock the chat completions endpoint
    base_url = "https://test-openai.openai.azure.com/openai/deployments/gpt-4o/chat/completions"

    def create_chat_response(request):
        """Create a dynamic chat response based on request settings."""
        try:
            request_data = json.loads(request.content)

            # Check if structured output is requested
            if "response_format" in request_data and request_data["response_format"]:
                # Structured output response
                mock_response = {
                    "sentiment": "neutral",
                    "confidence": 0.85,
                    "summary": "This is a mock response for testing purposes.",
                    "key_points": ["Mock response", "Testing mode active"],
                }
                content = json.dumps(mock_response)
            else:
                # Text output response
                content = (
                    "This is a mock response from the test Azure service. The integration test is working correctly."
                )

            # Create Azure OpenAI API response format
            response_data = {
                "id": "chatcmpl-test-123",
                "object": "chat.completion",
                "created": 1234567890,
                "model": "gpt-4o",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": content},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 50,
                    "completion_tokens": 20,
                    "total_tokens": 70,
                },
            }

            return Response(200, json=response_data, headers={"content-type": "application/json"})
        except Exception as e:
            # Return error response if something goes wrong
            return Response(
                500,
                json={
                    "error": {
                        "message": f"Mock error: {str(e)}",
                        "type": "internal_error",
                    }
                },
                headers={"content-type": "application/json"},
            )

    # Register the mock route
    respx_mock.post(base_url).mock(side_effect=create_chat_response)

    return respx_mock


@pytest.fixture
def mock_llm_response_structured():
    """Mock LLM response for structured output testing."""
    mock_content = Mock()
    mock_content.content = '{"sentiment":"neutral","confidence":0.85,"summary":"CI/CD automates software integration and deployment processes for improved efficiency."}'
    mock_content.role = "assistant"
    return [mock_content]


@pytest.fixture
def mock_llm_response_text():
    """Mock LLM response for text output testing."""
    mock_content = Mock()
    mock_content.content = "CI/CD stands for Continuous Integration and Continuous Deployment. It's a set of practices that automates the building, testing, and deployment of software, enabling teams to deliver code changes more frequently and reliably."
    mock_content.role = "assistant"
    return [mock_content]


@pytest.fixture
def mock_llm_response_pr_review():
    """Mock LLM response for PR review testing."""
    mock_content = Mock()
    mock_content.content = """## Code Review Summary

**Security Issues Fixed:**
✅ SQL injection vulnerability resolved by using parameterized queries
✅ Input validation added for user_id parameter

**Code Quality:**
- Good use of parameterized queries
- Proper error handling with ValueError for invalid input
- Consistent coding style

**Recommendations:**
- Consider adding logging for security events
- Add unit tests for the new validation logic

**Overall Assessment:** This PR successfully addresses the SQL injection vulnerability and adds appropriate input validation. The changes follow security best practices."""
    mock_content.role = "assistant"
    return [mock_content]


@pytest.fixture
def mock_semantic_kernel_function():
    """
    Mock Semantic Kernel function for integration tests.

    This fixture creates a mock KernelFunctionFromPrompt that behaves like the real one
    but returns predictable test data. Based on actual SK function structure from debugging.
    """

    # Create mock function with realistic metadata structure (matches real SK output)
    mock_function = Mock()

    # Mock the metadata property to match real SK function metadata
    mock_metadata = Mock()
    mock_metadata.name = "SimpleQuestion"
    mock_metadata.plugin_name = None
    mock_metadata.description = "Simple semantic kernel template for asking questions"
    mock_metadata.parameters = [
        Mock(
            name="role",
            description="The role of the assistant (e.g., technical, customer service)",
            default_value="technical",
            type_="",
            is_required=False,
            type_object=None,
            schema_data={
                "type": "object",
                "description": "The role of the assistant (e.g., technical, customer service) (default value: technical)",
            },
            include_in_function_choices=True,
        ),
        Mock(
            name="question",
            description="The question to be answered",
            default_value="",
            type_="",
            is_required=True,
            type_object=None,
            schema_data={"type": "object", "description": "The question to be answered"},
            include_in_function_choices=True,
        ),
    ]
    mock_metadata.is_prompt = True
    mock_metadata.is_asynchronous = True
    mock_function.metadata = mock_metadata

    # Mock prompt_template property (matches real SK structure)
    mock_prompt_template = Mock()
    mock_prompt_template_config = Mock()
    mock_prompt_template_config.name = "SimpleQuestion"
    mock_prompt_template_config.description = "Simple semantic kernel template for asking questions"
    mock_prompt_template_config.template = "You are a helpful {{$role}} assistant. \nPlease answer this question: {{$question}}\n\nProvide a clear and concise response.\n"
    mock_prompt_template_config.template_format = "semantic-kernel"
    mock_prompt_template_config.execution_settings = {
        "azure_openai": {"temperature": 0.7, "max_tokens": 500, "top_p": 1.0}
    }
    mock_prompt_template.prompt_template_config = mock_prompt_template_config
    mock_function.prompt_template = mock_prompt_template

    # Mock execution settings (matches real SK structure)
    mock_function.prompt_execution_settings = {"azure_openai": {"temperature": 0.7, "max_tokens": 500, "top_p": 1.0}}

    return mock_function


@pytest.fixture
def mock_semantic_kernel_result():
    """
    Mock Semantic Kernel FunctionResult for integration tests.

    This fixture creates a mock result that matches the actual structure returned
    by kernel.invoke() based on real debugging output from SK execution.
    """
    from unittest.mock import Mock

    # Create mock result based on actual SK FunctionResult structure
    mock_result = Mock()

    # Mock the function metadata (matches real SK output)
    mock_function_metadata = Mock()
    mock_function_metadata.name = "SimpleQuestion"
    mock_function_metadata.plugin_name = None
    mock_function_metadata.description = "Simple semantic kernel template for asking questions"
    mock_function_metadata.parameters = [
        Mock(
            name="role",
            description="The role of the assistant (e.g., technical, customer service)",
            default_value="technical",
            is_required=False,
        ),
        Mock(
            name="question",
            description="The question to be answered",
            default_value="",
            is_required=True,
        ),
    ]
    mock_result.function = mock_function_metadata

    # Mock the value array with ChatMessageContent (matches real SK ChatMessageContent structure)
    mock_chat_content = Mock()
    mock_chat_content.content = """Certainly!

**Continuous Integration (CI)** is the practice of automatically integrating code changes from multiple developers into a shared repository multiple times a day. It involves automated building and testing to detect issues early.

**Continuous Deployment (CD)** is the practice of automatically deploying every successful code change from the repository to the production environment, ensuring that new features or fixes are available to users quickly and reliably.

**In summary:**
- **CI** focuses on frequent code integration and automated testing.
- **CD** automates the release process, deploying code to production after passing tests.

They often work together as part of a DevOps pipeline to enable rapid, reliable software delivery."""
    mock_chat_content.role = "assistant"

    # Mock the items array within the chat content (TextContent structure from real SK)
    mock_text_content = Mock()
    mock_text_content.text = mock_chat_content.content
    mock_text_content.content_type = "text"
    mock_chat_content.items = [mock_text_content]

    # Mock additional ChatMessageContent properties from real SK output
    mock_chat_content.ai_model_id = "gpt-4.1-nano-stable"
    mock_chat_content.finish_reason = "stop"
    mock_chat_content.encoding = None

    mock_result.value = [mock_chat_content]

    # Mock rendered_prompt property (matches real SK output)
    mock_result.rendered_prompt = "You are a helpful expert DevOps engineer assistant. \nPlease answer this question: What is the difference between continuous integration and continuous deployment?\n\nProvide a clear and concise response.\n"

    # Mock metadata with arguments (matches real SK output structure)
    mock_result.metadata = {
        "arguments": {
            "role": "expert DevOps engineer",
            "question": "What is the difference between continuous integration and continuous deployment?",
        },
        "metadata": [
            {
                "logprobs": None,
                "id": "chatcmpl-BwyARHraYVAjwTiXgQ4CeM5J6b4Ks",
                "created": 1753394007,
                "system_fingerprint": "fp_68472df8fd",
                "usage": {"prompt_tokens": 41, "completion_tokens": 134, "total_tokens": 175},
            }
        ],
        "prompt": "You are a helpful expert DevOps engineer assistant. \nPlease answer this question: What is the difference between continuous integration and continuous deployment?\n\nProvide a clear and concise response.\n",
    }

    return mock_result


@pytest.fixture
def mock_semantic_kernel_structured_result():
    """
    Mock Semantic Kernel FunctionResult for structured output testing.

    This fixture creates a mock result for SK templates that use JSON schema
    for structured output validation. Based on real SK structure.
    """
    from unittest.mock import Mock

    mock_result = Mock()

    # Mock function metadata for structured analysis (matches real SK structure)
    mock_function_metadata = Mock()
    mock_function_metadata.name = "StructuredAnalysis"
    mock_function_metadata.plugin_name = None
    mock_function_metadata.description = "SK template with embedded JSON schema for structured output"
    mock_function_metadata.parameters = [
        Mock(
            name="text_to_analyze",
            description="The text content to analyze",
            default_value="",
            is_required=True,
        )
    ]
    mock_result.function = mock_function_metadata

    # Mock structured JSON response (realistic code review analysis output)
    structured_content = """{
    "analysis_type": "code_review",
    "confidence_score": 0.92,
    "findings": [
        {
            "type": "security",
            "severity": "high",
            "description": "SQL injection vulnerability detected",
            "line": 42,
            "recommendation": "Use parameterized queries"
        },
        {
            "type": "performance",
            "severity": "medium",
            "description": "Inefficient database query",
            "line": 67,
            "recommendation": "Add proper indexing"
        }
    ],
    "summary": "Code review analysis identified 2 issues: 1 high-severity security vulnerability and 1 medium-severity performance concern. Overall code quality is good with proper error handling patterns."
}"""

    # Mock ChatMessageContent structure (matches real SK output)
    mock_chat_content = Mock()
    mock_chat_content.content = structured_content
    mock_chat_content.role = "assistant"
    mock_chat_content.ai_model_id = "gpt-4.1-nano-stable"
    mock_chat_content.finish_reason = "stop"
    mock_chat_content.encoding = None

    # Mock TextContent items (matches real SK structure)
    mock_text_content = Mock()
    mock_text_content.text = structured_content
    mock_text_content.content_type = "text"
    mock_text_content.ai_model_id = None
    mock_text_content.metadata = {}
    mock_text_content.encoding = None
    mock_chat_content.items = [mock_text_content]

    mock_result.value = [mock_chat_content]

    # Mock rendered_prompt (realistic for structured analysis)
    mock_result.rendered_prompt = "Analyze the following text and provide a structured response: The new CI/CD pipeline implementation has significantly improved our deployment frequency..."

    # Mock metadata with arguments (matches real SK metadata structure)
    mock_result.metadata = {
        "arguments": {
            "text_to_analyze": "The new CI/CD pipeline implementation has significantly improved our deployment frequency. Teams are now able to deploy to production multiple times per day instead of weekly releases. However, there are still some concerns about test coverage and monitoring capabilities. The development team is enthusiastic about the changes, but operations teams have expressed some reservations about the increased deployment velocity."
        },
        "metadata": [
            {
                "logprobs": None,
                "id": "chatcmpl-structured-test-123",
                "created": 1753394100,
                "system_fingerprint": "fp_structured_test",
                "usage": {"prompt_tokens": 89, "completion_tokens": 87, "total_tokens": 176},
            }
        ],
        "prompt": "Analyze the following text and provide a structured response: The new CI/CD pipeline implementation has significantly improved our deployment frequency...",
    }

    return mock_result


@pytest.fixture
def integration_mock_azure_service():
    """
    Mock Azure service for integration tests with SK compatibility.

    Creates a mock service that satisfies SK service selection requirements
    and provides realistic SK response structures.
    """
    from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import (
        AzureChatCompletion,
    )
    from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
        AzureChatPromptExecutionSettings
    )
    from unittest.mock import AsyncMock, Mock
    
    # Create a mock that looks like AzureChatCompletion to SK
    mock_service = Mock(spec=AzureChatCompletion)
    
    # Set required SK service properties
    mock_service.service_id = "azure_openai"
    mock_service.ai_model_id = "gpt-4-test"
    mock_service.ai_model_type = Mock()
    
    # Mock the methods SK will call with realistic responses
    mock_service.get_chat_message_contents = AsyncMock()
    mock_service.get_prompt_execution_settings_class = Mock(return_value=AzureChatPromptExecutionSettings)
    
    # Make isinstance checks work for SK service selection
    mock_service.__class__ = AzureChatCompletion
    
    return mock_service


@pytest.fixture
def sk_mock_kernel_invoke():
    """
    Mock kernel.invoke method to return realistic SK FunctionResult objects.
    
    This fixture provides a way to mock kernel.invoke calls with realistic
    SK responses based on template type detection.
    """
    from unittest.mock import AsyncMock
    
    async def mock_invoke(template, arguments):
        """Mock kernel.invoke with realistic responses based on template name."""
        template_name = getattr(template, 'name', 'Unknown')
        
        if template_name == 'SimpleQuestion':
            # Use realistic CI/CD content from your mocks file
            content = 'Certainly! \n\n**Continuous Integration (CI)** is the practice of automatically integrating code changes from multiple developers into a shared repository multiple times a day. It involves automated building and testing to detect issues early.\n\n**Continuous Deployment (CD)** is the practice of automatically deploying every successful code change from the repository to the production environment, ensuring that new features or fixes are available to users quickly and reliably.\n\n**In summary:**\n- **CI** focuses on frequent code integration and automated testing.\n- **CD** automates the release process, deploying code to production after passing tests.\n\nThey often work together as part of a DevOps pipeline to enable rapid, reliable software delivery.'
            return create_simple_sk_mock_response(content, template_name)
        elif template_name == 'StructuredAnalysis':
            # Use realistic structured JSON content from your mocks file
            content = '{"sentiment":"positive","confidence":0.85,"key_themes":["CI/CD pipeline implementation","improved deployment frequency","test coverage concerns","monitoring capabilities","team enthusiasm","deployment velocity reservations"],"summary":"The new CI/CD pipeline has enhanced deployment frequency, enabling multiple daily deployments. While the development team is enthusiastic, concerns remain regarding test coverage, monitoring, and operational reservations about increased deployment speed.","word_count":86}'
            return create_simple_sk_mock_response(content, template_name)
        else:
            # Default simple text response for unknown templates
            content = "This is a default response for testing purposes."
            return create_simple_sk_mock_response(content, template_name)
    
    return AsyncMock(side_effect=mock_invoke)


@pytest.fixture
def mock_openai_service(monkeypatch):
    """
    Mock OpenAI environment variables for integration testing.
    Sets required OpenAI env vars for integration tests.
    """
    monkeypatch.setenv("OPENAI_API_KEY", "non-an-api-key")
    monkeypatch.setenv("OPENAI_CHAT_MODEL_ID", "gpt-4-test")
    # Optionally: monkeypatch.setenv("OPENAI_ORG_ID", "org-test")
    # Optionally: monkeypatch.setenv("OPENAI_BASE_URL", "https://api.openai.com/v1")


@pytest.fixture
def integration_mock_openai_service():
    """
    Mock OpenAI service for integration tests with realistic behavior.
    Mirrors integration_mock_azure_service but for OpenAI.
    """
    mock_service = AsyncMock()
    mock_service.get_chat_message_contents = AsyncMock()
    return mock_service


@pytest.fixture
def example_files_paths():
    """Paths to example files for integration testing."""
    return {
        "simple": Path("examples/simple-example.json"),
        "pr_review": Path("examples/pr-review-example.json"),
        "minimal": Path("examples/minimal-example.json"),
        "structured_output": Path("examples/structured-output-example.json"),
        "code_review_schema": Path("examples/code_review_schema.json"),
    }


@pytest.fixture
def integration_environment_check():
    """Check if integration test environment is properly set up."""
    # For integration tests, we still mock the actual Azure service
    # but test the full pipeline with real file operations and logic
    return {
        "mock_azure": True,
        "real_files": True,
        "real_json_parsing": True,
        "real_schema_validation": True,
    }


@pytest.fixture
def temp_integration_workspace(tmp_path):
    """Create a temporary workspace for integration tests."""
    workspace = tmp_path / "integration_test_workspace"
    workspace.mkdir()

    # Create subdirectories
    (workspace / "input").mkdir()
    (workspace / "output").mkdir()
    (workspace / "schemas").mkdir()

    return workspace
