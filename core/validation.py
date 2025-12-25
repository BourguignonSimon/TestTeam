from __future__ import annotations

import json
from typing import Any, Dict

from jsonschema import Draft202012Validator, ValidationError

from .schemas import load_envelope_schema, load_payload_schemas


class SchemaRegistry:
    def __init__(self) -> None:
        self.envelope_validator = Draft202012Validator(load_envelope_schema())
        payload_schemas = load_payload_schemas()
        self.payload_validators: Dict[str, Draft202012Validator] = {
            event_type: Draft202012Validator(schema)
            for event_type, schema in payload_schemas.items()
        }

    def validate_envelope(self, envelope: Dict[str, Any]) -> None:
        self.envelope_validator.validate(envelope)

    def validate_payload(self, event_type: str, payload: Dict[str, Any]) -> None:
        if event_type not in self.payload_validators:
            raise ValidationError(f"Unknown event_type: {event_type}")
        self.payload_validators[event_type].validate(payload)


class EventValidator:
    def __init__(self, registry: SchemaRegistry | None = None) -> None:
        self.registry = registry or SchemaRegistry()

    def validate(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        self.registry.validate_envelope(envelope)
        payload = envelope.get("payload", {})
        event_type = envelope.get("event_type", "")
        self.registry.validate_payload(event_type, payload)
        return envelope

    def ensure_json(self, data: str) -> Dict[str, Any]:
        return self.validate(json.loads(data))
