from __future__ import annotations

import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from app.api.v1.routes import approvals as approval_routes
from app.security.deps import Principal


def _user(role: str = "owner", user_id: str = "owner-1") -> Principal:
    return Principal(typ="user", user_id=user_id, role=role)


def _file(**overrides):
    payload = {
        "file_id": "scx_file_11111111-1111-1111-1111-111111111111",
        "tenant_id": 42,
        "owner_user_id": "owner-1",
        "meta": {"project_id": "default"},
        "decision_json": None,
    }
    payload.update(overrides)
    return SimpleNamespace(**payload)


def _session(**overrides):
    payload = {
        "id": "session-1",
        "state": "S5",
        "status_gate": "NEEDS_APPROVAL",
        "approval_required": True,
        "decision_json": None,
        "file_id": "scx_file_11111111-1111-1111-1111-111111111111",
    }
    payload.update(overrides)
    return SimpleNamespace(**payload)


def _assert_no_private_locator(payload: dict) -> None:
    text = json.dumps(payload, ensure_ascii=True, default=str).lower()
    for banned in ("storage_key", "object_key", "revision_id", "\"bucket\"", "uploads/"):
        if banned in text:
            raise AssertionError(f"approval payload leaked banned token: {banned}")


class _FakeBus:
    def __init__(self) -> None:
        self.events = []

    def publish_event(self, **kwargs) -> None:
        self.events.append(kwargs)


class _FakeDB:
    def __init__(self) -> None:
        self.added = []
        self.commits = 0
        self.refreshed = []

    def add(self, row) -> None:
        self.added.append(row)

    def commit(self) -> None:
        self.commits += 1

    def refresh(self, row) -> None:
        self.refreshed.append(row)


