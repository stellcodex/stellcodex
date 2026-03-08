from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from app.core.dlq import PermanentStageError
from app.core.event_types import EventType
from app.core.events import EventEnvelope
from app.workers import tasks
from app.workers.consumers import pipeline


class _DummyDb:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


@dataclass
class _ManifestRow:
    input_hash: str
    status: str = "ready"
    artifact_payload: dict | None = None
    cache_hit_count: int = 0


class _FakeQuery:
    def __init__(self, row) -> None:
        self.row = row

    def filter(self, *_args, **_kwargs):
        return self

    def first(self):
        return self.row


class _FakeDb:
    def __init__(self, row) -> None:
        self.row = row

    def query(self, *_args, **_kwargs):
        return _FakeQuery(self.row)

    def add(self, *_args, **_kwargs):
        return None

    def commit(self):
        return None

    def rollback(self):
        return None

    def refresh(self, _row):
        return None

    def close(self):
        return None


class _FakeBus:
    def __init__(self) -> None:
        self.events: list[EventEnvelope] = []

    def publish_event(self, **kwargs) -> EventEnvelope:
        env = EventEnvelope.build(
            event_type=kwargs["event_type"],
            source=kwargs["source"],
            subject=kwargs["subject"],
            tenant_id=kwargs["tenant_id"],
            project_id=kwargs["project_id"],
            trace_id=kwargs.get("trace_id"),
            event_id=kwargs.get("event_id"),
            data=kwargs.get("data"),
        )
        self.events.append(env)
        return env


class Phase2EventPipelineTests(unittest.TestCase):
    def _envelope(self) -> EventEnvelope:
        return EventEnvelope.build(
            event_type=EventType.FILE_UPLOADED.value,
            source="test",
            subject="scx_file_aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            tenant_id="1",
            project_id="p1",
            data={
                "file_id": "scx_file_aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                "version_no": 1,
            },
        )

    def test_duplicate_event_noop(self) -> None:
        db = _DummyDb()
        env = self._envelope()
        bus = SimpleNamespace()
        with patch.object(pipeline, "is_processed", return_value=True):
            out = pipeline.consume_with_guards(
                db,
                bus,
                envelope=env,
                consumer_name="phase2.consumer.convert",
                stage="convert",
                max_retries=3,
                failure_code="CONVERT_FAIL",
                handler=lambda *_args, **_kwargs: {},
            )
        self.assertEqual(out["status"], "duplicate")

    def test_cache_hit_short_circuit(self) -> None:
        db = _DummyDb()
        env = self._envelope()
        row = _ManifestRow(
            input_hash=pipeline.stable_hash(env.data),
            status="ready",
            artifact_payload={"file_id": env.data["file_id"], "artifact_uri": "converted/x.glb"},
        )
        with patch.object(pipeline, "is_processed", return_value=False), patch.object(
            pipeline, "acquire_stage_lock", return_value="token"
        ), patch.object(pipeline, "get_manifest_row", return_value=row), patch.object(
            pipeline, "cache_hit"
        ) as cache_hit_mock, patch.object(
            pipeline, "mark_processed"
        ) as mark_processed_mock, patch.object(
            pipeline, "release_stage_lock"
        ):
            out = pipeline.consume_with_guards(
                db,
                SimpleNamespace(),
                envelope=env,
                consumer_name="phase2.consumer.convert",
                stage="convert",
                max_retries=3,
                failure_code="CONVERT_FAIL",
                handler=lambda *_args, **_kwargs: {"should_not_run": True},
            )
        self.assertEqual(out["status"], "cache_hit")
        self.assertEqual(out["payload"]["artifact_uri"], "converted/x.glb")
        self.assertTrue(cache_hit_mock.called)
        self.assertTrue(mark_processed_mock.called)

    def test_permanent_failure_goes_to_dlq(self) -> None:
        db = _DummyDb()
        env = self._envelope()

        def _handler(*_args, **_kwargs):
            raise PermanentStageError("hard fail", "CONVERT_FAIL")

        with patch.object(pipeline, "is_processed", return_value=False), patch.object(
            pipeline, "acquire_stage_lock", return_value="token"
        ), patch.object(pipeline, "get_manifest_row", return_value=None), patch.object(
            pipeline, "record_dead_letter"
        ) as dlq_mock, patch.object(
            pipeline, "release_stage_lock"
        ):
            out = pipeline.consume_with_guards(
                db,
                SimpleNamespace(),
                envelope=env,
                consumer_name="phase2.consumer.convert",
                stage="convert",
                max_retries=0,
                failure_code="CONVERT_FAIL",
                handler=_handler,
            )
        self.assertEqual(out["status"], "failed")
        self.assertEqual(out["failure_code"], "CONVERT_FAIL")
        self.assertTrue(dlq_mock.called)

    def test_upload_to_ready_event_chain(self) -> None:
        fake_file = SimpleNamespace(
            file_id="scx_file_bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            tenant_id=7,
            status="queued",
            meta={"project_id": "demo", "kind": "3d", "mode": "brep"},
            original_filename="part.step",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        fake_db = _FakeDb(fake_file)
        fake_bus = _FakeBus()

        def _consume(_db, _bus, *, stage, **_kwargs):
            if stage == "pack":
                fake_file.status = "ready"
            return {
                "status": "processed",
                "payload": {
                    "file_id": fake_file.file_id,
                    "version_no": 1,
                    "stage": stage,
                    "approval_required": False,
                },
            }

        with patch.object(tasks, "SessionLocal", return_value=fake_db), patch.object(
            tasks, "default_event_bus", return_value=fake_bus
        ), patch.object(tasks, "resolve_version_no", return_value=1), patch.object(
            tasks, "consume_with_guards", side_effect=_consume
        ):
            out = tasks.convert_file(fake_file.file_id)

        self.assertEqual(out["status"], "ready")
        emitted = [evt.type for evt in fake_bus.events]
        self.assertEqual(
            emitted,
            [
                EventType.FILE_UPLOADED.value,
                EventType.FILE_CONVERT_STARTED.value,
                EventType.FILE_CONVERTED.value,
                EventType.ASSEMBLY_READY.value,
                EventType.DECISION_READY.value,
                "decision.produced",
                EventType.DFM_READY.value,
                "dfm.completed",
                EventType.REPORT_READY.value,
                EventType.PACKAGE_READY.value,
                "file.ready",
            ],
        )


if __name__ == "__main__":
    unittest.main()
