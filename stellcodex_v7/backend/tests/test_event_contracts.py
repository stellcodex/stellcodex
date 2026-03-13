from __future__ import annotations

import json
import unittest

from app.core.event_bus import EventBus
from app.core.events import EventEnvelope
from app.events.cloudevents import CloudEvent


class _FakeRedis:
    def __init__(self) -> None:
        self.rows: list[tuple[str, dict[str, str]]] = []

    def xadd(self, stream_key: str, fields: dict[str, str]) -> str:
        message_id = f"{stream_key}:{len(self.rows) + 1}"
        self.rows.append((message_id, dict(fields)))
        return message_id

    def xrevrange(self, _stream_key: str, count: int = 50):
        return list(reversed(self.rows[-count:]))


class EventContractTests(unittest.TestCase):
    def test_event_envelope_round_trips_flat_wire_format(self) -> None:
        event = EventEnvelope.build(
            event_type="file.uploaded",
            source="tests",
            subject="file:demo",
            tenant_id="7",
            project_id="p1",
            trace_id="trace-1",
            event_id="evt-1",
            data={"file_id": "scx_file_demo", "version_no": 1},
        )

        wire = event.to_wire()

        self.assertEqual(wire["specversion"], "1.0")
        self.assertEqual(wire["datacontenttype"], "application/json")
        self.assertEqual(json.loads(wire["data"]), event.data)
        self.assertEqual(json.loads(wire["payload"]), event.to_dict())

        restored = EventEnvelope.from_wire(wire)

        self.assertEqual(restored.to_dict(), event.to_dict())

    def test_event_envelope_reads_legacy_payload_only_wire_format(self) -> None:
        legacy_payload = {
            "id": "evt-legacy",
            "type": "file.converted",
            "source": "legacy.bus",
            "subject": "file:demo",
            "tenant_id": "9",
            "project_id": "demo",
            "trace_id": "trace-legacy",
            "time": "2026-03-10T00:00:00Z",
            "data": {"file_id": "scx_file_demo", "version_no": 2},
        }

        restored = EventEnvelope.from_wire({"payload": json.dumps(legacy_payload)})

        self.assertEqual(restored.id, "evt-legacy")
        self.assertEqual(restored.specversion, "1.0")
        self.assertEqual(restored.datacontenttype, "application/json")
        self.assertEqual(restored.data["version_no"], 2)

    def test_cloud_event_alias_uses_canonical_contract(self) -> None:
        event = CloudEvent.build(
            event_type="agent.task.submitted",
            source="tests.agent",
            subject="task:1",
            tenant_id="1",
            project_id="demo",
            data={"task_id": "task_1"},
        )

        self.assertIsInstance(event, EventEnvelope)
        self.assertEqual(event.specversion, "1.0")
        self.assertEqual(event.to_dict()["data"]["task_id"], "task_1")

    def test_legacy_event_bus_publishes_canonical_wire_and_fetches_back(self) -> None:
        bus = EventBus(stream_key="tests:phase2")
        bus.redis = _FakeRedis()

        event = bus.publish_event(
            event_type="assembly.ready",
            source="tests",
            subject="file:demo",
            tenant_id="3",
            project_id="demo",
            trace_id="trace-bus",
            event_id="evt-bus",
            data={"file_id": "scx_file_demo", "version_no": 5},
        )

        self.assertEqual(event.id, "evt-bus")
        self.assertEqual(len(bus.redis.rows), 1)
        stored_fields = bus.redis.rows[0][1]
        self.assertEqual(stored_fields["specversion"], "1.0")
        self.assertEqual(stored_fields["id"], "evt-bus")
        self.assertEqual(json.loads(stored_fields["payload"])["type"], "assembly.ready")

        recent = bus.fetch_recent(limit=5)

        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0].id, "evt-bus")
        self.assertEqual(recent[0].data["version_no"], 5)


if __name__ == "__main__":
    unittest.main()
