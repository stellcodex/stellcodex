from __future__ import annotations

from app.core.engineering import (
    MODE_BREP,
    MODE_MESH_APPROX,
    MODE_VISUAL_ONLY,
    build_geometry_metrics_payload,
    normalize_geometry_mode,
)
from app.stellai.engineering.policy import library_status


def test_geometry_mode_normalization_matches_contract() -> None:
    assert normalize_geometry_mode("brep") == MODE_BREP
    assert normalize_geometry_mode("mesh_approx") == MODE_MESH_APPROX
    assert normalize_geometry_mode("visual_only") == MODE_VISUAL_ONLY
    assert normalize_geometry_mode("unexpected") == MODE_VISUAL_ONLY


def test_geometry_metrics_payload_builds_stable_contract_fields() -> None:
    payload = build_geometry_metrics_payload(
        file_id="sample",
        mode="brep",
        bbox={"size": [2.0, 3.0, 4.0]},
        volume=24.0,
        surface_area=52.0,
        part_count=1,
        triangle_count=None,
        source_type="brep_smoke",
        confidence=0.95,
    )

    assert payload["file_id"] == "sample"
    assert payload["mode"] == MODE_BREP
    assert payload["geometry_hash"]
    assert len(payload["geometry_hash"]) == 64


def test_library_status_reports_ocp_and_pythonocc_separately() -> None:
    status = library_status()

    assert "ocp" in status
    assert "pythonocc_core" in status
