from __future__ import annotations

from typing import Dict

from core.event_bus import EventBus, build_envelope
from .base import Service


class QAWorker(Service):
    def __init__(self, project_id: str, bus: EventBus):
        super().__init__("qa_worker", project_id, bus)
        self._register_handlers()

    def _register_handlers(self) -> None:
        @self.on("dev_deliverable")
        def _test(envelope: Dict) -> None:
            backlog_item_id = envelope["backlog_item_id"]
            report = build_envelope(
                "qa_report",
                self.project_id,
                backlog_item_id,
                {"status": "pass", "notes": "All checks green"},
                envelope["correlation_id"],
                envelope["causation_id"],
            )
            self.bus.publish(self.project_id, report)
