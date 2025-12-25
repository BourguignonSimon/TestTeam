from __future__ import annotations

from typing import Dict, Iterable

from core.event_bus import EventBus, build_envelope


class UserGateway:
    def __init__(self, project_id: str, bus: EventBus):
        self.project_id = project_id
        self.bus = bus

    def submit_initial(self, backlog_item_id: str, summary: str, requested_by: str) -> str:
        envelope = build_envelope(
            "initial_request",
            self.project_id,
            backlog_item_id,
            {"summary": summary, "requested_by": requested_by},
            correlation_id=f"corr-{backlog_item_id}",
            causation_id=f"user-{backlog_item_id}",
        )
        return self.bus.publish(self.project_id, envelope)

    def consume_questions(self, consumer: str) -> Iterable[str]:
        group = "g_user_gateway_out"
        self.bus.ensure_consumer_group(self.project_id, group, stream=self.bus.user_outbox(self.project_id))
        self.bus.handle_pending(self.bus.user_outbox(self.project_id), group, consumer)
        messages = self.bus.consume(
            project_id=self.project_id,
            group=group,
            consumer=consumer,
            handler=self._answer_question,
            stream=self.bus.user_outbox(self.project_id),
        )
        return messages

    def _answer_question(self, envelope: Dict) -> None:
        answer = build_envelope(
            "user_response",
            self.project_id,
            envelope["backlog_item_id"],
            {"question": envelope["payload"]["question"], "answer": "Here are the acceptance criteria."},
            correlation_id=envelope["correlation_id"],
            causation_id="user-reply",
        )
        self.bus.publish(self.project_id, answer)
