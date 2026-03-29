#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import secrets
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

ROOT = Path("/root/workspace")
RUNS_DIR = ROOT / "_runs"
JOBS_DIR = ROOT / "_jobs"
ENV_FILE = Path("/srv/infra/runtime/infra.deploy.env")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso_now() -> str:
    return _now().isoformat()


def _load_env_file(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not path.is_file():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _run(cmd: List[str]) -> str:
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def _docker_ip(container: str) -> str:
    return _run(["docker", "inspect", "-f", "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}", container])


def _http_json(
    url: str,
    *,
    method: str = "GET",
    payload: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
) -> Tuple[int, Any]:
    data = None
    request_headers = {"Accept": "application/json"}
    if headers:
        request_headers.update(headers)
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        request_headers["Content-Type"] = "application/json"
    request = Request(url, data=data, headers=request_headers, method=method.upper())
    try:
        with urlopen(request, timeout=30) as response:
            raw = response.read()
            return response.status, json.loads(raw.decode("utf-8")) if raw else {}
    except HTTPError as exc:
        raw = exc.read()
        try:
            parsed = json.loads(raw.decode("utf-8")) if raw else {}
        except Exception:
            parsed = {"detail": raw.decode("utf-8", errors="ignore")}
        return exc.code, parsed
    except URLError as exc:
        return 599, {"detail": str(exc.reason)}


def _json_ready(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    return value


def _scx_id() -> str:
    return "scx_%s" % str(uuid4())


@dataclass
class Check:
    name: str
    ok: bool
    detail: Dict[str, Any]


def _check(results: List[Check], name: str, ok: bool, **detail: Any) -> None:
    results.append(Check(name=name, ok=ok, detail=_json_ready(detail)))


def _ensure_runtime_env() -> Dict[str, str]:
    env = _load_env_file(ENV_FILE)
    for key, value in env.items():
        os.environ.setdefault(key, value)
    password = env.get("POSTGRES_PASSWORD", "")
    postgres_ip = os.environ.get("V10_POSTGRES_IP") or _docker_ip("stellcodex-postgres")
    os.environ["DATABASE_URL"] = "postgresql+psycopg2://stellcodex:%s@%s:5432/stellcodex" % (password, postgres_ip)
    os.environ.setdefault("BOOTSTRAP_ADMIN_TOKEN", env.get("BOOTSTRAP_ADMIN_TOKEN", ""))
    return env


def _engine():
    return create_engine(os.environ["DATABASE_URL"], echo=False)


def _internal_headers(token: str) -> Dict[str, str]:
    return {"X-Internal-Token": token}


def _seed_ready_file(
    db: Session,
    *,
    project_id: str,
    original_filename: str,
    geometry_meta: Dict[str, Any],
    dfm_findings: Dict[str, Any],
    include_assembly_meta: bool,
    gltf_enabled: bool,
) -> str:
    file_id = _scx_id()
    meta = {
        "kind": "3d",
        "mode": "brep",
        "project_id": project_id,
        "rule_version": "v10.validation",
        "part_count": int(geometry_meta.get("part_count") or 1),
        "geometry_meta_json": geometry_meta,
        "dfm_findings": dfm_findings,
    }
    if include_assembly_meta:
        meta["assembly_meta_key"] = "validation/%s/assembly.json" % secrets.token_hex(8)

    db.execute(
        text(
            """
            INSERT INTO uploaded_files (
              file_id, owner_sub, tenant_id, owner_user_id, owner_anon_sub, is_anonymous, privacy,
              bucket, object_key, original_filename, content_type, size_bytes, sha256,
              gltf_key, thumbnail_key, folder_key, metadata, decision_json, status, visibility
            ) VALUES (
              :file_id, :owner_sub, :tenant_id, NULL, :owner_anon_sub, TRUE, 'private',
              :bucket, :object_key, :original_filename, :content_type, :size_bytes, :sha256,
              :gltf_key, NULL, :folder_key, CAST(:meta AS json), CAST(:decision_json AS jsonb), 'ready', 'private'
            )
            """
        ),
        {
            "file_id": file_id,
            "owner_sub": "v10-validation",
            "tenant_id": 1,
            "owner_anon_sub": "v10-validation",
            "bucket": "validation",
            "object_key": "validation/%s/original.step" % secrets.token_hex(8),
            "original_filename": original_filename,
            "content_type": "application/step",
            "size_bytes": 1024,
            "sha256": secrets.token_hex(32),
            "gltf_key": "validation/%s/preview.glb" % secrets.token_hex(8) if gltf_enabled else None,
            "folder_key": "project/%s/3d/brep" % project_id,
            "meta": json.dumps(meta, ensure_ascii=True),
            "decision_json": json.dumps({}, ensure_ascii=True),
        },
    )
    db.commit()
    return file_id


def _create_share(db: Session, *, file_id: str, expires_at: datetime) -> Dict[str, Any]:
    share_id = str(uuid4())
    token = secrets.token_hex(32)
    db.execute(
        text(
            """
            INSERT INTO shares (id, file_id, created_by_user_id, token, permission, expires_at, revoked_at, created_at)
            VALUES (CAST(:id AS uuid), :file_id, NULL, :token, 'view', :expires_at, NULL, :created_at)
            """
        ),
        {
            "id": share_id,
            "file_id": file_id,
            "token": token,
            "expires_at": expires_at.replace(tzinfo=None),
            "created_at": _now().replace(tzinfo=None),
        },
    )
    db.commit()
    return {"id": share_id, "token": token}


def _cleanup_validation(db: Session, *, file_ids: List[str]) -> None:
    if not file_ids:
        return
    case_ids = [
        row[0]
        for row in db.execute(
            text("SELECT case_id::text FROM ai_case_logs WHERE file_id = ANY(:file_ids)"),
            {"file_ids": file_ids},
        ).fetchall()
    ]
    similarity_keys = [
        row[0]
        for row in db.execute(
            text("SELECT DISTINCT similarity_index_key FROM ai_case_logs WHERE file_id = ANY(:file_ids)"),
            {"file_ids": file_ids},
        ).fetchall()
        if row[0]
    ]

    if case_ids:
        for table_name in ("ai_snapshot_jobs", "ai_eval_results", "solved_cases", "failed_cases", "blocked_cases", "recovered_cases"):
            db.execute(
                text("DELETE FROM %s WHERE case_id = ANY(CAST(:case_ids AS uuid[]))" % table_name),
                {"case_ids": case_ids},
            )
    if similarity_keys:
        db.execute(
            text("DELETE FROM ai_pattern_signals WHERE similarity_index_key = ANY(:similarity_keys)"),
            {"similarity_keys": similarity_keys},
        )
    db.execute(text("DELETE FROM ai_case_logs WHERE file_id = ANY(:file_ids)"), {"file_ids": file_ids})
    db.execute(text("DELETE FROM shares WHERE file_id = ANY(:file_ids)"), {"file_ids": file_ids})
    db.execute(text("DELETE FROM orchestrator_sessions WHERE file_id = ANY(:file_ids)"), {"file_ids": file_ids})
    db.execute(text("DELETE FROM uploaded_files WHERE file_id = ANY(:file_ids)"), {"file_ids": file_ids})
    db.commit()


def _query_row(db: Session, sql: str, **params: Any) -> Optional[Dict[str, Any]]:
    row = db.execute(text(sql), params).mappings().first()
    return dict(row) if row is not None else None


def _query_rows(db: Session, sql: str, **params: Any) -> List[Dict[str, Any]]:
    return [dict(row) for row in db.execute(text(sql), params).mappings().all()]


def run_final_execution(job: Optional[Dict[str, Any]] = None, *, invoked_by: str = "manual") -> Dict[str, Any]:
    env = _ensure_runtime_env()
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    (JOBS_DIR / "logs").mkdir(parents=True, exist_ok=True)

    token = os.environ.get("BOOTSTRAP_ADMIN_TOKEN", "")
    backend_ip = os.environ.get("V10_BACKEND_IP") or _docker_ip("stellcodex-backend")
    stellai_ip = os.environ.get("V10_STELLAI_IP") or _docker_ip("orchestra-stellai")
    orchestra_ip = os.environ.get("V10_ORCHESTRA_IP") or _docker_ip("orchestra-orchestrator")

    backend_base = "http://127.0.0.1:8000"
    backend_internal_base = "%s/api/v1/internal/runtime" % backend_base
    stellai_base = "http://%s:7020" % stellai_ip
    orchestra_base = "http://%s:7010" % orchestra_ip

    checks: List[Check] = []
    evidence: Dict[str, Any] = {
        "generated_at": _iso_now(),
        "invoked_by": invoked_by,
        "job": _json_ready(job or {}),
        "service_urls": {
            "backend": backend_base,
            "backend_internal": backend_internal_base,
            "backend_internal_ip": backend_ip,
            "stellai": stellai_base,
            "orchestra": orchestra_base,
        },
    }

    runtime_status, runtime_payload = _http_json("%s/api/v1/health" % backend_base)
    stell_status, stell_payload = _http_json("%s/health" % stellai_base)
    orch_status, orch_payload = _http_json("%s/health" % orchestra_base)
    listening = os.environ.get("V10_LISTENING_SNAPSHOT") or _run(["ss", "-ltnp"])
    containers = os.environ.get("V10_CONTAINER_LIST") or _run(["docker", "ps", "--format", "{{.Names}}"])
    backend_count = int(os.environ.get("V10_BACKEND_COUNT") or len([line for line in containers.splitlines() if line.strip() == "stellcodex-backend"]))

    _check(checks, "backend_health_ok", runtime_status == 200 and runtime_payload.get("status") == "ok", payload=runtime_payload)
    _check(checks, "stellai_health_ok", stell_status == 200 and stell_payload.get("status") == "OK", payload=stell_payload)
    _check(checks, "orchestra_health_ok", orch_status == 200 and orch_payload.get("status") == "OK", payload=orch_payload)
    _check(checks, "public_18000_absent", ":18000" not in listening, listening_excerpt="\n".join(line for line in listening.splitlines() if ":18000" in line))
    _check(checks, "single_backend_runtime", backend_count == 1, backend_count=backend_count, containers=containers.splitlines())

    knowledge_ingest_status, knowledge_ingest_payload = _http_json("%s/knowledge/ingest" % stellai_base, method="POST")
    knowledge_search_status, knowledge_search_payload = _http_json(
        "%s/knowledge/search" % stellai_base,
        method="POST",
        payload={"query": "thin wall dfm recovery rule", "max_results": 5},
    )
    knowledge_ready = (
        knowledge_ingest_status == 200
        and knowledge_ingest_payload.get("status") == "ok"
        and int(knowledge_ingest_payload.get("chunk_count") or 0) > 0
    )
    _check(checks, "knowledge_ingest_ready", knowledge_ready, ingest=knowledge_ingest_payload)
    _check(
        checks,
        "knowledge_search_ready",
        knowledge_search_status == 200 and isinstance(knowledge_search_payload.get("results"), list),
        payload=knowledge_search_payload,
    )

    project_suffix = secrets.token_hex(4)
    learning_project = "v10-learning-%s" % project_suffix
    approval_project = "v10-approval-%s" % project_suffix
    assembly_fail_project = "v10-assembly-fail-%s" % project_suffix

    learning_geometry = {"part_count": 2, "bbox": {"min_x": 0, "min_y": 0, "min_z": 0, "max_x": 12, "max_y": 8, "max_z": 4}}
    learning_dfm = {
        "status_gate": "BLOCK",
        "risk_flags": ["thin_wall"],
        "findings": [
            {
                "code": "THIN_WALL",
                "severity": "blocking",
                "message": "Thin wall detected; recovery input is required for stable machining.",
            }
        ],
    }
    approval_dfm = {
        "status_gate": "NEEDS_APPROVAL",
        "risk_flags": ["tooling_review"],
        "findings": [
            {
                "code": "TOOLING_REVIEW",
                "severity": "blocking",
                "message": "Deterministic manufacturing review required before release.",
            }
        ],
    }

    memory_evidence: Dict[str, Any] = {}
    retrieval_evidence: Dict[str, Any] = {}
    eval_evidence: Dict[str, Any] = {}
    orchestrator_evidence: Dict[str, Any] = {}

    with Session(_engine()) as db:
        learning_file_id = _seed_ready_file(
            db,
            project_id=learning_project,
            original_filename="v10_learning.step",
            geometry_meta=learning_geometry,
            dfm_findings=learning_dfm,
            include_assembly_meta=True,
            gltf_enabled=False,
        )
        approval_file_id = _seed_ready_file(
            db,
            project_id=approval_project,
            original_filename="v10_approval.step",
            geometry_meta={"part_count": 1, "bbox": {"min_x": 0, "min_y": 0, "min_z": 0, "max_x": 20, "max_y": 10, "max_z": 6}},
            dfm_findings=approval_dfm,
            include_assembly_meta=True,
            gltf_enabled=True,
        )
        assembly_fail_file_id = _seed_ready_file(
            db,
            project_id=assembly_fail_project,
            original_filename="v10_missing_assembly.step",
            geometry_meta={"part_count": 1, "bbox": {"min_x": 0, "min_y": 0, "min_z": 0, "max_x": 5, "max_y": 5, "max_z": 5}},
            dfm_findings=approval_dfm,
            include_assembly_meta=False,
            gltf_enabled=False,
        )
        file_ids = [learning_file_id, approval_file_id, assembly_fail_file_id]

        failure_results: List[Dict[str, Any]] = []
        for index in range(3):
            status_code, payload = _http_json(
                "%s/ai/cases/log" % backend_internal_base,
                method="POST",
                headers=_internal_headers(token),
                payload={
                    "file_id": learning_file_id,
                    "session_id": "v10-learning-failure-%s" % (index + 1),
                    "run_type": "v10_learning_validation",
                    "input_payload": {
                        "mode": "brep",
                        "retry_count": index,
                        "geometry_meta": learning_geometry,
                        "dfm_findings": learning_dfm,
                    },
                    "decision_output": {
                        "rule_version": "v10.validation",
                        "mode": "brep",
                        "confidence": 0.62,
                        "manufacturing_method": "cnc",
                        "rule_explanations": [
                            {
                                "rule_id": "THIN_WALL",
                                "triggered": True,
                                "severity": "HIGH",
                                "reference": "validation:thin_wall",
                                "reasoning": "Validation failure to bootstrap repeat-failure memory signal.",
                            }
                        ],
                        "conflict_flags": [],
                        "memory_context": {},
                        "memory_required_inputs": [],
                        "recommendations": ["Capture a recovery plan before retrying the same geometry."],
                    },
                    "execution_trace": [{"step": "validation.failure", "attempt": index + 1}],
                    "final_status": "failure",
                    "error_trace": {"type": "decision_error", "message": "stell.ai returned invalid decision"},
                    "duration_ms": 1200 - (index * 100),
                    "retrieved_context_summary": {},
                },
            )
            if status_code == 200 and isinstance(payload, dict):
                failure_results.append(payload)

        memory_ctx_status, memory_ctx_payload = _http_json(
            "%s/ai/memory/context" % backend_internal_base,
            method="POST",
            headers=_internal_headers(token),
            payload={
                "file_id": learning_file_id,
                "project_id": learning_project,
                "mode": "brep",
                "geometry_meta": learning_geometry,
                "dfm_findings": learning_dfm,
            },
        )
        _check(
            checks,
            "memory_context_populated",
            memory_ctx_status == 200
            and isinstance(memory_ctx_payload, dict)
            and len(memory_ctx_payload.get("top_similar_cases") or []) > 0
            and len(memory_ctx_payload.get("active_signals") or []) > 0,
            payload=memory_ctx_payload,
        )

        decide_status, decide_payload = _http_json(
            "%s/decide" % stellai_base,
            method="POST",
            payload={"file_id": learning_file_id},
        )
        retrieval_used = (
            decide_status == 200
            and isinstance(decide_payload.get("memory_context"), dict)
            and len(decide_payload.get("memory_context", {}).get("top_similar_cases") or []) > 0
            and "repeat_failure_guard" in (decide_payload.get("conflict_flags") or [])
        )
        _check(checks, "retrieval_changes_decision", retrieval_used, payload=decide_payload)
        _check(
            checks,
            "decision_contract_complete",
            decide_status == 200
            and bool(decide_payload.get("rule_version"))
            and bool(decide_payload.get("mode"))
            and decide_payload.get("confidence") is not None
            and bool(decide_payload.get("rule_explanations")),
            payload=decide_payload,
        )

        success_status, success_payload = _http_json(
            "%s/ai/cases/log" % backend_internal_base,
            method="POST",
            headers=_internal_headers(token),
            payload={
                "file_id": learning_file_id,
                "session_id": "v10-learning-success",
                "run_type": "v10_learning_validation",
                "input_payload": {
                    "mode": "brep",
                    "retry_count": 1,
                    "geometry_meta": learning_geometry,
                    "dfm_findings": learning_dfm,
                },
                "decision_output": decide_payload if isinstance(decide_payload, dict) else {},
                "execution_trace": [{"step": "validation.recovery_plan", "result": "submitted"}],
                "final_status": "success",
                "error_trace": None,
                "duration_ms": 640,
                "retrieved_context_summary": decide_payload.get("memory_context") if isinstance(decide_payload, dict) else {},
            },
        )
        success_case_id = str((success_payload or {}).get("case_id") or "")
        success_case = _query_row(
            db,
            """
            SELECT case_id::text AS case_id, case_type, retry_count, retrieved_context_summary
            FROM ai_case_logs
            WHERE case_id = CAST(:case_id AS uuid)
            """,
            case_id=success_case_id,
        )
        eval_row = _query_row(
            db,
            """
            SELECT case_id::text AS case_id, outcome, evaluation, resolution_seconds, success_rate, average_resolution_seconds
            FROM ai_eval_results
            WHERE case_id = CAST(:case_id AS uuid)
            """,
            case_id=success_case_id,
        )
        solved_exists = _query_row(
            db,
            "SELECT case_id::text AS case_id FROM solved_cases WHERE case_id = CAST(:case_id AS uuid)",
            case_id=success_case_id,
        )
        recovered_exists = _query_row(
            db,
            "SELECT case_id::text AS case_id FROM recovered_cases WHERE case_id = CAST(:case_id AS uuid)",
            case_id=success_case_id,
        )

        eval_payload = (eval_row or {}).get("evaluation") if isinstance((eval_row or {}).get("evaluation"), dict) else {}
        memory_written = bool(success_case and isinstance(success_case.get("retrieved_context_summary"), dict))
        eval_exists = bool(eval_row and {"success", "accuracy_score", "retry_used", "error_type", "improvement_flag"} <= set(eval_payload.keys()))
        improvement_observable = bool(eval_payload.get("improvement_flag")) and success_case is not None and success_case.get("case_type") == "recovery_case"
        _check(checks, "memory_written", memory_written, case_id=success_case_id)
        _check(checks, "eval_exists", eval_exists, evaluation=eval_payload)
        _check(checks, "improvement_observable", improvement_observable, evaluation=eval_payload)
        _check(checks, "memory_rows_written", solved_exists is not None and recovered_exists is not None, solved=bool(solved_exists), recovered=bool(recovered_exists))

        pattern_signals = _query_rows(
            db,
            """
            SELECT signal_id::text AS signal_id, signal_type, failure_class, signal_payload, similarity_index_key
            FROM ai_pattern_signals
            WHERE similarity_index_key = :similarity_index_key
            ORDER BY updated_at DESC, created_at DESC
            """,
            similarity_index_key=(success_payload or {}).get("similarity_index_key", ""),
        )

        assembly_fail_status, assembly_fail_payload = _http_json(
            "%s/files/sync" % orchestra_base,
            method="POST",
            payload={"file_id": assembly_fail_file_id},
        )
        _check(
            checks,
            "assembly_meta_fail_closed",
            assembly_fail_status == 409
            and isinstance(assembly_fail_payload.get("detail"), dict)
            and assembly_fail_payload["detail"].get("code") == "assembly_meta_missing",
            payload=assembly_fail_payload,
        )

        sync_status, sync_payload = _http_json(
            "%s/files/sync" % orchestra_base,
            method="POST",
            payload={"file_id": approval_file_id},
        )
        session_id = str(sync_payload.get("session_id") or "")
        decision_json = sync_payload.get("decision_json") if isinstance(sync_payload.get("decision_json"), dict) else {}
        deterministic_pipeline = (
            sync_status == 200
            and sync_payload.get("state") == "S5"
            and bool(sync_payload.get("approval_required"))
            and bool(decision_json)
            and bool(decision_json.get("rule_version"))
            and decision_json.get("confidence") is not None
            and bool(decision_json.get("rule_explanations"))
        )
        _check(checks, "orchestra_hits_s5_for_approval", deterministic_pipeline, payload=sync_payload)

        approve_status, approve_payload = _http_json(
            "%s/sessions/approve" % orchestra_base,
            method="POST",
            payload={"session_id": session_id, "reason": "Validation approval cleared"},
        )
        _check(checks, "approval_moves_to_s6", approve_status == 200 and approve_payload.get("state") == "S6", payload=approve_payload)

        share = _create_share(db, file_id=approval_file_id, expires_at=_now() + timedelta(minutes=15))
        share_sync_status, share_sync_payload = _http_json(
            "%s/files/sync" % orchestra_base,
            method="POST",
            payload={"file_id": approval_file_id},
        )
        _check(checks, "share_moves_to_s7", share_sync_status == 200 and share_sync_payload.get("state") == "S7", payload=share_sync_payload)

        share_status, share_payload = _http_json("%s/api/v1/share/%s" % (backend_base, share["token"]))
        safe_public_payload = share_status == 200 and "object_key" not in share_payload and "storage_key" not in share_payload and "bucket" not in share_payload
        _check(checks, "share_resolve_public_safe", safe_public_payload, payload=share_payload)

        db.execute(
            text("UPDATE shares SET expires_at = :expires_at WHERE id = CAST(:id AS uuid)"),
            {"expires_at": (_now() - timedelta(minutes=1)).replace(tzinfo=None), "id": share["id"]},
        )
        db.commit()
        expired_status, expired_payload = _http_json("%s/api/v1/share/%s" % (backend_base, share["token"]))
        _check(checks, "share_expiry_returns_410", expired_status == 410, payload=expired_payload)

        memory_evidence = {
            "failure_case_ids": [item.get("case_id") for item in failure_results if isinstance(item, dict)],
            "success_case_id": success_case_id,
            "success_case": success_case,
            "memory_context": memory_ctx_payload,
            "pattern_signals": pattern_signals,
        }
        retrieval_evidence = {
            "decision_status": decide_status,
            "decision_payload": decide_payload,
            "knowledge_ingest": knowledge_ingest_payload,
            "knowledge_search": knowledge_search_payload,
        }
        eval_evidence = {
            "case_id": success_case_id,
            "evaluation": eval_payload,
            "result": {
                "outcome": (eval_row or {}).get("outcome"),
                "resolution_seconds": (eval_row or {}).get("resolution_seconds"),
                "success_rate": (eval_row or {}).get("success_rate"),
                "average_resolution_seconds": (eval_row or {}).get("average_resolution_seconds"),
            },
        }
        orchestrator_evidence = {
            "approval_session_id": session_id,
            "state_sequence": [sync_payload.get("state"), approve_payload.get("state"), share_sync_payload.get("state")],
            "assembly_fail": {"status": assembly_fail_status, "payload": assembly_fail_payload},
            "share_resolve": {"status": share_status, "payload": share_payload},
            "share_expired": {"status": expired_status, "payload": expired_payload},
        }

        _cleanup_validation(db, file_ids=file_ids)

    evidence["checks"] = [{"name": item.name, "ok": item.ok, "detail": item.detail} for item in checks]
    evidence["memory"] = memory_evidence
    evidence["retrieval"] = retrieval_evidence
    evidence["eval"] = eval_evidence
    evidence["orchestrator"] = orchestrator_evidence

    critical_checks = {
        "backend_health_ok",
        "stellai_health_ok",
        "orchestra_health_ok",
        "public_18000_absent",
        "single_backend_runtime",
        "knowledge_ingest_ready",
        "retrieval_changes_decision",
        "decision_contract_complete",
        "memory_written",
        "eval_exists",
        "improvement_observable",
        "assembly_meta_fail_closed",
        "orchestra_hits_s5_for_approval",
        "approval_moves_to_s6",
        "share_moves_to_s7",
        "share_resolve_public_safe",
        "share_expiry_returns_410",
    }
    system_closed = all(item.ok for item in checks if item.name in critical_checks)
    evidence["system_closed"] = system_closed
    evidence["closure_rule"] = {
        "deterministic_pipeline_works": any(item.name == "orchestra_hits_s5_for_approval" and item.ok for item in checks),
        "memory_is_written": any(item.name == "memory_written" and item.ok for item in checks),
        "retrieval_affects_decisions": any(item.name == "retrieval_changes_decision" and item.ok for item in checks),
        "eval_exists": any(item.name == "eval_exists" and item.ok for item in checks),
        "improvement_is_observable": any(item.name == "improvement_observable" and item.ok for item in checks),
        "knowledge_ready": any(item.name == "knowledge_ingest_ready" and item.ok for item in checks),
    }

    (RUNS_DIR / "MEMORY_EVIDENCE.json").write_text(json.dumps(_json_ready(memory_evidence), ensure_ascii=True, indent=2), encoding="utf-8")
    (RUNS_DIR / "RETRIEVAL_EVIDENCE.json").write_text(json.dumps(_json_ready(retrieval_evidence), ensure_ascii=True, indent=2), encoding="utf-8")
    (RUNS_DIR / "EVAL_RESULTS.json").write_text(json.dumps(_json_ready(eval_evidence), ensure_ascii=True, indent=2), encoding="utf-8")

    final_report = [
        "# V10 Final System Report",
        "",
        "- Generated at: %s" % evidence["generated_at"],
        "- Invoked by: %s" % invoked_by,
        "- System closed: %s" % ("YES" if system_closed else "NO"),
        "",
        "## Runtime",
        "- Backend health: %s" % ("PASS" if runtime_status == 200 and runtime_payload.get("status") == "ok" else "FAIL"),
        "- STELL.AI health: %s" % ("PASS" if stell_status == 200 and stell_payload.get("status") == "OK" else "FAIL"),
        "- Orchestra health: %s" % ("PASS" if orch_status == 200 and orch_payload.get("status") == "OK" else "FAIL"),
        "- Public :18000 absent: %s" % ("PASS" if ":18000" not in listening else "FAIL"),
        "- Single backend runtime: %s" % ("PASS" if backend_count == 1 else "FAIL"),
        "",
        "## Closure Rule",
        "- Deterministic pipeline works: %s" % ("PASS" if evidence["closure_rule"]["deterministic_pipeline_works"] else "FAIL"),
        "- Memory is written: %s" % ("PASS" if evidence["closure_rule"]["memory_is_written"] else "FAIL"),
        "- Retrieval affects decisions: %s" % ("PASS" if evidence["closure_rule"]["retrieval_affects_decisions"] else "FAIL"),
        "- Eval exists: %s" % ("PASS" if evidence["closure_rule"]["eval_exists"] else "FAIL"),
        "- Improvement is observable: %s" % ("PASS" if evidence["closure_rule"]["improvement_is_observable"] else "FAIL"),
        "- Knowledge ready: %s" % ("PASS" if evidence["closure_rule"]["knowledge_ready"] else "FAIL"),
        "",
        "## Orchestration",
        "- Approval session state sequence: %s" % ", ".join(str(item) for item in orchestrator_evidence.get("state_sequence") or []),
        "- Share expiry returns 410: %s" % ("PASS" if any(item.name == "share_expiry_returns_410" and item.ok for item in checks) else "FAIL"),
        "",
        "## Outputs",
        "- MEMORY_EVIDENCE.json",
        "- RETRIEVAL_EVIDENCE.json",
        "- EVAL_RESULTS.json",
    ]
    (RUNS_DIR / "V10_FINAL_SYSTEM_REPORT.md").write_text("\n".join(final_report) + "\n", encoding="utf-8")

    learning_report = [
        "# STELL.AI Self-Learning Report",
        "",
        "- Generated at: %s" % evidence["generated_at"],
        "- Success case id: %s" % success_case_id,
        "- Improvement flag: %s" % eval_payload.get("improvement_flag"),
        "- Accuracy score: %s" % eval_payload.get("accuracy_score"),
        "- Retry used: %s" % eval_payload.get("retry_used"),
        "",
        "## Retrieval Effect",
        "- Top similar cases seen: %s" % len((decide_payload.get("memory_context") or {}).get("top_similar_cases") or []) if isinstance(decide_payload, dict) else 0,
        "- Active signals seen: %s" % len((decide_payload.get("memory_context") or {}).get("active_signals") or []) if isinstance(decide_payload, dict) else 0,
        "- Repeat failure guard active: %s" % ("PASS" if isinstance(decide_payload, dict) and "repeat_failure_guard" in (decide_payload.get("conflict_flags") or []) else "FAIL"),
        "",
        "## Learning Effect",
        "- Prior failures recorded: %s" % len(memory_evidence.get("failure_case_ids") or []),
        "- Retrieved context summary stored: %s" % ("PASS" if any(item.name == "memory_written" and item.ok for item in checks) else "FAIL"),
        "- Improvement observable: %s" % ("PASS" if improvement_observable else "FAIL"),
        "",
        "## Knowledge",
        "- Knowledge chunks indexed: %s" % knowledge_ingest_payload.get("chunk_count"),
        "- Knowledge search results: %s" % len(knowledge_search_payload.get("results") or []) if isinstance(knowledge_search_payload, dict) else 0,
    ]
    (RUNS_DIR / "STELLAI_SELF_LEARNING_REPORT.md").write_text("\n".join(learning_report) + "\n", encoding="utf-8")

    return evidence


def main() -> int:
    evidence = run_final_execution(job=None, invoked_by="manual")
    print(json.dumps({"system_closed": evidence["system_closed"], "generated_at": evidence["generated_at"]}, ensure_ascii=True))
    return 0 if evidence["system_closed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
