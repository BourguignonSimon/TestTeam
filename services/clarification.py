from __future__ import annotations

from typing import Dict

from core.event_bus import EventBus, build_envelope
from .base import Service


class Clarification(Service):
    def __init__(self, project_id: str, bus: EventBus):
        super().__init__("clarification", project_id, bus)
        self._register_handlers()

    def _register_handlers(self) -> None:
        @self.on("backlog_item_created")
        def _ask_question(envelope: Dict) -> None:
            backlog_item_id = envelope["backlog_item_id"]
            question = build_envelope(
                "clarification_needed",
                self.project_id,
                backlog_item_id,
                {"question": "What is the acceptance criteria?", "assignee": envelope["payload"].get("requested_by", "user")},
                envelope["correlation_id"],
                envelope["causation_id"],
            )
            self.bus.publish_user_outbox(self.project_id, question)