class ApprovalContractTests(unittest.TestCase):
    def test_approve_requires_user_token(self) -> None:
        db = _FakeDB()

        with patch.object(approval_routes, "_load_session", return_value=_session()), \
             patch.object(approval_routes, "_load_file_for_session", return_value=_file()):
            with self.assertRaises(HTTPException) as ctx:
                approval_routes.approve_session(
                    "session-1",
                    approval_routes.ApprovalActionIn(note=None),
                    db=db,
                    principal=Principal(typ="guest", owner_sub="guest-1", anon=True),
                )

        self.assertEqual(ctx.exception.status_code, 401)

    def test_cross_tenant_approval_attempt_is_forbidden(self) -> None:
        db = _FakeDB()

        with patch.object(approval_routes, "_load_session", return_value=_session()), \
             patch.object(approval_routes, "_load_file_for_session", return_value=_file(owner_user_id="owner-2")):
            with self.assertRaises(HTTPException) as ctx:
                approval_routes.approve_session(
                    "session-1",
                    approval_routes.ApprovalActionIn(note=None),
                    db=db,
                    principal=_user(user_id="owner-1"),
                )

        self.assertEqual(ctx.exception.status_code, 403)

    def test_invalid_approval_state_jump_fails(self) -> None:
        db = _FakeDB()
        decision = {
            "state": "S2",
            "status_gate": "PENDING",
            "approval_required": False,
            "conflict_flags": [],
            "rule_explanations": ["pending"],
        }

        with patch.object(approval_routes, "_load_session", return_value=_session(state="S2")), \
             patch.object(approval_routes, "_load_file_for_session", return_value=_file()), \
             patch.object(approval_routes, "_ensure_canonical_decision", return_value=decision):
            with self.assertRaises(HTTPException) as ctx:
                approval_routes.approve_session(
                    "session-1",
                    approval_routes.ApprovalActionIn(note=None),
                    db=db,
                    principal=_user(),
                )

        self.assertEqual(ctx.exception.status_code, 409)
        self.assertEqual(ctx.exception.detail, "Session state is not approvable")

    def test_approve_emits_audit_and_evidence_and_transitions_to_s7(self) -> None:
        db = _FakeDB()
        row = _session(state="S5")
        file_row = _file()
        decision = {
            "state": "S5",
            "status_gate": "NEEDS_APPROVAL",
            "approval_required": True,
            "conflict_flags": ["approval_rejected"],
            "rule_explanations": ["needs approval"],
        }
        bus = _FakeBus()

        with patch.object(approval_routes, "_load_session", return_value=row), \
             patch.object(approval_routes, "_load_file_for_session", return_value=file_row), \
             patch.object(approval_routes, "_ensure_canonical_decision", return_value=decision), \
             patch.object(approval_routes, "upsert_orchestrator_session", return_value=row), \
             patch.object(approval_routes, "upsert_projection", return_value=None), \
             patch.object(approval_routes, "default_event_bus", return_value=bus), \
             patch.object(approval_routes, "write_memory_payload", return_value="/tmp/approval.json"), \
             patch.object(approval_routes, "log_event") as log_mock:
            result = approval_routes.approve_session(
                "session-1",
                approval_routes.ApprovalActionIn(note="ship it"),
                db=db,
                principal=_user(),
            )

        self.assertEqual(result.file_id, file_row.file_id)
        self.assertEqual(result.state, "S7")
        self.assertEqual(result.status_gate, "PASS")
        self.assertFalse(result.approval_required)
        _assert_no_private_locator(result.model_dump())
        self.assertEqual(file_row.meta["approval_override"], "approved")
        self.assertEqual(file_row.meta["decision_json"]["state_transition_path"], ["S5", "S6", "S7"])
        self.assertNotIn("approval_rejected", file_row.meta["decision_json"]["conflict_flags"])
        self.assertEqual(len(bus.events), 2)
        self.assertTrue(all(event["tenant_id"] == "42" for event in bus.events))
        log_mock.assert_called_once()
        self.assertEqual(log_mock.call_args.args[1], "approval.approved")
        self.assertEqual(log_mock.call_args.kwargs["data"]["from_state"], "S5")
        self.assertEqual(log_mock.call_args.kwargs["data"]["to_state"], "S7")

    def test_duplicate_approve_does_not_corrupt_state(self) -> None:
        db = _FakeDB()
        row = _session(state="S7", approval_required=False)
        file_row = _file()
        decision = {
            "state": "S7",
            "status_gate": "PASS",
            "approval_required": False,
            "conflict_flags": [],
            "rule_explanations": ["already approved"],
        }

        with patch.object(approval_routes, "_load_session", return_value=row), \
             patch.object(approval_routes, "_load_file_for_session", return_value=file_row), \
             patch.object(approval_routes, "_ensure_canonical_decision", return_value=decision), \
             patch.object(approval_routes, "upsert_orchestrator_session", return_value=row), \
             patch.object(approval_routes, "upsert_projection", return_value=None), \
             patch.object(approval_routes, "default_event_bus", return_value=_FakeBus()), \
             patch.object(approval_routes, "write_memory_payload", return_value="/tmp/approval.json"), \
             patch.object(approval_routes, "log_event", return_value=None):
            result = approval_routes.approve_session(
                "session-1",
                approval_routes.ApprovalActionIn(note=None),
                db=db,
                principal=_user(),
            )

        self.assertEqual(result.state, "S7")
        _assert_no_private_locator(result.model_dump())
        self.assertEqual(file_row.meta["decision_json"]["state_transition_path"], ["S7"])

    def test_reject_returns_session_to_s4_and_marks_conflict(self) -> None:
        db = _FakeDB()
        row = _session(state="S7", approval_required=False)
        file_row = _file()
        decision = {
            "state": "S7",
            "status_gate": "PASS",
            "approval_required": False,
            "conflict_flags": [],
            "rule_explanations": ["already approved"],
        }
        bus = _FakeBus()

        with patch.object(approval_routes, "_load_session", return_value=row), \
             patch.object(approval_routes, "_load_file_for_session", return_value=file_row), \
             patch.object(approval_routes, "_ensure_canonical_decision", return_value=decision), \
             patch.object(approval_routes, "upsert_orchestrator_session", return_value=row), \
             patch.object(approval_routes, "upsert_projection", return_value=None), \
             patch.object(approval_routes, "default_event_bus", return_value=bus), \
             patch.object(approval_routes, "write_memory_payload", return_value="/tmp/reject.json"), \
             patch.object(approval_routes, "log_event") as log_mock:
            result = approval_routes.reject_session(
                "session-1",
                approval_routes.ApprovalActionIn(note="needs rework"),
                db=db,
                principal=_user(),
            )

        self.assertEqual(result.state, "S4")
        self.assertTrue(result.approval_required)
        _assert_no_private_locator(result.model_dump())
        self.assertEqual(file_row.meta["approval_override"], "rejected")
        self.assertIn("approval_rejected", file_row.meta["decision_json"]["conflict_flags"])
        self.assertEqual(len(bus.events), 2)
        log_mock.assert_called_once()
        self.assertEqual(log_mock.call_args.args[1], "approval.rejected")
        self.assertEqual(log_mock.call_args.kwargs["data"]["to_state"], "S4")

    def test_duplicate_reject_keeps_state_safe(self) -> None:
        db = _FakeDB()
        row = _session(state="S4", approval_required=True)
        file_row = _file()
        decision = {
            "state": "S4",
            "status_gate": "NEEDS_APPROVAL",
            "approval_required": True,
            "conflict_flags": ["approval_rejected"],
            "rule_explanations": ["already rejected"],
        }

        with patch.object(approval_routes, "_load_session", return_value=row), \
             patch.object(approval_routes, "_load_file_for_session", return_value=file_row), \
             patch.object(approval_routes, "_ensure_canonical_decision", return_value=decision), \
             patch.object(approval_routes, "upsert_orchestrator_session", return_value=row), \
             patch.object(approval_routes, "upsert_projection", return_value=None), \
             patch.object(approval_routes, "default_event_bus", return_value=_FakeBus()), \
             patch.object(approval_routes, "write_memory_payload", return_value="/tmp/reject.json"), \
             patch.object(approval_routes, "log_event", return_value=None):
            result = approval_routes.reject_session(
                "session-1",
                approval_routes.ApprovalActionIn(note=None),
                db=db,
                principal=_user(),
            )

        self.assertEqual(result.state, "S4")
        self.assertTrue(result.approval_required)
        _assert_no_private_locator(result.model_dump())

    def test_stale_session_file_lookup_fails_safely(self) -> None:
        db = _FakeDB()

        with patch.object(approval_routes, "_load_session", return_value=_session()), \
             patch.object(
                 approval_routes,
                 "_load_file_for_session",
                 side_effect=HTTPException(status_code=404, detail="File not found"),
             ):
            with self.assertRaises(HTTPException) as ctx:
                approval_routes.approve_session(
                    "session-1",
                    approval_routes.ApprovalActionIn(note=None),
                    db=db,
                    principal=_user(),
                )

        self.assertEqual(ctx.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
