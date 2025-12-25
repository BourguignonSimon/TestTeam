from __future__ import annotations

from typing import Dict

from core.event_bus import EventBus
from core.state_machine import ProjectState
from .base import Service


class Reporting(Service):
    def __init__(self, project_id: str, bus: EventBus, state: ProjectState):
        super().__init__("reporting", project_id, bus)
        self.state = state
        self._register_handlers()

    def _register_handlers(self) -> None:
        @self.on("work_completed")
        def _snapshot(envelope: Dict) -> None:
            backlog_item = self.state.get_or_create(envelope["backlog_item_id"])
            backlog_item.transition("done")
            state = {
                "project_id": self.project_id,
                "backlog_item_id": backlog_item.backlog_item_id,
                "status": backlog_item.status,
                "history": backlog_item.history,
                "causation_id": envelope["causation_id"],
                "correlation_id": envelope["correlation_id"],
            }
            self.bus.emit_snapshot(self.project_id, state)
