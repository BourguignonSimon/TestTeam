from __future__ import annotations

import json
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Iterable, Optional

from jsonschema import ValidationError
import redis

from .validation import EventValidator

MAX_ATTEMPTS = 5
RETRY_INTERVAL_MS = 1000


@dataclass
class Event:
    envelope: Dict[str, Any]
    message_id: str

    def to_stream_entry(self) -> Dict[str, str]:
        return {
            "envelope": json.dumps(self.envelope),
            "attempt": str(self.envelope.get("attempt", 1)),
        }


class EventBus:
    def __init__(self, client: redis.Redis, validator: Optional[EventValidator] = None) -> None:
        self.client = client
        self.validator = validator or EventValidator()

    def stream_name(self, project_id: str) -> str:
        return f"proj:{project_id}:events"

    def user_outbox(self, project_id: str) -> str:
        return f"proj:{project_id}:user_outbox"

    def dead_letter(self, project_id: str) -> str:
        return f"proj:{project_id}:dlq"

    def publish(self, project_id: str, envelope: Dict[str, Any]) -> str:
        """Validate and add an event to the project stream."""
        envelope = {**envelope, "timestamp": envelope.get("timestamp") or datetime.now(timezone.utc).isoformat()}
        self.validator.validate(envelope)
        stream = self.stream_name(project_id)
        event = Event(envelope=envelope, message_id="*")
        return self.client.xadd(stream, event.to_stream_entry())

    def publish_user_outbox(self, project_id: str, envelope: Dict[str, Any]) -> str:
        envelope = {**envelope, "timestamp": envelope.get("timestamp") or datetime.now(timezone.utc).isoformat()}
        self.validator.validate(envelope)
        outbox = self.user_outbox(project_id)
        event = Event(envelope=envelope, message_id="*")
        return self.client.xadd(outbox, event.to_stream_entry())

    def ensure_consumer_group(self, project_id: str, group: str, stream: Optional[str] = None) -> None:
        target_stream = stream or self.stream_name(project_id)
        try:
            self.client.xgroup_create(name=target_stream, groupname=group, id="$", mkstream=True)
        except redis.exceptions.ResponseError as exc:  # group exists
            if "BUSYGROUP" not in str(exc):
                raise

    def _dedupe_key(self, project_id: str, group: str, message_id: str) -> str:
        return f"dedupe:{project_id}:{group}:{message_id}"

    def _lock_key(self, project_id: str, backlog_item_id: str) -> str:
        return f"lock:{project_id}:{backlog_item_id}"

    @contextmanager
    def lock_backlog(self, project_id: str, backlog_item_id: str, ttl: int = 30):
        lock_key = self._lock_key(project_id, backlog_item_id)
        acquired = self.client.set(lock_key, "1", nx=True, ex=ttl)
        if not acquired:
            raise RuntimeError(f"backlog item {backlog_item_id} is locked")
        try:
            yield
        finally:
            self.client.delete(lock_key)

    def _is_duplicate(self, project_id: str, group: str, message_id: str) -> bool:
        return self.client.get(self._dedupe_key(project_id, group, message_id)) is not None

    def _mark_processed(self, project_id: str, group: str, message_id: str, ttl: int = 3600):
        self.client.set(self._dedupe_key(project_id, group, message_id), "1", ex=ttl)

    def _read(self, stream: str, group: str, consumer: str, count: int = 1):
        return self.client.xreadgroup(groupname=group, consumername=consumer, streams={stream: ">"}, count=count, block=1000)

    def handle_pending(self, stream: str, group: str, consumer: str, min_idle_ms: int = RETRY_INTERVAL_MS):
        pending = self.client.xpending_range(stream, group, min="-", max="+", count=10, consumername=None)
        for entry in pending:
            if entry.idle >= min_idle_ms:
                self.client.xclaim(stream, group, consumername=consumer, min_idle_time=min_idle_ms, message_ids=[entry.message_id])

    def consume(
        self,
        project_id: str,
        group: str,
        consumer: str,
        handler: Callable[[Dict[str, Any]], None],
        stream: Optional[str] = None,
    ) -> Iterable[str]:
        target_stream = stream or self.stream_name(project_id)
        self.ensure_consumer_group(project_id, group, target_stream)
        self.handle_pending(target_stream, group, consumer)

        messages = self._read(target_stream, group, consumer)
        for _, entries in messages:
            for message_id, data in entries:
                attempt = int(data.get("attempt", "1"))
                envelope_json = data["envelope"]
                try:
                    envelope = self.validator.ensure_json(envelope_json)
                except ValidationError as exc:
                    self.client.xadd(self.dead_letter(project_id), {"error": str(exc), "envelope": envelope_json, "attempt": str(attempt)})
                    self.client.xack(target_stream, group, message_id)
                    continue

                backlog_item_id = envelope["backlog_item_id"]
                if self._is_duplicate(project_id, group, message_id):
                    self.client.xack(target_stream, group, message_id)
                    continue

                with self.lock_backlog(project_id, backlog_item_id):
                    try:
                        handler(envelope)
                        self._mark_processed(project_id, group, message_id)
                        self.client.xack(target_stream, group, message_id)
                        yield message_id
                    except Exception as exc:  # noqa: BLE001
                        if attempt >= MAX_ATTEMPTS:
                            self.client.xadd(
                                self.dead_letter(project_id),
                                {"error": str(exc), "envelope": envelope_json, "attempt": str(attempt)},
                            )
                            self.client.xack(target_stream, group, message_id)
                        else:
                            retry_envelope = {**envelope, "attempt": attempt + 1}
                            self.client.xadd(target_stream, Event(retry_envelope, "*").to_stream_entry())
                            self.client.xack(target_stream, group, message_id)
                        continue

    def emit_snapshot(self, project_id: str, state: Dict[str, Any]) -> str:
        envelope = {
            "event_type": "snapshot",
            "project_id": project_id,
            "backlog_item_id": state.get("backlog_item_id", "n/a"),
            "correlation_id": state.get("correlation_id", "snapshot"),
            "causation_id": state.get("causation_id", "snapshot"),
            "payload": {"state": state},
        }
        return self.publish(project_id, envelope)


def build_envelope(event_type: str, project_id: str, backlog_item_id: str, payload: Dict[str, Any], correlation_id: str, causation_id: str) -> Dict[str, Any]:
    return {
        "event_type": event_type,
        "project_id": project_id,
        "backlog_item_id": backlog_item_id,
        "correlation_id": correlation_id,
        "causation_id": causation_id,
        "payload": payload,
    }
