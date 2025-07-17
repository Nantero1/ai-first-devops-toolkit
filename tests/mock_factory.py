"""
Mock Factory for LLM Runner Tests

This module provides factory functions to create realistic mock objects
based on actual Semantic Kernel and Azure OpenAI API responses.

The mock data is based on actual API responses captured during testing.
"""

from typing import Any
from unittest.mock import Mock

from semantic_kernel.contents import ChatMessageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole


def create_mock_chat_message_content(
    content: str,
    role: str = "assistant",
    ai_model_id: str = "gpt-4.1-nano",
    metadata: dict[str, Any] | None = None,
) -> Mock:
    """
    Create a realistic mock ChatMessageContent object.

    Based on actual Semantic Kernel ChatMessageContent structure
    captured from real API responses.
    """
    mock_content = Mock(spec=ChatMessageContent)

    # Basic properties
    mock_content.content = content
    mock_content.role = AuthorRole(role)
    mock_content.ai_model_id = ai_model_id
    mock_content.content_type = "message"
    mock_content.name = None
    mock_content.encoding = None
    mock_content.finish_reason = "stop"
    mock_content.status = None

    # Metadata with realistic structure
    default_metadata = {
        "logprobs": None,
        "id": "chatcmpl-mock-test-id",
        "created": 1751837268,
        "system_fingerprint": "fp_mock_test",
        "usage": {"prompt_tokens": 37, "completion_tokens": 88},
    }
    mock_content.metadata = metadata or default_metadata

    # Items array with TextContent
    mock_text_content = Mock(spec=TextContent)
    mock_text_content.inner_content = None
    mock_text_content.ai_model_id = None
    mock_text_content.metadata = {}
    mock_text_content.content_type = "text"
    mock_text_content.text = content
    mock_text_content.encoding = None

    mock_content.items = [mock_text_content]

    # Inner content (Azure OpenAI ChatCompletion structure)
    mock_inner_content = Mock()
    mock_inner_content.id = "chatcmpl-mock-test-id"
    mock_inner_content.choices = [Mock()]
    mock_inner_content.choices[0].finish_reason = "stop"
    mock_inner_content.choices[0].index = 0
    mock_inner_content.choices[0].logprobs = None
    mock_inner_content.choices[0].message = Mock()
    mock_inner_content.choices[0].message.content = content
    mock_inner_content.choices[0].message.refusal = None
    mock_inner_content.choices[0].message.role = "assistant"
    mock_inner_content.choices[0].message.annotations = []
    mock_inner_content.choices[0].message.audio = None
    mock_inner_content.choices[0].message.function_call = None
    mock_inner_content.choices[0].message.tool_calls = None

    mock_content.inner_content = mock_inner_content

    return mock_content


def create_structured_output_mock() -> list[Mock]:
    """
    Create mock for structured output response based on actual API response.

    Based on actual response from simple-example.json with structured-output-example.json schema.
    """
    structured_response = '{"sentiment":"neutral","confidence":0.95,"key_points":["Continuous Integration (CI): automated testing and merging of code changes","Continuous Deployment (CD): automated deployment of code to production","Improves software delivery speed and quality","Reduces manual errors","Facilitates frequent releases"],"summary":"CI/CD in software development refers to practices of automatically integrating, testing, and deploying code to improve delivery speed and quality."}'

    mock_content = create_mock_chat_message_content(
        content=structured_response,
        metadata={
            "logprobs": None,
            "id": "chatcmpl-BqRBksh5sLpOVS8UPc92ahyllKqbU",
            "created": 1751837268,
            "system_fingerprint": "fp_68472df8fd",
            "usage": {"prompt_tokens": 187, "completion_tokens": 88},
        },
    )

    return [mock_content]


