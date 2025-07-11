"""
Schema handling and dynamic model creation for LLM CI Runner.

This module provides functionality for creating dynamic Pydantic models from JSON schemas
and handling schema validation throughout the application.
"""

import logging
from typing import Any

from json_schema_to_pydantic import create_model as create_model_from_schema  # type: ignore[import-untyped]
from semantic_kernel.kernel_pydantic import KernelBaseModel

from .exceptions import SchemaValidationError

LOGGER = logging.getLogger(__name__)


def create_dynamic_model_from_schema(
    schema_dict: dict[str, Any], model_name: str = "DynamicOutputModel"
) -> type[KernelBaseModel]:
    """
    Create a dynamic Pydantic model from JSON schema that inherits from KernelBaseModel.

    Uses the json-schema-to-pydantic library for robust schema conversion instead of manual implementation.

    Args:
        schema_dict: JSON schema dictionary
        model_name: Name for the generated model class

    Returns:
        Dynamic Pydantic model class inheriting from KernelBaseModel

    Raises:
        SchemaValidationError: If schema conversion fails
    """
    LOGGER.debug(f"🏗️  Creating dynamic model: {model_name}")

    try:
        # Use the dedicated library for robust JSON schema -> Pydantic conversion
        base_generated_model = create_model_from_schema(schema_dict)

        # Create a new class that inherits from both KernelBaseModel and the generated model
        # This ensures we get KernelBaseModel functionality while keeping the schema structure
        class DynamicKernelModel(KernelBaseModel, base_generated_model):  # type: ignore[valid-type, misc]
            pass

        # Set the name for better debugging
        DynamicKernelModel.__name__ = model_name
        DynamicKernelModel.__qualname__ = model_name

        # Count fields for logging
        field_count = len(base_generated_model.model_fields)
        required_fields = [name for name, field in base_generated_model.model_fields.items() if field.is_required()]

        LOGGER.info(f"✅ Created dynamic model with {field_count} fields")
        LOGGER.debug(f"   Required fields: {required_fields}")
        LOGGER.debug(f"   All fields: {list(base_generated_model.model_fields.keys())}")

        return DynamicKernelModel

    except Exception as e:
        raise SchemaValidationError(f"Failed to create dynamic model: {e}") from e
