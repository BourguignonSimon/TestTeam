from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class BacklogItem:
    backlog_item_id: str
    status: str = "new"
    history: List[str] = field(default_factory=list)

    def transition(self, new_status: str) -> None:
        self.status = new_status
        self.history.append(new_status)


@dataclass
class ProjectState:
    project_id: str
    backlog: Dict[str, BacklogItem] = field(default_factory=dict)

    def get_or_create(self, backlog_item_id: str) -> BacklogItem:
        if backlog_item_id not in self.backlog:
            self.backlog[backlog_item_id] = BacklogItem(backlog_item_id)
        return self.backlog[backlog_item_id]
