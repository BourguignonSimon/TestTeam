import pytest

from core.event_bus import EventBus, build_envelope
from core.validation import EventValidator
import fakeredis


def test_invalid_payload_rejected():
    client = fakeredis.FakeRedis(decode_responses=True)
    bus = EventBus(client, validator=EventValidator())
    bad_envelope = build_envelope(
        "initial_request",
        "proj",
        "b1",
        {"summary": "", "requested_by": ""},
        "corr",
        "cause",
    )
    with pytest.raises(Exception):
        bus.publish("proj", bad_envelope)
