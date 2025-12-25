from __future__ import annotations

from typing import Any, Dict


class ValidationError(Exception):
    pass


class Draft202012Validator:
    def __init__(self, schema: Dict[str, Any]):
        self.schema = schema

    def validate(self, instance: Dict[str, Any]) -> None:
        if not isinstance(instance, dict):
            raise ValidationError("instance must be object")
        required = self.schema.get("required", [])
        for field in required:
            if field not in instance:
                raise ValidationError(f"missing required field {field}")
        props = self.schema.get("properties", {})
        additional_allowed = self.schema.get("additionalProperties", True)
        for key, value in instance.items():
            if key not in props and not additional_allowed:
                raise ValidationError(f"unexpected property {key}")
            if key in props:
                self._validate_property(key, value, props[key])

    def _validate_property(self, key: str, value: Any, schema: Dict[str, Any]) -> None:
        expected_type = schema.get("type")
        if expected_type == "string":
            if not isinstance(value, str):
                raise ValidationError(f"{key} must be string")
            min_len = schema.get("minLength")
            if min_len is not None and len(value) < min_len:
                raise ValidationError(f"{key} shorter than {min_len}")
            if "enum" in schema and value not in schema["enum"]:
                raise ValidationError(f"{key} not in enum")
        elif expected_type == "object":
            Draft202012Validator(schema).validate(value)
        elif expected_type is not None:
            raise ValidationError(f"Unsupported type {expected_type}")
