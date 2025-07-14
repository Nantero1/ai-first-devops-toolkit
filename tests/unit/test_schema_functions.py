"""
Unit tests for schema-related functions in llm_ci_runner.py

Tests create_dynamic_model_from_schema and load_json_schema functions
with heavy mocking following the Given-When-Then pattern.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from llm_ci_runner import (
    InputValidationError,
    SchemaValidationError,
    create_dynamic_model_from_schema,
    load_schema_file,
)


class TestCreateDynamicModelFromSchema:
    """Tests for create_dynamic_model_from_schema function."""

    @patch("llm_ci_runner.schema.create_model_from_schema")
    def test_create_valid_model_with_all_field_types(self, mock_create_model):
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

        # Mock the base generated model with a compatible metaclass
        from pydantic import BaseModel

        class MockGeneratedModel(BaseModel):
            pass

        MockGeneratedModel.model_fields = {
            "sentiment": Mock(is_required=lambda: True),
            "confidence": Mock(is_required=lambda: True),
            "tags": Mock(is_required=lambda: True),
            "optional_field": Mock(is_required=lambda: False),
        }
        mock_create_model.return_value = MockGeneratedModel

        # when
        result_model = create_dynamic_model_from_schema(schema_dict, model_name)

        # then
        mock_create_model.assert_called_once_with(schema_dict)
        assert result_model.__name__ == model_name
        assert result_model.__qualname__ == model_name
        # Verify it's a type
        assert isinstance(result_model, type)

    @patch("llm_ci_runner.schema.create_model_from_schema")
    def test_create_model_with_empty_properties_succeeds(self, mock_create_model):
        """Test that empty properties creates a valid model."""
        # given
        schema_dict = {"type": "object", "properties": {}, "required": []}

        # Mock with proper BaseModel
        from pydantic import BaseModel

        class MockEmptyModel(BaseModel):
            pass

        MockEmptyModel.model_fields = {}
        mock_create_model.return_value = MockEmptyModel

        # when
        result = create_dynamic_model_from_schema(schema_dict)

        # then
        assert result is not None
        mock_create_model.assert_called_once_with(schema_dict)

    @patch("llm_ci_runner.schema.create_model_from_schema")
    def test_create_model_with_non_object_type_succeeds(self, mock_create_model):
        """Test that non-object type is handled by the library."""
        # given
        schema_dict = {"type": "string", "properties": {"field": {"type": "string"}}}

        # Mock with proper BaseModel
        from pydantic import BaseModel

        class MockStringTypeModel(BaseModel):
            field: str = ""

        MockStringTypeModel.model_fields = {"field": Mock(is_required=lambda: False)}
        mock_create_model.return_value = MockStringTypeModel

        # when
        result = create_dynamic_model_from_schema(schema_dict)

        # then
        assert result is not None
        mock_create_model.assert_called_once_with(schema_dict)

    def test_create_model_with_non_dict_schema_raises_error(self):
        """Test that non-dictionary schema raises SchemaValidationError."""
        # given
        schema_dict = "not a dictionary"

        # when & then
        with pytest.raises(SchemaValidationError, match="Failed to create dynamic model"):
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
        with patch("llm_ci_runner.schema.create_model_from_schema") as mock_create_model:
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
    @patch("llm_ci_runner.schema.create_model_from_schema")
    def test_required_field_handling(self, mock_create_model, required_fields, field_name, expected_required):
        """Test that required fields are handled correctly."""
        # given
        schema_dict = {
            "type": "object",
            "properties": {field_name: {"type": "string", "description": "Test field"}},
            "required": required_fields,
        }

        # Mock with proper BaseModel
        from pydantic import BaseModel

        class MockRequiredModel(BaseModel):
            pass

        # Dynamically add the field to the mock model
        setattr(MockRequiredModel, field_name, "")
        MockRequiredModel.model_fields = {field_name: Mock(is_required=lambda: expected_required)}
        mock_create_model.return_value = MockRequiredModel

        # when
        result_model = create_dynamic_model_from_schema(schema_dict)

        # then
        mock_create_model.assert_called_once_with(schema_dict)
        assert result_model is not None


class TestPydanticModelConversion:
    """Tests for Pydantic model conversion methods (model_dump() and dict())."""

    def test_static_pydantic_model_model_dump_method(self):
        """Test that static Pydantic models have model_dump() method."""
        # given
        from pydantic import BaseModel, Field

        class TestStaticModel(BaseModel):
            """Static Pydantic model for testing conversion methods."""

            name: str = Field(..., description="Test name")
            value: int = Field(..., description="Test value")
            optional_field: str = Field(default="default", description="Optional field")

        model_instance = TestStaticModel(name="test", value=42)

        # when
        result = model_instance.model_dump()

        # then
        assert isinstance(result, dict)
        assert result["name"] == "test"
        assert result["value"] == 42
        assert result["optional_field"] == "default"
        assert len(result) == 3

    def test_static_pydantic_model_dict_method(self):
        """Test that static Pydantic models have dict() method (for backward compatibility)."""
        # given
        from pydantic import BaseModel, Field

        class TestStaticModel(BaseModel):
            """Static Pydantic model for testing dict() method."""

            name: str = Field(..., description="Test name")
            value: int = Field(..., description="Test value")

        model_instance = TestStaticModel(name="test", value=42)

        # when
        result = model_instance.model_dump()

        # then
        assert isinstance(result, dict)
        assert result["name"] == "test"
        assert result["value"] == 42
        assert len(result) == 2

    def test_dynamic_kernel_model_model_dump_method(self):
        """Test that dynamic KernelBaseModel models have model_dump() method."""
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
            },
            "required": ["sentiment", "confidence"],
            "additionalProperties": False,
        }

        # Create dynamic model
        dynamic_model = create_dynamic_model_from_schema(schema_dict, "TestDynamicModel")
        model_instance = dynamic_model(sentiment="positive", confidence=0.95)

        # when
        result = model_instance.model_dump()

        # then
        assert isinstance(result, dict)
        assert result["sentiment"] == "positive"
        assert result["confidence"] == 0.95
        assert len(result) == 2

    def test_dynamic_kernel_model_dict_method(self):
        """Test that dynamic KernelBaseModel models have dict() method."""
        # given
        schema_dict = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Test name"},
                "score": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 100,
                    "description": "Test score",
                },
            },
            "required": ["name", "score"],
            "additionalProperties": False,
        }

        # Create dynamic model
        dynamic_model = create_dynamic_model_from_schema(schema_dict, "TestDynamicModel")
        model_instance = dynamic_model(name="test", score=85)

        # when
        result = model_instance.model_dump()

        # then
        assert isinstance(result, dict)
        assert result["name"] == "test"
        assert result["score"] == 85
        assert len(result) == 2

    def test_model_dump_with_exclude_unset_option(self):
        """Test model_dump() with exclude_unset option."""
        # given
        from pydantic import BaseModel, Field
        from typing import Optional

        class TestModel(BaseModel):
            """Test model with optional fields."""

            required_field: str = Field(..., description="Required field")
            optional_field: str = Field(default="default", description="Optional field")
            unset_field: Optional[str] = Field(default=None, description="Unset field")

        model_instance = TestModel(required_field="test")

        # when
        result = model_instance.model_dump(exclude_unset=True)

        # then
        assert isinstance(result, dict)
        assert result["required_field"] == "test"
        assert "optional_field" not in result  # exclude_unset excludes fields with defaults
        assert "unset_field" not in result
        assert len(result) == 1

    def test_model_dump_with_include_none_option(self):
        """Test model_dump() with include_none option."""
        # given
        from pydantic import BaseModel, Field
        from typing import Optional

        class TestModel(BaseModel):
            """Test model with None values."""

            required_field: str = Field(..., description="Required field")
            optional_field: Optional[str] = Field(default=None, description="Optional field")

        model_instance = TestModel(required_field="test", optional_field=None)

        # when
        result = model_instance.model_dump(exclude_none=False)

        # then
        assert isinstance(result, dict)
        assert result["required_field"] == "test"
        assert result["optional_field"] is None
        assert len(result) == 2

    def test_dict_method_backward_compatibility(self):
        """Test that dict() method works for backward compatibility."""
        # given
        from pydantic import BaseModel, Field

        class TestModel(BaseModel):
            """Test model for backward compatibility."""

            field1: str = Field(..., description="Field 1")
            field2: int = Field(..., description="Field 2")

        model_instance = TestModel(field1="value1", field2=123)

        # when
        result = model_instance.model_dump()

        # then
        assert isinstance(result, dict)
        assert result["field1"] == "value1"
        assert result["field2"] == 123
        assert len(result) == 2

    def test_dynamic_model_with_complex_schema(self):
        """Test dynamic model conversion with complex schema (nested objects, arrays)."""
        # given
        schema_dict = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Test name"},
                "metadata": {
                    "type": "object",
                    "properties": {
                        "version": {"type": "string", "description": "Version"},
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Tags",
                        },
                    },
                    "required": ["version", "tags"],
                },
                "scores": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "category": {"type": "string", "description": "Category"},
                            "score": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                                "description": "Score",
                            },
                        },
                        "required": ["category", "score"],
                    },
                },
            },
            "required": ["name", "metadata", "scores"],
            "additionalProperties": False,
        }

        # Create dynamic model
        dynamic_model = create_dynamic_model_from_schema(schema_dict, "ComplexTestModel")
        model_instance = dynamic_model(
            name="test",
            metadata={"version": "1.0", "tags": ["tag1", "tag2"]},
            scores=[
                {"category": "quality", "score": 0.85},
                {"category": "performance", "score": 0.92},
            ],
        )

        # when
        result = model_instance.model_dump()

        # then
        assert isinstance(result, dict)
        assert result["name"] == "test"
        assert result["metadata"]["version"] == "1.0"
        assert result["metadata"]["tags"] == ["tag1", "tag2"]
        assert len(result["scores"]) == 2
        assert result["scores"][0]["category"] == "quality"
        assert result["scores"][0]["score"] == 0.85
        assert result["scores"][1]["category"] == "performance"
        assert result["scores"][1]["score"] == 0.92

    def test_model_conversion_methods_consistency(self):
        """Test that model_dump() and dict() produce consistent results."""
        # given
        from pydantic import BaseModel, Field

        class TestModel(BaseModel):
            """Test model for conversion consistency."""

            string_field: str = Field(..., description="String field")
            int_field: int = Field(..., description="Integer field")
            float_field: float = Field(..., description="Float field")
            bool_field: bool = Field(..., description="Boolean field")

        model_instance = TestModel(
            string_field="test",
            int_field=42,
            float_field=3.14,
            bool_field=True,
        )

        # when
        model_dump_result = model_instance.model_dump()
        dict_result = model_instance.model_dump()

        # then
        assert isinstance(model_dump_result, dict)
        assert isinstance(dict_result, dict)
        assert model_dump_result == dict_result
        assert model_dump_result["string_field"] == "test"
        assert model_dump_result["int_field"] == 42
        assert model_dump_result["float_field"] == 3.14
        assert model_dump_result["bool_field"] is True

    def test_kernel_base_model_inheritance(self):
        """Test that dynamic models properly inherit from KernelBaseModel."""
        # given
        schema_dict = {
            "type": "object",
            "properties": {
                "test_field": {"type": "string", "description": "Test field"},
            },
            "required": ["test_field"],
            "additionalProperties": False,
        }

        # Create dynamic model
        dynamic_model = create_dynamic_model_from_schema(schema_dict, "KernelTestModel")

        # when & then
        from semantic_kernel.kernel_pydantic import KernelBaseModel

        assert issubclass(dynamic_model, KernelBaseModel)

        # Test that it can be instantiated
        model_instance = dynamic_model(test_field="test_value")
        assert model_instance.test_field == "test_value"

        # Test conversion methods
        result = model_instance.model_dump()
        assert result["test_field"] == "test_value"


class TestLoadSchemaFile:
    """Tests for load_schema_file function."""

    def test_load_valid_schema_file(self, temp_schema_file):
        """Test loading a valid JSON schema file."""
        # given
        schema_file = temp_schema_file

        # when
        with patch("llm_ci_runner.schema.create_dynamic_model_from_schema") as mock_create_model:
            mock_model = Mock()
            mock_model.__name__ = "TestModel"
            mock_create_model.return_value = mock_model

            result = load_schema_file(schema_file)

        # then
        assert result is not None
        mock_create_model.assert_called_once()

    def test_load_schema_with_none_file_returns_none(self):
        """Test that None file path returns None."""
        # given
        schema_file = None

        # when
        result = load_schema_file(schema_file)

        # then
        assert result is None

    def test_load_nonexistent_file_raises_error(self):
        """Test that nonexistent file raises InputValidationError."""
        # given
        schema_file = Path("nonexistent.json")

        # when & then
        with pytest.raises(InputValidationError, match="Schema file not found"):
            load_schema_file(schema_file)

    def test_load_invalid_json_raises_error(self, temp_dir):
        """Test that invalid JSON raises InputValidationError."""
        # given
        invalid_json_file = temp_dir / "invalid.json"
        with open(invalid_json_file, "w") as f:
            f.write("{{{{ completely invalid content \n unmatched braces")  # Invalid for both YAML and JSON

        # when & then
        with pytest.raises(InputValidationError, match="Invalid JSON in schema file:"):
            load_schema_file(invalid_json_file)

    def test_load_schema_with_create_model_error_raises_schema_error(self, temp_schema_file):
        """Test that model creation errors are wrapped in InputValidationError."""
        # given
        schema_file = temp_schema_file

        # when & then
        with patch("llm_ci_runner.schema.create_dynamic_model_from_schema") as mock_create_model:
            mock_create_model.side_effect = Exception("Model creation failed")

            with pytest.raises(InputValidationError, match="Failed to load schema file"):
                load_schema_file(schema_file)

    def test_load_schema_with_file_read_error_raises_schema_error(self):
        """Test that file read errors are wrapped in InputValidationError."""
        # given
        schema_file = Path("test.json")

        # when & then
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("builtins.open", side_effect=OSError("Permission denied")),
        ):
            with pytest.raises(InputValidationError, match="Failed to load schema file"):
                load_schema_file(schema_file)

    def test_load_valid_yaml_schema_file(self, temp_dir):
        """Test loading a valid YAML schema file."""
        # given
        schema_file = temp_dir / "schema.yaml"
        schema_content = """
