from __future__ import annotations

from typing import Dict

from core.event_bus import EventBus, build_envelope
from .base import Service


class Orchestrator(Service):
    def __init__(self, project_id: str, bus: EventBus):
        super().__init__("orchestrator", project_id, bus)
        self._register_handlers()

    def _register_handlers(self) -> None:
        @self.on("initial_request")
        def _handle_initial(envelope: Dict) -> None:
            payload = envelope["payload"]
            backlog_item_id = envelope["backlog_item_id"]
            new_event = build_envelope(
                "backlog_item_created",
                self.project_id,
                backlog_item_id,
                {"backlog_item_id": backlog_item_id, "priority": "high"},
                envelope["correlation_id"],
                envelope["causation_id"],
            )
            self.bus.publish(self.project_id, new_event)

        @self.on("user_response")
        def _handle_user_response(envelope: Dict) -> None:
            backlog_item_id = envelope["backlog_item_id"]
            ready = build_envelope(
                "ready_for_dev",
                self.project_id,
                backlog_item_id,
                {"backlog_item_id": backlog_item_id},
                envelope["correlation_id"],
                envelope["causation_id"],
            )
            self.bus.publish(self.project_id, ready)

        @self.on("qa_report")
        def _handle_qa(envelope: Dict) -> None:
            backlog_item_id = envelope["backlog_item_id"]
            done = build_envelope(
                "work_completed",
                self.project_id,
                backlog_item_id,
                {"backlog_item_id": backlog_item_id, "status": "done"},
                envelope["correlation_id"],
                envelope["causation_id"],
            )
            self.bus.publish(self.project_id, done)
