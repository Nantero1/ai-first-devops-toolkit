"""
Schema handling and dynamic model creation for LLM CI Runner.

This module provides functionality for creating dynamic Pydantic models from JSON schemas
and handling schema validation throughout the application.
"""

import logging
from typing import Any

from json_schema_to_pydantic import create_model as create_model_from_schema  # type: ignore[import-untyped]
from pydantic.fields import FieldInfo
from semantic_kernel.kernel_pydantic import KernelBaseModel

from .exceptions import SchemaValidationError

LOGGER = logging.getLogger(__name__)


def create_dynamic_model_from_schema(
    schema_dict: dict[str, Any],
) -> type[KernelBaseModel]:
    """
    Create a dynamic Pydantic model from JSON schema that inherits from KernelBaseModel.

    Uses the json-schema-to-pydantic library for robust schema conversion with KernelBaseModel as base class.
    Model name is determined by the schema's 'title' field, or defaults to library's default naming.

    Args:
        schema_dict: JSON schema dictionary

    Returns:
        Dynamic Pydantic model class inheriting from KernelBaseModel

    Raises:
        SchemaValidationError: If schema conversion fails
    """
    try:
        # Get model title for logging (safe for non-dict inputs)
        model_title_safe = (
            schema_dict.get("title", "DynamicOutputModel") if isinstance(schema_dict, dict) else "DynamicOutputModel"
        )
        model_title_safe = "".join(word.capitalize() for word in model_title_safe.split())
        if isinstance(schema_dict, dict):
            schema_dict["title"] = model_title_safe
        LOGGER.debug(f"🏗️  Creating dynamic model: {model_title_safe}")

        # Use the library's native support for base model types
        # Model naming is handled by the library via schema's 'title' field
        DynamicKernelModel: type[KernelBaseModel] = create_model_from_schema(
            schema_dict, base_model_type=KernelBaseModel
        )

        # Count fields for logging
        field_count = len(DynamicKernelModel.model_fields)
        required_fields = [name for name, field in DynamicKernelModel.model_fields.items() if field.is_required()]
        LOGGER.debug(
            f"✅ Model '{DynamicKernelModel.__name__}' created: {field_count} fields, {len(required_fields)} required"
        )

        return DynamicKernelModel

    except Exception as e:
        error_msg = f"Failed to create dynamic model from schema: {e}"
        LOGGER.error(error_msg)
        raise SchemaValidationError(error_msg) from e


def generate_one_shot_example(model_class: type[KernelBaseModel]) -> dict[str, Any]:
    """Generate a smart one-shot example using Pydantic's examples, defaults, and structure.

    Priority order: Field examples > Default values > Structural generation

    Args:
        model_class: Pydantic model class

    Returns:
        Dictionary containing smart example data
    """
    try:
        example = {}

        # Process each field individually
        for field_name, field_info in model_class.model_fields.items():
            field_value = None

            # 1. Check for field examples (highest priority) - use official property
            if field_info.examples and isinstance(field_info.examples, list) and len(field_info.examples) > 0:
                field_value = field_info.examples[0]

            # 2. Check for default values (medium priority)
            if field_value is None and not field_info.is_required():
                default_value = field_info.get_default()
                # Check if default is not PydanticUndefined
                from pydantic_core import PydanticUndefined

                if default_value is not PydanticUndefined and default_value is not ...:
                    field_value = default_value

            # 3. Generate structural example (lowest priority)
            if field_value is None:
                field_value = _generate_field_example(field_info)

            example[field_name] = field_value

        LOGGER.debug(f"✨ Generated smart example with {len(example)} fields")
        return example

    except Exception as e:
        LOGGER.warning(f"⚠️ Failed to generate smart example: {e}")
        return {"example": "structure"}


def _generate_field_example(field_info: FieldInfo) -> Any:
    """Generate a structural example for a single field based on its type annotation.

    Args:
        field_info: Pydantic field info

    Returns:
        Example value for the field
    """
    # Get the field annotation
    annotation = field_info.annotation

    # Handle basic types
    if annotation is str:
        str_example = "example"

        # Add title info if available (provides better field naming)
        if field_info.title:
            str_example = field_info.title

        # Add description info if available (provides context for LLM)
        elif field_info.description:
            # Keep it concise for structural guidance
            str_example = (
                field_info.description[:30] + "..." if len(field_info.description) > 30 else field_info.description
            )

        # Keep existing metadata - perfect for LLM constraint guidance
        if field_info.metadata:
            str_example += f" [{field_info.metadata}]"

        if field_info.is_required():
            str_example += " (required)"
        else:
            str_example += " (optional)"

        return str_example
    elif annotation is int:
        return 1
    elif annotation is float:
        return 1.0
    elif annotation is bool:
        return True

    # Handle enums - add proper type checking
    if annotation is not None:
        try:
            import enum

            if isinstance(annotation, type) and issubclass(annotation, enum.Enum):
                # Return first enum value
                enum_values = list(annotation)
                if enum_values:
                    return enum_values[0].value
        except (TypeError, AttributeError):  # pragma: no cover
            pass

        # Handle Pydantic models (nested objects) - add proper type checking
        try:
            if isinstance(annotation, type) and hasattr(annotation, "model_fields"):
                # This is likely a Pydantic model - recursively generate example
                return generate_one_shot_example(annotation)
        except (TypeError, AttributeError):  # pragma: no cover
            pass

    # Handle typing constructs
    try:
        import typing

        origin = typing.get_origin(annotation)
        args = typing.get_args(annotation)

        if origin is list:
            # List type - create list with one example element
            if args:
                item_example = _generate_type_example(args[0])
                return [item_example]
            return ["example"]

        elif origin is dict:
            # Dict type
            return {"key": "value"}

        elif origin is typing.Union:
            # Union type - use first non-None type
            for arg in args:
                if arg is not type(None):
                    return _generate_type_example(arg)

    except Exception:  # pragma: no cover
        pass

    # Fallback for unknown types
    return "example"


def _generate_type_example(type_annotation: Any) -> Any:
    """Generate an example value for a given type annotation.

    Args:
        type_annotation: The type annotation

    Returns:
        Example value for the type
    """
    if type_annotation is str:
        return "example"
    elif type_annotation is int:
        return 1
    elif type_annotation is float:
        return 1.0
    elif type_annotation is bool:
        return True

    # Handle enums - add proper type checking
    if type_annotation is not None:
        try:
            import enum

            if isinstance(type_annotation, type) and issubclass(type_annotation, enum.Enum):
                enum_values = list(type_annotation)
                if enum_values:
                    return enum_values[0].value
        except (TypeError, AttributeError):
            pass

        # Handle Pydantic models - add proper type checking
        try:
            if isinstance(type_annotation, type) and hasattr(type_annotation, "model_fields"):
                return generate_one_shot_example(type_annotation)
        except (TypeError, AttributeError):  # pragma: no cover
            pass

    return "example"
