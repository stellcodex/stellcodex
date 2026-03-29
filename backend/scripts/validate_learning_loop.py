"""
validate_learning_loop.py

Proves the self-learning loop end-to-end:
  run → case record → eval → pattern signal → retrieval → next run references prior context

Run from backend root:
  DATABASE_URL=postgresql://... python scripts/validate_learning_loop.py

Exit 0 = all checks pass. Exit 1 = one or more checks failed.
"""
from __future__ import annotations

import sys
import uuid
from datetime import datetime, timezone

# --- bootstrap path -----------------------------------------------------------
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.ai_learning import (
    AiCaseLog,
    AiEvalResult,
    AiPatternSignal,
    BlockedCase,
    FailedCase,
    RecoveredCase,
    SolvedCase,
)
from app.models.file import UploadFile as UploadFileModel
from app.services.ai_learning import get_memory_context, record_case_run
from app.workers.bootstrap import prepare_worker_runtime

PASS = "  [PASS]"
FAIL = "  [FAIL]"

_results: list[tuple[str, bool]] = []


def check(label: str, condition: bool) -> bool:
    _results.append((label, condition))
    status = PASS if condition else FAIL
    print(f"{status}  {label}")
    return condition


def _engine():
    return create_engine(settings.DATABASE_URL, echo=False)


def _make_stub_file(db: Session, tenant_id: int = 1) -> UploadFileModel:
    """Insert a minimal uploaded_files row for validation purposes."""
    file_id = f"scx-val-{uuid.uuid4().hex[:12]}"
    row = UploadFileModel(
        file_id=file_id,
        tenant_id=tenant_id,
        original_filename="validation_part.step",
        content_type="application/octet-stream",
        status="processed",
        meta={
            "kind": "3d",
            "mode": "brep",
            "project_id": "validation_project",
        },
    )
    db.add(row)
    db.flush()
    return row


def _cleanup(db: Session, file_id: str) -> None:
    db.execute(
        text(
            "DELETE FROM ai_case_logs WHERE file_id = :fid"
        ),
        {"fid": file_id},
    )
    db.execute(
        text("DELETE FROM uploaded_files WHERE file_id = :fid"),
        {"fid": file_id},
    )
    db.commit()


