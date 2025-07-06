"""
Unit tests for schema-related functions in llm_runner.py

Tests create_dynamic_model_from_schema and load_json_schema functions
with heavy mocking following the Given-When-Then pattern.
"""

import pytest
import json
from unittest.mock import Mock, patch, mock_open
from pathlib import Path

import llm_runner
from llm_runner import (
    create_dynamic_model_from_schema,
    load_json_schema,
    SchemaValidationError,
)


class TestCreateDynamicModelFromSchema:
    """Tests for create_dynamic_model_from_schema function."""

    def test_create_valid_model_with_all_field_types(self):
        """Test creating a dynamic model with various field types."""
        # given
        schema_dict = {
            "type": "object",
            "properties": {
                "sentiment": {
                    "type": "string",
                    "enum": ["positive", "negative", "neutral"],
                    "description": "Sentiment classification",
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "description": "Confidence score",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of tags",
                },
                "optional_field": {"type": "string", "description": "Optional field"},
            },
            "required": ["sentiment", "confidence", "tags"],
            "additionalProperties": False,
        }
        model_name = "TestModel"

        # when
        with patch("llm_runner.create_model_from_schema") as mock_create_model:
            # Mock the base generated model
            mock_base_model = Mock()
            mock_base_model.model_fields = {
                "sentiment": Mock(is_required=lambda: True),
                "confidence": Mock(is_required=lambda: True),
                "tags": Mock(is_required=lambda: True),
                "optional_field": Mock(is_required=lambda: False),
            }
            mock_create_model.return_value = mock_base_model

            result_model = create_dynamic_model_from_schema(schema_dict, model_name)

        # then
        mock_create_model.assert_called_once_with(schema_dict)
        assert result_model.__name__ == model_name
        assert result_model.__qualname__ == model_name
        # Verify it's a subclass of KernelBaseModel
        assert hasattr(result_model, "__bases__")

    def test_create_model_with_empty_properties_raises_error(self):
        """Test that empty properties raises SchemaValidationError."""
        # given
        schema_dict = {"type": "object", "properties": {}, "required": []}

        # when & then
        with pytest.raises(
            SchemaValidationError, match="Schema must have 'properties'"
        ):
            create_dynamic_model_from_schema(schema_dict)

    def test_create_model_with_invalid_type_raises_error(self):
        """Test that non-object type raises SchemaValidationError."""
        # given
        schema_dict = {"type": "string", "properties": {"field": {"type": "string"}}}

        # when & then
        with pytest.raises(
            SchemaValidationError, match="Schema must be of type 'object'"
        ):
            create_dynamic_model_from_schema(schema_dict)

    def test_create_model_with_non_dict_schema_raises_error(self):
        """Test that non-dictionary schema raises SchemaValidationError."""
        # given
        schema_dict = "not a dictionary"

        # when & then
        with pytest.raises(SchemaValidationError, match="Schema must be a dictionary"):
            create_dynamic_model_from_schema(schema_dict)

    def test_create_model_with_library_exception_raises_schema_error(self):
        """Test that library exceptions are wrapped in SchemaValidationError."""
        # given
        schema_dict = {
            "type": "object",
            "properties": {"field": {"type": "string"}},
            "required": ["field"],
        }

        # when & then
        with patch("llm_runner.create_model_from_schema") as mock_create_model:
            mock_create_model.side_effect = Exception("Library error")

            with pytest.raises(
                SchemaValidationError,
                match="Failed to create dynamic model: Library error",
            ):
                create_dynamic_model_from_schema(schema_dict)

    @pytest.mark.parametrize(
        "required_fields, field_name, expected_required",
        [
            (["field1", "field2"], "field1", True),
            (["field1", "field2"], "field3", False),
            ([], "field1", False),
        ],
    )
    def test_required_field_handling(
        self, required_fields, field_name, expected_required
    ):
        """Test that required fields are handled correctly."""
        # given
        schema_dict = {
            "type": "object",
            "properties": {field_name: {"type": "string", "description": "Test field"}},
            "required": required_fields,
        }

        # when
        with patch("llm_runner.create_model_from_schema") as mock_create_model:
            mock_base_model = Mock()
            mock_base_model.model_fields = {
                field_name: Mock(is_required=lambda: expected_required)
            }
            mock_create_model.return_value = mock_base_model

            result_model = create_dynamic_model_from_schema(schema_dict)

        # then
        mock_create_model.assert_called_once_with(schema_dict)
        assert result_model is not None


class TestLoadJsonSchema:
    """Tests for load_json_schema function."""

    def test_load_valid_schema_file(self, temp_schema_file):
        """Test loading a valid JSON schema file."""
        # given
        schema_file = temp_schema_file

        # when
        with patch("llm_runner.create_dynamic_model_from_schema") as mock_create_model:
            mock_model = Mock()
            mock_model.__name__ = "TestModel"
            mock_create_model.return_value = mock_model

            result = load_json_schema(schema_file)

        # then
        assert result is not None
        mock_create_model.assert_called_once()

    def test_load_schema_with_none_file_returns_none(self):
        """Test that None file path returns None."""
        # given
        schema_file = None

        # when
        result = load_json_schema(schema_file)

        # then
        assert result is None

    def test_load_nonexistent_file_raises_error(self):
        """Test that nonexistent file raises SchemaValidationError."""
        # given
        schema_file = Path("nonexistent.json")

        # when & then
        with pytest.raises(SchemaValidationError, match="Schema file not found"):
            load_json_schema(schema_file)

    def test_load_invalid_json_raises_error(self, temp_dir):
        """Test that invalid JSON raises SchemaValidationError."""
        # given
        invalid_json_file = temp_dir / "invalid.json"
        with open(invalid_json_file, "w") as f:
            f.write("{ invalid json }")

        # when & then
        with pytest.raises(SchemaValidationError, match="Invalid JSON in schema file"):
            load_json_schema(invalid_json_file)

    def test_load_schema_with_create_model_error_raises_schema_error(
        self, temp_schema_file
    ):
        """Test that model creation errors are wrapped in SchemaValidationError."""
        # given
        schema_file = temp_schema_file

        # when & then
        with patch("llm_runner.create_dynamic_model_from_schema") as mock_create_model:
            mock_create_model.side_effect = Exception("Model creation failed")

            with pytest.raises(
                SchemaValidationError, match="Error creating dynamic model"
            ):
                load_json_schema(schema_file)

    def test_load_schema_with_file_read_error_raises_schema_error(self):
        """Test that file read errors are wrapped in SchemaValidationError."""
        # given
        schema_file = Path("test.json")

        # when & then
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("builtins.open", side_effect=IOError("Permission denied")),
        ):

            with pytest.raises(
                SchemaValidationError, match="Error reading schema file"
            ):
                load_json_schema(schema_file)
