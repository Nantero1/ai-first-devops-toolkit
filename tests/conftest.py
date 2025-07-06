"""
Shared test fixtures and configuration for LLM Runner tests.

This file provides common fixtures and test utilities used across
unit and integration tests.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_input_messages():
    """Sample input messages for testing."""
    return [
        {"role": "system", "content": "You are a helpful assistant."},
        {
            "role": "user",
            "content": "Explain CI/CD in one paragraph.",
            "name": "developer",
        },
    ]


@pytest.fixture
def sample_input_data(sample_input_messages):
    """Sample input data structure for testing."""
    return {
        "messages": sample_input_messages,
        "context": {
            "session_id": "test-session-001",
            "metadata": {"task_type": "explanation", "domain": "software_development"},
        },
    }


@pytest.fixture
def sample_json_schema():
    """Sample JSON schema for structured output testing."""
    return {
        "type": "object",
        "properties": {
            "sentiment": {
                "type": "string",
                "enum": ["positive", "negative", "neutral"],
                "description": "Overall sentiment of the content",
            },
            "confidence": {
                "type": "number",
                "minimum": 0,
                "maximum": 1,
                "description": "Confidence score (0-1)",
            },
            "summary": {
                "type": "string",
                "maxLength": 200,
                "description": "Brief summary (max 200 chars)",
            },
        },
        "required": ["sentiment", "confidence", "summary"],
        "additionalProperties": False,
    }


@pytest.fixture
def sample_structured_response():
    """Sample structured response that matches the schema."""
    return {
        "sentiment": "neutral",
        "confidence": 0.85,
        "summary": "CI/CD automates software integration and deployment processes.",
    }


@pytest.fixture
def temp_input_file(temp_dir, sample_input_data):
    """Create a temporary input JSON file."""
    input_file = temp_dir / "input.json"
    with open(input_file, "w") as f:
        json.dump(sample_input_data, f, indent=2)
    return input_file


@pytest.fixture
def temp_schema_file(temp_dir, sample_json_schema):
    """Create a temporary schema JSON file."""
    schema_file = temp_dir / "schema.json"
    with open(schema_file, "w") as f:
        json.dump(sample_json_schema, f, indent=2)
    return schema_file


@pytest.fixture
def temp_output_file(temp_dir):
    """Create a temporary output file path."""
    return temp_dir / "output.json"


@pytest.fixture
def mock_azure_service():
    """Mock Azure OpenAI service for testing."""
    mock_service = AsyncMock()
    mock_service.get_chat_message_contents = AsyncMock()
    return mock_service


@pytest.fixture
def mock_chat_message_content():
    """Mock ChatMessageContent for testing."""
    mock_content = Mock()
    mock_content.content = '{"sentiment":"neutral","confidence":0.85,"summary":"Test response"}'
    mock_content.role = "assistant"
    return mock_content


# Test markers
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.slow = pytest.mark.slow
