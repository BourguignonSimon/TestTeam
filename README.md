# Event-Driven Multi-Agent Framework (MVP)

This repository provides a minimal event-driven framework that coordinates multiple agents over Redis Streams. It demonstrates schema-first event validation, idempotent consumers, retry with dead-letter queues, and backlog item locking.

## Architecture

```
/schemas           JSON Schema Draft 2020-12 definitions
/core              Validation, event bus (Redis Streams), state helpers
/services          Agent implementations (orchestrator, clarification, dev, QA, reporting, user gateway)
/scripts           Demo workflows
/tests             Automated coverage
```

### Streams and groups
- Streams: `proj:{project_id}:events`, `proj:{project_id}:user_outbox`, `proj:{project_id}:dlq`
- Consumer groups: `g_orchestrator`, `g_clarification`, `g_dev`, `g_qa`, `g_reporting`, `g_user_gateway_in`, `g_user_gateway_out`

Every published and consumed event is validated against JSON Schema (Draft 2020-12). Consumers are idempotent per group, retries reclaim pending entries, and messages move to the DLQ after five failed attempts. A Redis lock prevents concurrent processing for the same `backlog_item_id`.

## Running locally

1. Start Redis:
   ```bash
   docker compose up -d
   ```

2. Install dependencies:
   ```bash
   pip install -e .
   ```

3. Run the demos (fakeredis by default; set `REAL_REDIS=1` to use the Docker Redis):
   ```bash
   python scripts/demo_happy_path.py
   python scripts/demo_failure_retry_dlq.py
   ```

## Tests

Run the automated tests with:
```bash
python -m pytest
```

## Notes

- Schemas live in `/schemas` and are loaded by the `core.validation.EventValidator`.
- The event bus (`core.event_bus.EventBus`) ensures validation, deduplication, locking, retry, pending reclaim, and DLQ routing.
- The demo scripts exercise the full lifecycle and a forced failure scenario.
