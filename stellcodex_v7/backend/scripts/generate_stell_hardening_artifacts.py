from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from app.core.identity.stell_identity import ENGINEERING_ASYNC_ACCEPTED_TEXT, RESPONSE_BLOCKED_TEXT
from app.core.runtime.response_guard import build_safe_runtime_payload, dump_guard_scan
from app.stellai.channel_runtime import execute_channel_runtime
from app.stellai.engineering.policy import engineering_support_matrix, library_status
from app.stellai.types import RuntimeContext, RuntimeRequest


ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = ROOT / "stellcodex_v7" / "backend"

IDENTITY_SCAN_FILES = (
    BACKEND_ROOT / "app" / "api" / "v1" / "routes" / "stell.py",
    BACKEND_ROOT / "app" / "api" / "v1" / "routes" / "stell_ai.py",
    BACKEND_ROOT / "app" / "api" / "v1" / "routes" / "whatsapp.py",
    BACKEND_ROOT / "app" / "stellai" / "channel_runtime.py",
    BACKEND_ROOT / "app" / "stellai" / "runtime.py",
    ROOT / "scripts" / "stell_rpc_bridge.py",
)
IDENTITY_TERMS = ("Codex", "GPT", "AI assistant", "generic assistant", "assistant")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _scan_identity_leaks() -> dict[str, Any]:
    hits: list[dict[str, Any]] = []
    for path in IDENTITY_SCAN_FILES:
        if not path.exists():
            continue
        for line_no, line in enumerate(_load_text(path).splitlines(), start=1):
            if "re.compile(" in line:
                continue
            if any(term in line for term in IDENTITY_TERMS):
                hits.append({"file": str(path.relative_to(ROOT)), "line": line_no, "content": line.strip()})
    return {
        "scan_scope": [str(path.relative_to(ROOT)) for path in IDENTITY_SCAN_FILES if path.exists()],
        "identity_leakage_count": len(hits),
        "hits": hits,
        "pass": len(hits) == 0,
    }


def _runtime_binding_proof() -> dict[str, Any]:
    whatsapp_route = _load_text(BACKEND_ROOT / "app" / "api" / "v1" / "routes" / "whatsapp.py")
    admin_route = _load_text(BACKEND_ROOT / "app" / "api" / "v1" / "routes" / "stell.py")
    rpc_bridge = _load_text(ROOT / "scripts" / "stell_rpc_bridge.py")

    checks = {
        "whatsapp_route_uses_channel_runtime": "execute_channel_runtime(" in whatsapp_route,
        "admin_route_uses_channel_runtime": "execute_channel_runtime(" in admin_route,
        "legacy_bridge_uses_channel_runtime": "execute_channel_runtime(" in rpc_bridge,
        "legacy_bridge_external_brain_removed": "stell_brain.py" not in rpc_bridge,
        "legacy_bridge_subprocess_removed": "subprocess.run" not in rpc_bridge,
    }
    return {"checks": checks, "pass": all(checks.values())}


def _whatsapp_flow_proof() -> dict[str, Any]:
    whatsapp_route = _load_text(BACKEND_ROOT / "app" / "api" / "v1" / "routes" / "whatsapp.py")
    channel_runtime = _load_text(BACKEND_ROOT / "app" / "stellai" / "channel_runtime.py")
    message_mode = _load_text(BACKEND_ROOT / "app" / "core" / "runtime" / "message_mode.py")
    response_guard = _load_text(BACKEND_ROOT / "app" / "core" / "runtime" / "response_guard.py")

    checks = {
        "webhook_normalizer_present": "normalize_whatsapp_payload" in whatsapp_route,
        "runtime_entrypoint_present": "execute_channel_runtime(" in whatsapp_route,
        "mode_router_present": "detect_mode(" in channel_runtime and "MessageMode" in message_mode,
        "async_dispatch_boundary_present": "_should_dispatch_engineering_async" in channel_runtime,
        "response_guard_present": "build_safe_runtime_payload" in channel_runtime and "guard_text_or_default" in channel_runtime,
        "webhook_error_body_sanitized": 'return WhatsAppWebhookOut(status="error"' in whatsapp_route,
    }
    return {
        "flow": [
            "whatsapp_webhook",
            "normalize_whatsapp_payload",
            "execute_channel_runtime",
            "detect_mode",
            "tool_or_async_dispatch",
            "response_guard",
        ],
        "checks": checks,
        "pass": all(checks.values()),
    }


def _can_import(name: str) -> dict[str, Any]:
    spec = importlib.util.find_spec(name)
    if spec is None:
        return {"available": False, "imported": False}
    proc = subprocess.run(
        [sys.executable, "-c", f"import {name}"],
        capture_output=True,
        text=True,
    )
    result: dict[str, Any] = {"available": True, "imported": proc.returncode == 0}
    if proc.returncode != 0:
        result["return_code"] = proc.returncode
        stderr = (proc.stderr or "").strip()
        if stderr:
            result["stderr"] = stderr.splitlines()[-1]
    return result