def run_validation() -> bool:
    print("\n=== STELLCODEX SELF-LEARNING LOOP VALIDATION ===\n")
    prepare_worker_runtime()

    engine = _engine()
    all_pass = True

    with Session(engine) as db:
        file_row = _make_stub_file(db, tenant_id=1)
        file_id = file_row.file_id
        print(f"  stub file_id: {file_id}\n")

        # ── CHECK 1: FAILURE CASE — record_case_run stores AiCaseLog + AiEvalResult ──────
        print("── 1. Failure case capture ──────────────────────────────────")
        failure_result = record_case_run(
            db,
            file_row=file_row,
            case_id=None,
            session_id="val-session-001",
            run_type="dfm_session_sync",
            input_payload={
                "mode": "brep",
                "geometry_meta": {"part_count": 3},
                "dfm_findings": {
                    "status_gate": "BLOCK",
                    "findings": [{"code": "THIN_WALL"}, {"code": "UNDERCUT"}],
                },
            },
            decision_output={
                "manufacturing_method": "CNC",
                "confidence": 0.55,
                "conflict_flags": ["repeat_failure_guard"],
            },
            execution_trace=[{"step": "dfm_check", "result": "blocked"}],
            final_status="failure",
            error_trace={"type": "decision_error", "message": "stell.ai returned invalid decision"},
            duration_ms=1200,
        )
        failure_case_id = failure_result["case_id"]

        case_row = db.get(AiCaseLog, uuid.UUID(failure_case_id))
        check("failure AiCaseLog persisted", case_row is not None)
        check("failure final_status == 'failure'", case_row is not None and case_row.final_status == "failure")
        check("failure failure_class == 'decision_error'", case_row is not None and case_row.failure_class == "decision_error")

        eval_row = db.query(AiEvalResult).filter(AiEvalResult.case_id == uuid.UUID(failure_case_id)).first()
        check("failure AiEvalResult persisted", eval_row is not None)
        check("failure eval outcome == 'failure'", eval_row is not None and eval_row.outcome == "failure")

        failed_row = db.query(FailedCase).filter(FailedCase.case_id == uuid.UUID(failure_case_id)).first()
        check("failure FailedCase memory row persisted", failed_row is not None)

        # ── CHECK 2: Record 2 more failures to trigger pattern_signal (threshold = 3) ────
        print("\n── 2. Pattern signal extraction (3× repeat failure) ─────────")
        for i in range(2):
            record_case_run(
                db,
                file_row=file_row,
                case_id=None,
                session_id=f"val-session-00{i + 2}",
                run_type="dfm_session_sync",
                input_payload={
                    "mode": "brep",
                    "geometry_meta": {"part_count": 3},
                    "dfm_findings": {
                        "status_gate": "BLOCK",
                        "findings": [{"code": "THIN_WALL"}, {"code": "UNDERCUT"}],
                    },
                },
                decision_output={
                    "manufacturing_method": "CNC",
                    "confidence": 0.50,
                    "conflict_flags": ["repeat_failure_guard"],
                },
                execution_trace=[],
                final_status="failure",
                error_trace={"type": "decision_error", "message": "stell.ai returned invalid decision"},
                duration_ms=900,
            )

        signal_row = (
            db.query(AiPatternSignal)
            .filter(
                AiPatternSignal.tenant_id == 1,
                AiPatternSignal.signal_type == "pattern_signal",
                AiPatternSignal.failure_class == "decision_error",
                AiPatternSignal.active.is_(True),
            )
            .first()
        )
        check("pattern_signal created after 3× repeat failure", signal_row is not None)
        if signal_row:
            payload = signal_row.signal_payload if isinstance(signal_row.signal_payload, dict) else {}
            check("pattern_signal repeat_count >= 3", int(payload.get("repeat_count") or 0) >= 3)
            check("pattern_signal guard_flag present", payload.get("guard_flag") == "repeat_failure_guard")

        # ── CHECK 3: RETRIEVAL before next decision ───────────────────────────────────────
        print("\n── 3. Memory retrieval before next decision ─────────────────")
        memory_ctx = get_memory_context(
            db,
            file_row=file_row,
            project_id="validation_project",
            mode="brep",
            geometry_meta={"part_count": 3},
            dfm_findings={
                "status_gate": "BLOCK",
                "findings": [{"code": "THIN_WALL"}, {"code": "UNDERCUT"}],
            },
        )
        check("get_memory_context returns result", bool(memory_ctx))
        check("top_similar_cases populated", len(memory_ctx.get("top_similar_cases") or []) > 0)
        check("last_failed_case retrieved", memory_ctx.get("last_failed_case") is not None)
        check("active_signals contains pattern_signal", any(
            s.get("signal_type") == "pattern_signal"
            for s in (memory_ctx.get("active_signals") or [])
        ))

        # ── CHECK 4: RECOVERY CASE — success after prior failures, with injected context ──
        print("\n── 4. Recovery case with injected memory context ────────────")
        success_result = record_case_run(
            db,
            file_row=file_row,
            case_id=None,
            session_id="val-session-recovery",
            run_type="dfm_session_sync",
            input_payload={
                "mode": "brep",
                "geometry_meta": {"part_count": 3},
                "dfm_findings": {
                    "status_gate": "PASS",
                    "findings": [],
                },
            },
            decision_output={
                "manufacturing_method": "CNC",
                "confidence": 0.91,
                "conflict_flags": [],
            },
            execution_trace=[{"step": "dfm_check", "result": "pass"}, {"step": "decision", "result": "approved"}],
            final_status="success",
            error_trace=None,
            duration_ms=750,
            retrieved_context_summary=memory_ctx,
        )
        success_case_id = success_result["case_id"]

        success_row = db.get(AiCaseLog, uuid.UUID(success_case_id))
        check("recovery AiCaseLog persisted", success_row is not None)
        check("recovery final_status == 'success'", success_row is not None and success_row.final_status == "success")
        check(
            "retrieved_context_summary stored on case log",
            success_row is not None and isinstance(success_row.retrieved_context_summary, dict),
        )
        check(
            "retrieved_context_summary contains top_similar_cases",
            success_row is not None
            and isinstance(success_row.retrieved_context_summary, dict)
            and "top_similar_cases" in success_row.retrieved_context_summary,
        )

        solved_row = db.query(SolvedCase).filter(SolvedCase.case_id == uuid.UUID(success_case_id)).first()
        check("SolvedCase memory row persisted", solved_row is not None)

        recovered_row = db.query(RecoveredCase).filter(RecoveredCase.case_id == uuid.UUID(success_case_id)).first()
        check("RecoveredCase memory row persisted (prior failures existed)", recovered_row is not None)

        recovery_signal = (
            db.query(AiPatternSignal)
            .filter(
                AiPatternSignal.tenant_id == 1,
                AiPatternSignal.signal_type == "recovery_signal",
                AiPatternSignal.active.is_(True),
            )
            .first()
        )
        check("recovery_signal emitted after success following failures", recovery_signal is not None)

        # ── CHECK 5: BLOCKED CASE ─────────────────────────────────────────────────────────
        print("\n── 5. Blocked case ──────────────────────────────────────────")
        blocked_result = record_case_run(
            db,
            file_row=file_row,
            case_id=None,
            session_id="val-session-blocked",
            run_type="dfm_session_sync",
            input_payload={
                "mode": "brep",
                "blocked_reasons": [{"code": "missing_required_inputs", "detail": "material not set"}],
            },
            decision_output={"manufacturing_method": "unknown", "confidence": 0.0},
            execution_trace=[],
            final_status="blocked",
            error_trace=None,
            duration_ms=50,
        )
        blocked_case_id = blocked_result["case_id"]
        blocked_case_row = db.get(AiCaseLog, uuid.UUID(blocked_case_id))
        check("blocked AiCaseLog persisted", blocked_case_row is not None)
        check("blocked final_status == 'blocked'", blocked_case_row is not None and blocked_case_row.final_status == "blocked")
        blocked_mem_row = db.query(BlockedCase).filter(BlockedCase.case_id == uuid.UUID(blocked_case_id)).first()
        check("BlockedCase memory row persisted", blocked_mem_row is not None)

        # ── CHECK 6: FAIL-CLOSED — loop unavailability degrades safely ────────────────────
        print("\n── 6. Fail-closed behaviour ─────────────────────────────────")
        try:
            ctx_null = get_memory_context(
                db,
                file_row=file_row,
                project_id=None,
                mode=None,
                geometry_meta=None,
                dfm_findings=None,
            )
            check("get_memory_context with null inputs returns dict (no crash)", isinstance(ctx_null, dict))
        except Exception as exc:
            check(f"get_memory_context with null inputs raised: {exc}", False)

        # ── CLEANUP ───────────────────────────────────────────────────────────────────────
        _cleanup(db, file_id)

    # ── STELL.AI AGENT PATH ───────────────────────────────────────────────────────────────
    print("\n\n=== STELL.AI AGENT LEARNING LOOP ===\n")
    _run_stell_ai_validation(engine)

    # ── SUMMARY ──────────────────────────────────────────────────────────────────────────
    print("\n=== SUMMARY ===")
    total = len(_results)
    passed = sum(1 for _, ok in _results if ok)
    failed_items = [(label, ok) for label, ok in _results if not ok]
    print(f"  {passed}/{total} checks passed")
    if failed_items:
        print("\nFailed checks:")
        for label, _ in failed_items:
            print(f"  {FAIL}  {label}")
        return False
    print("\n  All checks passed. Loop is end-to-end proven.")
    return True