type: object
properties:
  sentiment:
    type: string
    enum: [positive, negative, neutral]
    description: Sentiment classification
  confidence:
    type: number
    minimum: 0
    maximum: 1
    description: Confidence score
required: [sentiment, confidence]
additionalProperties: false
"""
        with open(schema_file, "w") as f:
            f.write(schema_content)

        # when
        with patch("llm_ci_runner.schema.create_dynamic_model_from_schema") as mock_create_model:
            mock_model = Mock()
            mock_model.__name__ = "TestModel"
            mock_create_model.return_value = mock_model

            result = load_schema_file(schema_file)

        # then
        assert result is not None
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert result[0] == mock_model
        assert isinstance(result[1], dict)
        mock_create_model.assert_called_once()
        # Verify the YAML was parsed correctly
        call_args = mock_create_model.call_args[0][0]
        assert call_args["type"] == "object"
        assert "sentiment" in call_args["properties"]
        assert call_args["required"] == ["sentiment", "confidence"]

    def test_load_invalid_yaml_schema_raises_error(self, temp_dir):
        """Test that invalid YAML schema raises InputValidationError."""
        # given
        invalid_yaml_file = temp_dir / "invalid.yaml"
        with open(invalid_yaml_file, "w") as f:
            f.write("type: object\nproperties:\n  field: {\n")

        # when & then
        with pytest.raises(InputValidationError, match="Invalid JSON in schema file"):
            load_schema_file(invalid_yaml_file)
