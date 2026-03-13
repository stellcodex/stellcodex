from __future__ import annotations

import time
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.worker_registry import build_local_worker_snapshot, heartbeat_worker_node, set_worker_status, upsert_worker_node
from app.db.base import Base
from app.models.engineering import WorkerNode


class WorkerRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        self.Session = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
        Base.metadata.create_all(bind=self.engine, tables=[WorkerNode.__table__])
        self.db = self.Session()

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()

    def test_upsert_heartbeat_and_status_transitions(self) -> None:
        snapshot = build_local_worker_snapshot(queues=["cad", "render"])
        row = upsert_worker_node(self.db, **snapshot)
        self.db.commit()

        self.assertEqual(row.worker_id, snapshot["worker_id"])
        self.assertEqual(row.status, "online")
        self.assertEqual(row.capabilities_json["queues"], ["cad", "render"])

        first_heartbeat = row.last_heartbeat
        time.sleep(0.01)
        heartbeat_worker_node(self.db, worker_id=row.worker_id, status="busy")
        self.db.commit()

        refreshed = self.db.query(WorkerNode).filter(WorkerNode.worker_id == row.worker_id).first()
        assert refreshed is not None
        self.assertEqual(refreshed.status, "busy")
        self.assertGreaterEqual(refreshed.last_heartbeat, first_heartbeat)

        set_worker_status(self.db, worker_id=row.worker_id, status="offline")
        self.db.commit()
        refreshed = self.db.query(WorkerNode).filter(WorkerNode.worker_id == row.worker_id).first()
        assert refreshed is not None
        self.assertEqual(refreshed.status, "offline")
