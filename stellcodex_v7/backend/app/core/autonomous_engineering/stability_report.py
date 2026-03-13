"""V10 engineering capability report generation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.core.autonomous_engineering.knowledge_base import load_default_knowledge_base
from app.stellai.engineering.policy import occ_available


def build_v10_engineering_report(
    *,
    system_health: str,
    tests_passed: int,
    tests_total: int,
    gate_status: str,
    evidence_artifacts: list[str] | None = None,
    degraded_features: list[str] | None = None,
) -> dict[str, Any]:
    knowledge_diagnostics = load_default_knowledge_base().diagnostics()
    effective_degraded = list(degraded_features or [])
    if not occ_available():
        effective_degraded.append("brep_occ_path_unavailable")
    if knowledge_diagnostics.get("vector_provider") != "chroma":
        effective_degraded.append("vector_store_fallback_active")
    return {
        "system_health": str(system_health),
        "engineering_capabilities": {
            "design_interpreter": "enabled",
            "manufacturing_planner": "enabled",
            "process_simulation": "enabled",
            "cost_optimizer": "enabled",
            "design_optimizer": "enabled",
            "decision_synthesis": "enabled",
            "knowledge_base": knowledge_diagnostics,
        },
        "manufacturing_planning_status": {
            "status": "enabled",
            "workflow": "deterministic_async_ready",
            "gate_status": str(gate_status),
        },
        "cost_estimation_accuracy": {
            "status": "deterministic_baseline",
            "method": "rule_based_cost_model",
            "currency": "EUR",
        },
        "test_coverage": {
            "tests_passed": int(tests_passed),
            "tests_total": int(tests_total),
            "status": "pass" if int(tests_passed) == int(tests_total) else "partial",
        },
        "degraded_features": list(dict.fromkeys(effective_degraded)),
        "evidence_artifacts": list(evidence_artifacts or []),
    }


def write_v10_engineering_report(
    *,
    output_path: str | Path,
    system_health: str,
    tests_passed: int,
    tests_total: int,
    gate_status: str,
    evidence_artifacts: list[str] | None = None,
    degraded_features: list[str] | None = None,
) -> dict[str, Any]:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = build_v10_engineering_report(
        system_health=system_health,
        tests_passed=tests_passed,
        tests_total=tests_total,
        gate_status=gate_status,
        evidence_artifacts=evidence_artifacts,
        degraded_features=degraded_features,
    )
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return payload