def _library_install_report() -> dict[str, Any]:
    smoke = {
        "trimesh": _can_import("trimesh"),
        "open3d": _can_import("open3d"),
        "numpy": _can_import("numpy"),
        "scipy": _can_import("scipy"),
        "shapely": _can_import("shapely"),
        "networkx": _can_import("networkx"),
        "meshio": _can_import("meshio"),
        "pyvista": _can_import("pyvista"),
        "cadquery": _can_import("cadquery"),
        "OCC": _can_import("OCC"),
    }
    combined_smoke_ok = all(
        item["imported"]
        for name, item in smoke.items()
        if name in {"trimesh", "open3d", "numpy", "scipy", "shapely", "networkx", "meshio", "pyvista"}
    )
    return {
        "requirements_file": str((BACKEND_ROOT / "requirements-engineering.txt").relative_to(ROOT)),
        "occ_requirements_file": str((BACKEND_ROOT / "requirements-engineering-occ.txt").relative_to(ROOT)),
        "libraries": library_status(),
        "smoke": smoke,
        "mesh_stack_smoke_pass": combined_smoke_ok,
        "cadquery_smoke_pass": bool(smoke["cadquery"]["imported"]),
        "occ_smoke_pass": bool(smoke["OCC"]["imported"]),
    }


def _response_guard_proof() -> dict[str, Any]:
    sample_scan = dump_guard_scan(
        {
            "reply": "I am Codex on /api/v1/private with bucket=s3://secret",
            "bucket": "private-bucket",
            "path": "/root/workspace/private.txt",
        }
    )
    safe_payload = build_safe_runtime_payload(
        session_id="sess-guard",
        trace_id="trace-guard",
        message="status",
        reply="GPT RuntimeError /root/private",
        issue="response_guard_proof",
        mode="SYSTEM_STATUS",
    )
    passed = (
        sample_scan["forbidden_detected"] is True
        and sample_scan["forbidden_remaining"] is False
        and safe_payload["reply"] == RESPONSE_BLOCKED_TEXT
    )
    return {
        "sample_scan": sample_scan,
        "safe_payload_reply": safe_payload["reply"],
        "pass": passed,
    }


def _context() -> RuntimeContext:
    return RuntimeContext(
        tenant_id="tenant-proof",
        project_id="whatsapp",
        principal_type="whatsapp",
        principal_id="whatsapp:+905551112233",
        session_id="sess-proof",
        trace_id="trace-proof",
        file_ids=("scx_11111111-1111-1111-1111-111111111111",),
        allowed_tools=frozenset(),
    )


def _async_dispatch_proof() -> dict[str, Any]:
    import app.workers.tasks as tasks

    original = tasks.enqueue_engineering_analysis
    observed: dict[str, Any] = {}

    def fake_enqueue(file_id: str) -> str:
        observed["file_id"] = file_id
        return "job-proof-123"

    class _ExplodingRuntime:
        def run(self, *, request, db=None):
            raise AssertionError("sync runtime path should not execute for heavy whatsapp engineering work")

    tasks.enqueue_engineering_analysis = fake_enqueue
    try:
        outcome = execute_channel_runtime(
            request=RuntimeRequest(message="analyze mesh volume and dfm", context=_context(), top_k=4),
            db=None,
            runtime=_ExplodingRuntime(),
            channel="whatsapp",
        )
    finally:
        tasks.enqueue_engineering_analysis = original

    return {
        "reply": outcome.reply,
        "job_id": outcome.job_id,
        "observed_file_id": observed.get("file_id"),
        "status_lookup_contract": "existing_job_status_route",
        "pass": outcome.reply == ENGINEERING_ASYNC_ACCEPTED_TEXT and outcome.job_id == "job-proof-123",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate locked STELL runtime hardening evidence artifacts.")
    parser.add_argument("--evidence-dir", default="/root/workspace/evidence/stell_runtime_hardening_v3")
    args = parser.parse_args()

    evidence_dir = Path(args.evidence_dir).resolve()
    evidence_dir.mkdir(parents=True, exist_ok=True)

    artifacts = {
        "identity_leak_scan_report.json": _scan_identity_leaks(),
        "runtime_binding_proof.json": _runtime_binding_proof(),
        "whatsapp_flow_proof.json": _whatsapp_flow_proof(),
        "library_install_report.json": _library_install_report(),
        "engineering_support_matrix.json": engineering_support_matrix(),
        "response_guard_proof.json": _response_guard_proof(),
        "async_dispatch_proof.json": _async_dispatch_proof(),
    }
    for name, payload in artifacts.items():
        _write_json(evidence_dir / name, payload)

    _write_json(
        evidence_dir / "generation_summary.json",
        {
            "evidence_dir": str(evidence_dir),
            "artifacts": sorted(artifacts.keys()),
            "pass": all(bool(payload.get("pass", True)) for payload in artifacts.values()),
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
