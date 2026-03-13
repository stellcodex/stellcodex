from __future__ import annotations

import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.events.idempotency import ensure_idempotent
from app.models.phase2 import ProcessedEventId


class EventIdempotencyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        self.Session = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
        Base.metadata.create_all(bind=self.engine, tables=[ProcessedEventId.__table__])
        self.db = self.Session()

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()

    def test_same_consumer_duplicate_is_noop(self) -> None:
        first = ensure_idempotent(
            self.db,
            "evt-1",
            "file.ready",
            consumer="stream:consumer-a",
            file_id="scx_file_demo",
            version_no=1,
            trace_id="trace-1",
            payload={"file_id": "scx_file_demo", "version_no": 1},
        )
        self.db.commit()
        second = ensure_idempotent(
            self.db,
            "evt-1",
            "file.ready",
            consumer="stream:consumer-a",
            file_id="scx_file_demo",
            version_no=1,
            trace_id="trace-1",
            payload={"file_id": "scx_file_demo", "version_no": 1},
        )

        self.assertFalse(first)
        self.assertTrue(second)
        self.assertEqual(self.db.query(ProcessedEventId).count(), 1)

    def test_different_consumers_can_record_same_event_id(self) -> None:
        first = ensure_idempotent(self.db, "evt-2", "assembly.ready", consumer="stream:consumer-a")
        self.db.commit()
        second = ensure_idempotent(self.db, "evt-2", "assembly.ready", consumer="stream:consumer-b")
        self.db.commit()

        self.assertFalse(first)
        self.assertFalse(second)
        rows = self.db.query(ProcessedEventId).order_by(ProcessedEventId.consumer.asc()).all()
        self.assertEqual([row.consumer for row in rows], ["stream:consumer-a", "stream:consumer-b"])


if __name__ == "__main__":
    unittest.main()
