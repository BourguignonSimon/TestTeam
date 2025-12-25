from __future__ import annotations

import os
from typing import List

import redis
import fakeredis

from core.event_bus import EventBus
from core.state_machine import ProjectState
from services.clarification import Clarification
from services.dev_worker import DevWorker
from services.orchestrator import Orchestrator
from services.qa_worker import QAWorker
from services.reporting import Reporting
from services.user_gateway import UserGateway


def build_client() -> redis.Redis:
    if os.getenv("REAL_REDIS"):
        return redis.Redis(host=os.getenv("REDIS_HOST", "localhost"), port=int(os.getenv("REDIS_PORT", "6379")), decode_responses=True)
    return fakeredis.FakeRedis(decode_responses=True)


def run_demo() -> List[str]:
    project_id = "demo"
    backlog_item_id = "item-1"
    client = build_client()
    bus = EventBus(client)
    state = ProjectState(project_id)

    orchestrator = Orchestrator(project_id, bus)
    clarification = Clarification(project_id, bus)
    dev_worker = DevWorker(project_id, bus)
    qa_worker = QAWorker(project_id, bus)
    reporting = Reporting(project_id, bus, state)
    gateway = UserGateway(project_id, bus)

    transcript: List[str] = []

    gateway.submit_initial(backlog_item_id, summary="Implement feature", requested_by="product")

    for service, group, consumer in [
        (orchestrator, "g_orchestrator", "orch"),
        (clarification, "g_clarification", "clar"),
    ]:
        for _ in service.consume(group, consumer):
            transcript.append(f"{service.name} handled an event")

    for _ in gateway.consume_questions("gateway-out"):
        transcript.append("user_gateway answered clarification")

    for service, group, consumer in [
        (orchestrator, "g_orchestrator", "orch"),
        (dev_worker, "g_dev", "dev"),
        (qa_worker, "g_qa", "qa"),
        (orchestrator, "g_orchestrator", "orch"),
        (reporting, "g_reporting", "report"),
    ]:
        for _ in service.consume(group, consumer):
            transcript.append(f"{service.name} handled an event")

    snapshots = client.xread({bus.stream_name(project_id): "0"}, count=None)
    transcript.append(f"snapshot count: {len(snapshots)}")
    return transcript


if __name__ == "__main__":
    for line in run_demo():
        print(line)
