from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"


@lru_cache(maxsize=1)
def load_envelope_schema() -> Dict[str, Any]:
    with (SCHEMAS_DIR / "event_envelope.json").open("r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_payload_schemas() -> Dict[str, Any]:
    with (SCHEMAS_DIR / "payload_schemas.json").open("r", encoding="utf-8") as f:
        return json.load(f)["properties"]
