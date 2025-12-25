from __future__ import annotations

from typing import Dict

from core.event_bus import EventBus, build_envelope
from .base import Service


class DevWorker(Service):
    def __init__(self, project_id: str, bus: EventBus, failure_mode: bool = False):
        super().__init__("dev_worker", project_id, bus)
        self.failure_mode = failure_mode
        self.fail_counts: Dict[str, int] = {}
        self._register_handlers()

    def _register_handlers(self) -> None:
        @self.on("ready_for_dev")
        def _build(envelope: Dict) -> None:
            backlog_item_id = envelope["backlog_item_id"]
            if self.failure_mode:
                attempts = self.fail_counts.get(backlog_item_id, 0) + 1
                self.fail_counts[backlog_item_id] = attempts
                raise RuntimeError(f"forced failure for {backlog_item_id} attempt {attempts}")

            deliverable = build_envelope(
                "dev_deliverable",
                self.project_id,
                backlog_item_id,
                {"description": "Implementation complete", "artifact": "artifact.tar.gz"},
                envelope["correlation_id"],
                envelope["causation_id"],
            )
            self.bus.publish(self.project_id, deliverable)
