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
        model_title = (
            schema_dict.get("title", "DynamicOutputModel") if isinstance(schema_dict, dict) else "DynamicOutputModel"
        )
        LOGGER.debug(f"🏗️  Creating dynamic model: {model_title}")

        # Use the library's native support for base model types
        # Model naming is handled by the library via schema's 'title' field
        DynamicKernelModel = create_model_from_schema(schema_dict, base_model_type=KernelBaseModel)

        # Count fields for logging
        field_count = len(DynamicKernelModel.model_fields)
        required_fields = [name for name, field in DynamicKernelModel.model_fields.items() if field.is_required()]

        LOGGER.debug(f"✅ Created dynamic model with {field_count} fields")
        LOGGER.debug(f"   Required fields: {required_fields}")
        LOGGER.debug(f"   All fields: {list(DynamicKernelModel.model_fields.keys())}")

        return DynamicKernelModel

    except Exception as e:
        raise SchemaValidationError(f"Failed to create dynamic model: {e}") from e