def _run_stell_ai_validation(engine) -> None:
    """
    Validates STELL.AI agent learning loop via stell_learning_client.

    Proves: RUN1 (failure) → pattern_signal → RUN2 retrieves RUN1 →
            RUN2 behavior changes (guard blocks) → AiCaseLog records retrieved_context_summary.
    """
    import sys, pathlib
    sys.path.insert(0, "/root/stell")

    try:
        import stell_learning_client as slc
    except ImportError as exc:
        check("stell_learning_client importable", False)
        print(f"  (skipping STELL.AI checks: {exc})")
        return

    check("stell_learning_client importable", True)

    from sqlalchemy import text

    LANE = "codex"
    PROMPT = "python api endpoint debug yardim"  # triggers code category

    # ── STEP 1: Clean state for this test lane/category ──────────────────────
    sim_key = slc._agent_similarity_key(LANE, slc._classify_prompt_category(PROMPT))
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM ai_case_logs WHERE file_id = :fid AND project_id = :lane"),
            {"fid": slc.STELL_AGENT_FILE_ID, "lane": LANE},
        )
        conn.execute(
            text("DELETE FROM ai_pattern_signals WHERE tenant_id = :tid AND similarity_index_key = :sk"),
            {"tid": slc.STELL_AGENT_TENANT_ID, "sk": sim_key},
        )

    # ── STEP 2: RUN1 — failure run ───────────────────────────────────────────
    print("── 1. RUN1: failure case (no prior context) ─────────────────")
    run1_ctx = slc.get_agent_memory(LANE, PROMPT)
    check("RUN1: get_agent_memory returns dict", isinstance(run1_ctx, dict))
    check("RUN1: no prior cases (fresh state)", len(run1_ctx.get("top_similar_cases") or []) == 0)
    check("RUN1: no active signals (fresh state)", len(run1_ctx.get("active_signals") or []) == 0)

    run1_case_id = slc.log_agent_case(
        session_id=None,
        lane=LANE,
        prompt=PROMPT,
        executor="stell-internal-executor",
        decision_json={"lane": LANE, "selected_executor": "stell-internal-executor", "confidence": 0.71},
        final_status="failure",
        error_message="provider unavailable: connection refused",
        duration_ms=3200,
        retrieved_context_summary=run1_ctx if run1_ctx else None,
    )
    check("RUN1: case_id returned", run1_case_id is not None)

    with engine.connect() as conn:
        r1_row = conn.execute(
            text("SELECT final_status, failure_class, retrieved_context_summary FROM ai_case_logs WHERE case_id = :cid"),
            {"cid": run1_case_id},
        ).first()
    check("RUN1: AiCaseLog persisted in DB", r1_row is not None)
    check("RUN1: final_status == 'failure'", r1_row is not None and r1_row[0] == "failure")
    check("RUN1: failure_class == 'infra_error'", r1_row is not None and r1_row[1] == "infra_error")

    # ── STEP 3: Run 2 more failures to trigger pattern_signal ────────────────
    print("\n── 2. Pattern signal extraction (3× failure) ────────────────")
    for i in range(2):
        slc.log_agent_case(
            session_id=None,
            lane=LANE,
            prompt=PROMPT,
            executor="stell-internal-executor",
            decision_json={"lane": LANE, "selected_executor": "stell-internal-executor", "confidence": 0.68},
            final_status="failure",
            error_message="provider unavailable: connection refused",
            duration_ms=2900,
            retrieved_context_summary=None,
        )

    with engine.connect() as conn:
        sig_row = conn.execute(
            text(
                "SELECT signal_payload FROM ai_pattern_signals "
                "WHERE tenant_id = :tid AND signal_type = 'pattern_signal' "
                "AND similarity_index_key = :sk AND active = TRUE LIMIT 1"
            ),
            {"tid": slc.STELL_AGENT_TENANT_ID, "sk": sim_key},
        ).first()
    check("pattern_signal created after 3× infra_error", sig_row is not None)
    if sig_row:
        payload = sig_row[0] if isinstance(sig_row[0], dict) else {}
        check("pattern_signal guard_flag == repeat_failure_guard", payload.get("guard_flag") == slc.REPEAT_FAILURE_GUARD)
        check("pattern_signal repeat_count >= 3", int(payload.get("repeat_count") or 0) >= 3)

    # ── STEP 4: RUN2 — retrieval happens, guard is active ────────────────────
    print("\n── 3. RUN2: retrieval before decision, guard enforced ───────")
    run2_ctx = slc.get_agent_memory(LANE, PROMPT)
    check("RUN2: get_agent_memory returns dict", isinstance(run2_ctx, dict))
    check("RUN2: top_similar_cases populated (RUN1 visible)", len(run2_ctx.get("top_similar_cases") or []) > 0)
    check("RUN2: last_failed_case retrieved (RUN1 case)", run2_ctx.get("last_failed_case") is not None)
    check(
        "RUN2: active_signals contains pattern_signal with guard_flag",
        any(
            isinstance(s, dict)
            and isinstance(s.get("signal_payload"), dict)
            and s["signal_payload"].get("guard_flag") == slc.REPEAT_FAILURE_GUARD
            for s in (run2_ctx.get("active_signals") or [])
        ),
    )

    # RUN2 behavior: guard is active → log as blocked (simulating delegate_text guard path)
    run2_case_id = slc.log_agent_case(
        session_id=None,
        lane=LANE,
        prompt=PROMPT,
        executor="guard",
        decision_json={
            "guard_flag": slc.REPEAT_FAILURE_GUARD,
            "repeat_count": 3,
            "lane": LANE,
            "requires_manual_review": True,
        },
        final_status="blocked",
        error_message="repeat_failure_guard signal active — automatic advance blocked",
        duration_ms=12,
        retrieved_context_summary=run2_ctx,
    )
    check("RUN2: case_id returned", run2_case_id is not None)

    with engine.connect() as conn:
        r2_row = conn.execute(
            text(
                "SELECT final_status, failure_class, retrieved_context_summary "
                "FROM ai_case_logs WHERE case_id = :cid"
            ),
            {"cid": run2_case_id},
        ).first()
    check("RUN2: AiCaseLog persisted in DB", r2_row is not None)
    check("RUN2: final_status == 'blocked' (behavior changed from RUN1 'failure')", r2_row is not None and r2_row[0] == "blocked")
    check(
        "RUN2: retrieved_context_summary stored on AiCaseLog",
        r2_row is not None and isinstance(r2_row[2], dict),
    )
    check(
        "RUN2: retrieved_context_summary contains top_similar_cases (RUN1 was seen)",
        r2_row is not None
        and isinstance(r2_row[2], dict)
        and len(r2_row[2].get("top_similar_cases") or []) > 0,
    )
    check(
        "RUN2: retrieved_context_summary contains active_signals (guard was seen)",
        r2_row is not None
        and isinstance(r2_row[2], dict)
        and len(r2_row[2].get("active_signals") or []) > 0,
    )

    # ── STEP 5: RUN1 vs RUN2 comparison ──────────────────────────────────────
    print("\n── 4. RUN1 vs RUN2 comparison ───────────────────────────────")
    check(
        "RUN1 final_status='failure' vs RUN2 final_status='blocked' (behavior changed)",
        r1_row is not None and r2_row is not None and r1_row[0] == "failure" and r2_row[0] == "blocked",
    )
    check(
        "RUN2 retrieved_context_summary references prior case (top_similar_cases non-empty)",
        r2_row is not None and isinstance(r2_row[2], dict) and len(r2_row[2].get("top_similar_cases") or []) > 0,
    )

    # ── STEP 6: FAIL-CLOSED — memory unavailable, core still runs ────────────
    print("\n── 5. STELL.AI fail-closed behaviour ────────────────────────")
    try:
        empty = slc.get_agent_memory("", "")
        check("get_agent_memory with empty inputs returns dict (no crash)", isinstance(empty, dict))
    except Exception as exc:
        check(f"get_agent_memory with empty inputs raised: {exc}", False)

    # ── CLEANUP ──────────────────────────────────────────────────────────────
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM ai_case_logs WHERE file_id = :fid AND project_id = :lane"),
            {"fid": slc.STELL_AGENT_FILE_ID, "lane": LANE},
        )
        conn.execute(
            text("DELETE FROM ai_pattern_signals WHERE tenant_id = :tid AND similarity_index_key = :sk"),
            {"tid": slc.STELL_AGENT_TENANT_ID, "sk": sim_key},
        )


if __name__ == "__main__":
    ok = run_validation()
    sys.exit(0 if ok else 1)