def create_text_output_mock() -> list[Mock]:
    """
    Create mock for text output response based on actual API response.

    Based on actual response from simple-example.json without schema.
    """
    text_response = "CI/CD stands for Continuous Integration and Continuous Deployment (or Continuous Delivery), and it are key practices in modern software development aimed at automating the process of integrating code changes and deploying applications. Continuous Integration involves frequently merging developers' code changes into a shared repository, where automated tests are run to ensure code quality and prevent integration issues. Continuous Deployment or Delivery automates the release process, enabling rapid, reliable deployment of applications to production or staging environments. Together, CI/CD improves development efficiency, reduces bugs, and accelerates the delivery of new features to users."

    mock_content = create_mock_chat_message_content(
        content=text_response,
        metadata={
            "logprobs": None,
            "id": "chatcmpl-BqRC3UPdOdbGvnck6k7dP3cczYKTC",
            "created": 1751837287,
            "system_fingerprint": "fp_68472df8fd",
            "usage": {"prompt_tokens": 37, "completion_tokens": 111},
        },
    )

    return [mock_content]


def create_pr_review_mock() -> list[Mock]:
    """
    Create mock for PR review response based on expected realistic output.
    """
    pr_review_response = """## Code Review Summary

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

    mock_content = create_mock_chat_message_content(
        content=pr_review_response,
        metadata={
            "logprobs": None,
            "id": "chatcmpl-mock-pr-review-id",
            "created": 1751837300,
            "system_fingerprint": "fp_mock_test",
            "usage": {"prompt_tokens": 245, "completion_tokens": 156},
        },
    )

    return [mock_content]


def create_minimal_response_mock() -> list[Mock]:
    """
    Create mock for minimal response based on minimal-example.json.
    """
    minimal_response = "Hello! I'm ready to help you with any questions or tasks you have."

    mock_content = create_mock_chat_message_content(
        content=minimal_response,
        metadata={
            "logprobs": None,
            "id": "chatcmpl-mock-minimal-id",
            "created": 1751837320,
            "system_fingerprint": "fp_mock_test",
            "usage": {"prompt_tokens": 15, "completion_tokens": 19},
        },
    )

    return [mock_content]


def create_error_response_mock(
    error_message: str = "Service temporarily unavailable",
) -> Exception:
    """
    Create mock exception for testing error handling.
    """
    from azure.core.exceptions import ClientAuthenticationError

    return ClientAuthenticationError(error_message)


def create_jinja2_template_mock() -> list[Mock]:
    """
    Create mock for Jinja2 template response based on the jinja2-example/schema.yaml.
    """
    jinja2_response = '{"summary": "Implements rate limiting and improves error handling.", "code_quality_score": 9, "security_assessment": {"vulnerabilities_found": ["None detected"], "risk_level": "low", "recommendations": ["Continue using parameterized queries", "Add more input validation"]}, "performance_analysis": {"impact": "positive", "concerns": ["None"], "optimizations": ["Consider caching frequent queries"]}, "testing_recommendations": {"test_coverage": "adequate", "missing_tests": ["Edge case for max_limit"], "test_scenarios": ["Test rate limit exceeded", "Test invalid credentials"]}, "suggestions": ["Improve documentation", "Add logging for rate limit events"], "overall_rating": "approve_with_suggestions"}'
    return [create_mock_chat_message_content(content=jinja2_response)]


def create_hbs_template_mock() -> list[Mock]:
    """
    Create mock for Handlebars template response based on the pr-review-template/schema.yaml.
    """
    hbs_response = '{"description": "This PR addresses SQL injection vulnerabilities and improves input validation. Session management is now more secure and error handling is robust.", "summary": "Fixes security issues and improves session management.", "change_type": "security", "impact": "high", "security_findings": [{"type": "vulnerability_fixed", "description": "SQL injection vulnerability resolved by using parameterized queries.", "severity": "high"}, {"type": "security_improvement", "description": "Input validation added for user_id.", "severity": "medium"}], "testing_notes": ["Add tests for invalid credentials", "Test session creation with invalid user_id"], "deployment_notes": ["No downtime expected", "Monitor authentication logs post-deployment"], "breaking_changes": [], "related_issues": [456, 789]}'
    return [create_mock_chat_message_content(content=hbs_response)]


# Mock response mapping for easy test fixture creation
MOCK_RESPONSES = {
    "structured_output": create_structured_output_mock,
    "text_output": create_text_output_mock,
    "pr_review": create_pr_review_mock,
    "minimal": create_minimal_response_mock,
    "error": create_error_response_mock,
    "jinja2_template": create_jinja2_template_mock,
    "hbs_template": create_hbs_template_mock,
}
