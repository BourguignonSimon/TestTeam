from __future__ import annotations

from typing import Callable, Dict, Iterable

from core.event_bus import EventBus


class Service:
    def __init__(self, name: str, project_id: str, bus: EventBus):
        self.name = name
        self.project_id = project_id
        self.bus = bus
        self.handlers: Dict[str, Callable[[dict], None]] = {}

    def on(self, event_type: str):
        def decorator(func: Callable[[dict], None]):
            self.handlers[event_type] = func
            return func

        return decorator

    def handle(self, envelope: dict) -> None:
        event_type = envelope["event_type"]
        handler = self.handlers.get(event_type)
        if handler:
            handler(envelope)

    def consume(self, group: str, consumer: str, stream: str | None = None) -> Iterable[str]:
        return self.bus.consume(self.project_id, group, consumer, self.handle, stream=stream)
