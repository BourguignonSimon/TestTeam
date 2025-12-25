from __future__ import annotations

import os
from typing import List

import redis
import fakeredis

from core.event_bus import EventBus, build_envelope
from services.dev_worker import DevWorker
from services.orchestrator import Orchestrator
from services.user_gateway import UserGateway


def build_client() -> redis.Redis:
    if os.getenv("REAL_REDIS"):
        return redis.Redis(host=os.getenv("REDIS_HOST", "localhost"), port=int(os.getenv("REDIS_PORT", "6379")), decode_responses=True)
    return fakeredis.FakeRedis(decode_responses=True)


def run_failure_demo() -> List[str]:
    project_id = "demo-fail"
    backlog_item_id = "item-fail"
    client = build_client()
    bus = EventBus(client)

    orchestrator = Orchestrator(project_id, bus)
    failing_dev = DevWorker(project_id, bus, failure_mode=True)
    gateway = UserGateway(project_id, bus)

    transcript: List[str] = []

    gateway.submit_initial(backlog_item_id, summary="Failing item", requested_by="qa")

    for _ in orchestrator.consume("g_orchestrator", "orch"):
        transcript.append("orchestrator handled initial")

    ready = build_envelope(
        "ready_for_dev",
        project_id,
        backlog_item_id,
        {"backlog_item_id": backlog_item_id},
        correlation_id="corr-fail",
        causation_id="orch",
    )
    bus.publish(project_id, ready)

    # Dev worker will raise repeatedly, triggering retry until DLQ
    for _ in range(6):
        list(failing_dev.consume("g_dev", "dev"))

    dlq_entries = client.xread({bus.dead_letter(project_id): "0"}, count=10)
    transcript.append(f"dlq size: {len(dlq_entries[0][1]) if dlq_entries else 0}")
    return transcript


if __name__ == "__main__":
    for line in run_failure_demo():
        print(line)
