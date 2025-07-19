"""
Unit tests for schema-related functions in llm_ci_runner.py

Tests create_dynamic_model_from_schema and load_json_schema functions
with heavy mocking following the Given-When-Then pattern.
"""

from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import Field
from semantic_kernel.kernel_pydantic import KernelBaseModel

from llm_ci_runner import (
    InputValidationError,
    SchemaValidationError,
    create_dynamic_model_from_schema,
    generate_one_shot_example,
    load_schema_file,
)


class TestCreateDynamicModelFromSchema:
    """Tests for create_dynamic_model_from_schema function."""

    def test_create_valid_model_with_all_field_types(self):
        """Test creating a dynamic model with various field types."""
        # given
        schema_dict = {
            "type": "object",
            "title": "TestModel",
            "description": "Test model for testing",
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

        # when
        result_model = create_dynamic_model_from_schema(schema_dict)

        # then
        assert result_model is not None
        assert hasattr(result_model, "model_fields")
        field_names = list(result_model.model_fields.keys())
        assert "sentiment" in field_names
        assert "confidence" in field_names
        assert "tags" in field_names
        assert "optional_field" in field_names

    def test_create_model_with_invalid_schema_raises_error(self):
        """Test creating a model with invalid schema raises SchemaValidationError."""
        # given
        invalid_schema = "not a dict"  # Non-dict input causes 'str' has no attribute 'get' error

        # when/then
        with pytest.raises(SchemaValidationError):
            create_dynamic_model_from_schema(invalid_schema)

    def test_create_model_with_non_dict_schema_raises_error(self):
        """Test creating a model with non-dict schema raises SchemaValidationError."""
        # given
        invalid_schema = "not a dict"

        # when/then
        with pytest.raises(SchemaValidationError):
            create_dynamic_model_from_schema(invalid_schema)


class TestLoadSchemaFile:
    """Tests for load_schema_file function."""

    def test_load_valid_json_schema_file(self, tmp_path):
        """Test loading a valid JSON schema file."""
        # given
        schema_dict = {
            "type": "object",
            "title": "TestSchema",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        schema_file = tmp_path / "test_schema.json"
        schema_file.write_text(
            '{"type": "object", "title": "TestSchema", "properties": {"name": {"type": "string"}}, "required": ["name"]}'
        )

        # when
        result = load_schema_file(schema_file)

        # then
        assert result is not None
        model_class, original_schema = result
        assert model_class is not None
        assert isinstance(original_schema, dict)
        assert original_schema["type"] == "object"

    def test_load_valid_yaml_schema_file(self, tmp_path):
        """Test loading a valid YAML schema file."""
        # given
        yaml_content = """
type: object
name: TestSchema
properties:
  name:
    type: string
required:
  - name
"""
        schema_file = tmp_path / "test_schema.yaml"
        schema_file.write_text(yaml_content)

        # when
        result = load_schema_file(schema_file)

        # then
        assert result is not None
        model_class, original_schema = result
        assert model_class is not None
        assert isinstance(original_schema, dict)
        assert original_schema["type"] == "object"

    def test_load_nonexistent_schema_file_raises_error(self):
        """Test loading nonexistent schema file raises InputValidationError."""
        # given
        nonexistent_file = Path("does_not_exist.json")

        # when/then
        with pytest.raises(InputValidationError, match="Schema file not found"):
            load_schema_file(nonexistent_file)

    def test_load_none_schema_file_returns_none(self):
        """Test loading None schema file returns None."""
        # given
        schema_file = None

        # when
        result = load_schema_file(schema_file)

        # then
        assert result is None

    def test_load_invalid_json_schema_file_raises_error(self, tmp_path):
        """Test loading invalid JSON schema file raises InputValidationError."""
        # given
        schema_file = tmp_path / "invalid_schema.json"
        schema_file.write_text("{ [ }")  # Invalid syntax for both JSON and YAML

        # when/then
        with pytest.raises(InputValidationError, match="Invalid JSON"):
            load_schema_file(schema_file)


class TestGenerateOneShotExample:
    """Tests for generate_one_shot_example function."""

    def test_generate_example_with_field_examples(self):
        """Test generating example that uses Field examples as highest priority."""

        # given
        class TestModel(KernelBaseModel):
            name: str = Field(
                default="default_name",
                examples=["example_name", "another_name"],
            )
            age: int = Field(default=25, examples=[30, 35])
            status: str = "active"  # structural only

        # when
        result = generate_one_shot_example(TestModel)

        # then
        assert result["name"] == "example_name"  # Uses first example, not default
        assert result["age"] == 30  # Uses first example, not default
        assert result["status"] == "active"  # Uses default value

    def test_generate_example_with_defaults_only(self):
        """Test generating example that uses default values when no examples provided."""

        # given
        class TestModel(KernelBaseModel):
            name: str = Field(default="default_name")
            age: int = Field(default=25)
            active: bool = Field(default=True)

        # when
        result = generate_one_shot_example(TestModel)

        # then
        assert result["name"] == "default_name"  # Uses default
        assert result["age"] == 25  # Uses default
        assert result["active"] is True  # Structural

    def test_generate_example_structural_only(self):
        """Test generating example with only structural generation."""

        # given
        class TestModel(KernelBaseModel):
            name: str
            age: int
            tags: list[str]
            active: bool

        # when
        result = generate_one_shot_example(TestModel)

        # then
        assert result["name"] == "example (required)"  # Structural with required indicator
        assert result["age"] == 1  # Structural
        assert result["tags"] == ["example"]  # Structural
        assert result["active"] is True  # Structural

    def test_generate_example_with_nested_objects(self):
        """Test generating example with nested object structures."""

        # given
        class NestedModel(KernelBaseModel):
            nested_name: str = Field(default="nested_default")
            nested_count: int

        class TestModel(KernelBaseModel):
            name: str = Field(examples=["test_name"])
            nested: NestedModel

        # when
        result = generate_one_shot_example(TestModel)

        # then
        assert result["name"] == "test_name"  # Uses example
        assert isinstance(result["nested"], dict)
        # Note: nested objects use structural generation in our current implementation

    def test_generate_example_with_enums(self):
        """Test generating example with enum fields."""
        # given
        from enum import Enum

        class Status(str, Enum):
            ACTIVE = "active"
            INACTIVE = "inactive"

        class TestModel(KernelBaseModel):
            status: Status
            priority: str = Field(examples=["high"], default="medium")

        # when
        result = generate_one_shot_example(TestModel)

        # then
        assert result["status"] == "active"  # First enum value
        assert result["priority"] == "high"  # Uses example over default

    def test_generate_example_with_arrays(self):
        """Test generating example with array fields."""

        # given
        class TestModel(KernelBaseModel):
            tags: list[str] = Field(
                default=["default_tag"],
                examples=[["example_tag1", "example_tag2"]],
            )
            numbers: list[int]  # structural generation

        # when
        result = generate_one_shot_example(TestModel)

        # then
        assert result["tags"] == ["example_tag1", "example_tag2"]  # Uses example
        assert result["numbers"] == [1]  # Structural generation

    def test_generate_example_handles_exception_gracefully(self):
        """Test that function handles exceptions gracefully."""

        # given
        class InvalidModel(KernelBaseModel):
            test_field: str

        # when
        with patch(
            "llm_ci_runner.schema._generate_field_example",
            side_effect=Exception("Test error"),
        ):
            result = generate_one_shot_example(InvalidModel)

        # then
        assert result == {"example": "structure"}  # Fallback on error

    def test_generate_example_priority_order(self):
        """Test that examples take priority over defaults over structural generation."""

        # given
        class TestModel(KernelBaseModel):
            # Field with example (highest priority)
            field_with_example: str = Field(
                default="default_value",
                examples=["example_value"],
            )
            # Field with default only (medium priority)
            field_with_default: str = Field(default="default_only")
            # Field with structural only (lowest priority)
            field_structural: str

        # when
        result = generate_one_shot_example(TestModel)

        # then
        assert result["field_with_example"] == "example_value"  # Example wins
        assert result["field_with_default"] == "default_only"  # Default used
        assert result["field_structural"] == "example (required)"  # Structural fallback with required indicator

    def test_generate_example_with_complex_schema_refs(self):
        """Test generating example with complex schema $refs."""

        # given
        class NestedData(KernelBaseModel):
            features: list[str] = Field(default=["default_feature"])
            count: int = Field(examples=[42])

        class TestModel(KernelBaseModel):
            name: str = Field(examples=["test"])
            data: NestedData

        # when
        result = generate_one_shot_example(TestModel)

        # then
        assert result["name"] == "test"  # Uses example
        # For nested objects, current implementation does structural generation
        # This could be enhanced in the future to handle nested examples

    def test_generate_example_with_field_title_and_attributes(self):
        """Test generating example with field title and description attributes."""

        # given
        class TestModel(KernelBaseModel):
            # Field with title (should use title over generic "example")
            titled_field: str = Field(title="CustomTitle")
            # Field with description (should use description when no title)
            described_field: str = Field(description="Field with description")
            # Field with title AND description (title should take precedence)
            complex_field: str = Field(title="ComplexTitle", description="This has both title and description")

        # when
        result = generate_one_shot_example(TestModel)

        # then
        assert result["titled_field"] == "CustomTitle (required)"  # Uses title
        assert result["described_field"] == "Field with description (required)"  # Uses description
        assert result["complex_field"] == "ComplexTitle (required)"  # Title takes precedence

    def test_generate_example_with_long_description_truncation(self):
        """Test generating example with long field descriptions that get truncated."""
        # given
        long_description = (
            "This is a very long field description that exceeds thirty characters and should be truncated with ellipsis"
        )
        short_description = "Short description"

        class TestModel(KernelBaseModel):
            # Field with long description (should be truncated at 30 chars)
            long_desc_field: str = Field(description=long_description)
            # Field with short description (should not be truncated)
            short_desc_field: str = Field(description=short_description)

        # when
        result = generate_one_shot_example(TestModel)

        # then
        assert result["long_desc_field"].startswith("This is a very long field desc")  # Truncated
        assert result["long_desc_field"].endswith("... (required)")  # Has ellipsis
        assert result["short_desc_field"] == "Short description (required)"  # Not truncated

    def test_generate_example_with_optional_fields(self):
        """Test generating example distinguishing required vs optional fields."""
        # given

        class TestModel(KernelBaseModel):
            # Required field (no default, no Optional)
            required_field: str
            # Optional field with default
            optional_with_default: str | None = "default_value"
            # Optional field without default (using Optional type)
            optional_no_default: str | None = None

        # when
        result = generate_one_shot_example(TestModel)

        # then
        assert result["required_field"].endswith("(required)")  # Shows required
        assert result["optional_with_default"] == "default_value"  # Uses default, not structural
        # Note: Optional[str] = None fields may use structural generation or None handling

    def test_generate_example_with_union_and_complex_types(self):
        """Test generating example with Union types and complex typing constructs."""
        # given
        from enum import Enum

        class Priority(str, Enum):
            HIGH = "high"
            MEDIUM = "medium"
            LOW = "low"

        class NestedModel(KernelBaseModel):
            nested_value: str = "nested_default"

        class TestModel(KernelBaseModel):
            # Union type (should use first non-None type)
            union_field: str | int
            # Dict type
            dict_field: dict[str, str]
            # List with complex type
            list_field: list[str]
            # Enum field (should use first enum value)
            enum_field: Priority
            # Nested Pydantic model (should recurse)
            nested_field: NestedModel

        # when
        result = generate_one_shot_example(TestModel)

        # then
        # Union should resolve to first type (str)
        assert isinstance(result["union_field"], str)
        # Dict should have key-value structure
        assert result["dict_field"] == {"key": "value"}
        # List should have example items
        assert result["list_field"] == ["example"]
        # Enum should use first value
        assert result["enum_field"] == "high"
        # Nested model should be a dict with nested structure
        assert isinstance(result["nested_field"], dict)
        assert "nested_value" in result["nested_field"]

    def test_generate_example_with_pydantic_undefined_defaults(self):
        """Test handling of PydanticUndefined and Ellipsis default values."""
        # given
        from pydantic import Field

        class TestModel(KernelBaseModel):
            # Field that will have PydanticUndefined as default (should use structural)
            undefined_field: str
            # Field with ellipsis default (should use structural)
            ellipsis_field: str = Field(default=...)
            # Normal field with real default (should use default)
            normal_field: str = Field(default="real_default")

        # when
        result = generate_one_shot_example(TestModel)

        # then
        # PydanticUndefined should fall back to structural generation
        assert result["undefined_field"].endswith("(required)")
        # Ellipsis should fall back to structural generation
        assert result["ellipsis_field"].endswith("(required)")
        # Real default should be used
        assert result["normal_field"] == "real_default"

    @pytest.mark.parametrize(
        "invalid_annotation,expected_fallback",
        [
            pytest.param("not_a_type", "example", id="string_annotation"),
            pytest.param(123, "example", id="int_annotation"),
            pytest.param(None, "example", id="none_annotation"),
        ],
    )
    def test_generate_type_example_with_invalid_annotations(self, invalid_annotation, expected_fallback):
        """Test _generate_type_example handles invalid annotations gracefully."""
        # given
        from llm_ci_runner.schema import _generate_type_example

        # when - pass invalid annotation that will trigger TypeError/AttributeError in enum/model checks
        result = _generate_type_example(invalid_annotation)

        # then - should fall back to default "example" string
        assert result == expected_fallback

    def test_generate_type_example_with_malformed_enum_and_model_types(self):
        """Test _generate_type_example handles edge cases in enum and Pydantic model detection."""
        # given
        from llm_ci_runner.schema import _generate_type_example

        # Create mock objects that look like types but will fail isinstance/issubclass checks
        class MockType:
            """Mock object that looks like a type but isn't."""

            pass

        class AlmostEnum:
            """Object that has enum-like properties but isn't actually an enum."""

            def __init__(self):
                # This will cause AttributeError when list() is called
                pass

        # when/then - these should not crash and fall back to "example"
        assert _generate_type_example(MockType()) == "example"
        assert _generate_type_example(AlmostEnum()) == "example"

        # Test with object that has model_fields attribute but isn't a Pydantic model
        class FakeModel:
            model_fields = "not_a_dict"  # This will cause issues in recursion

        # This should handle the exception gracefully
        assert _generate_type_example(FakeModel()) == "example"

    def test_generate_field_example_with_optional_and_metadata_edge_cases(self):
        """Test _generate_field_example handles different annotation types correctly."""
        # given

        from pydantic import Field

        from llm_ci_runner.schema import _generate_field_example

        class TestModel(KernelBaseModel):
            # Plain str field - should get (required)/(optional) labels
            plain_str_required: str = Field(description="A required string field")
            plain_str_optional: str = Field(default="default", description="An optional string field")

            # Optional[str] field - has different annotation, won't get (required)/(optional)
            optional_str_field: str | None = Field(default=None, description="An optional field")

            # Test with title field (should use title over description)
            titled_field: str = Field(title="CustomTitle", description="This should be ignored")

        # when
        field_info_str_required = TestModel.model_fields["plain_str_required"]
        field_info_str_optional = TestModel.model_fields["plain_str_optional"]
        field_info_optional_str = TestModel.model_fields["optional_str_field"]
        field_info_titled = TestModel.model_fields["titled_field"]

        result_str_required = _generate_field_example(field_info_str_required)
        result_str_optional = _generate_field_example(field_info_str_optional)
        result_optional_str = _generate_field_example(field_info_optional_str)
        result_titled = _generate_field_example(field_info_titled)

        # then
        # Plain str fields should get (required)/(optional) labels
        assert "(required)" in result_str_required
        assert "A required string field" in result_str_required

        assert "(optional)" in result_str_optional
        assert "An optional string field" in result_str_optional

        # Optional[str] has different annotation - may not get labels, just test it doesn't crash
        assert isinstance(result_optional_str, str)  # Should return some string

        # Titled field should use title over description
        assert "CustomTitle" in result_titled
        assert "(required)" in result_titled

    def test_generate_type_example_with_typing_constructs_edge_cases(self):
        """Test _generate_type_example handles complex typing constructs and edge cases."""
        # given
        from typing import Union

        from llm_ci_runner.schema import _generate_type_example

        # when/then - test various typing constructs to trigger different code paths

        # Test Union types - these may fall back to "example" if not properly handled
        union_with_none = _generate_type_example(Union[str, None])
        assert union_with_none == "example"  # Union types may fallback

        union_multi = _generate_type_example(Union[int, str])
        assert union_multi == "example"  # Union types may fallback

        # Test basic types (should hit specific type checks and work correctly)
        assert _generate_type_example(int) == 1
        assert _generate_type_example(float) == 1.0
        assert _generate_type_example(bool) is True
        assert _generate_type_example(str) == "example"

        # Test fallback for unknown types
        class UnknownType:
            pass

        assert _generate_type_example(UnknownType) == "example"

        # Test None annotation
        assert _generate_type_example(None) == "example"
