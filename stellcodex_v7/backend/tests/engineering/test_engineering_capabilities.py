from __future__ import annotations

from pathlib import Path

from app.core.identity.stell_identity import ENGINEERING_ASYNC_ACCEPTED_TEXT
from app.stellai.channel_runtime import execute_channel_runtime
from app.stellai.engineering.analysis import analyze_file
from app.stellai.engineering.policy import detect_engineering_capability, engineering_support_matrix
from app.stellai.types import RuntimeContext, RuntimeRequest


def _context(*, file_ids: tuple[str, ...] = ()) -> RuntimeContext:
    return RuntimeContext(
        tenant_id="tenant-1",
        project_id="proj-1",
        principal_type="whatsapp",
        principal_id="whatsapp:+905551112233",
        session_id="sess-1",
        trace_id="trace-1",
        file_ids=file_ids,
        allowed_tools=frozenset(),
    )


def test_engineering_support_matrix_reports_truthful_capabilities() -> None:
    matrix = engineering_support_matrix()
    by_ext = {row["ext"]: row for row in matrix["formats"]}

    assert by_ext["stl"]["mode"] == "mesh_approx"
    assert by_ext["gltf"]["capability_status"] == "preview_only"
    assert by_ext["x_t"]["capability_status"] == "unsupported"
    if not matrix["occ_enabled"]:
        assert by_ext["step"]["capability_status"] == "limited_without_occ"


def test_unsupported_parasolid_claim_is_truthful() -> None:
    payload = detect_engineering_capability("part.x_t", occ_enabled=False)

    assert payload["mode"] == "unsupported"
    assert payload["capability_status"] == "unsupported"
    assert payload["confidence"] == 0.0
    assert payload["unavailable_reason"]


def test_mesh_analysis_reports_mesh_approx_mode(tmp_path: Path) -> None:
    mesh_path = tmp_path / "part.stl"
    mesh_path.write_text(
        "\n".join(
            [
                "solid part",
                "facet normal 0 0 1",
                "  outer loop",
                "    vertex 0 0 0",
                "    vertex 1 0 0",
                "    vertex 0 1 0",
                "  endloop",
                "endfacet",
                "endsolid part",
            ]
        ),
        encoding="utf-8",
    )

    result = analyze_file(
        file_id="scx_11111111-1111-1111-1111-111111111111",
        filename="part.stl",
        size_bytes=mesh_path.stat().st_size,
        local_path=mesh_path,
    )

    assert result["mode"] == "mesh_approx"
    assert result["capability_status"] == "supported"
    assert result["surface_area"] is not None
    assert result["bounding_box"] is not None
    assert result["geometry_metrics"]["mode"] == "MESH_APPROX"
    assert result["geometry_metrics"]["geometry_hash"]
    assert result["feature_map"]["mode"] == "MESH_APPROX"
    assert "holes" in result["feature_map"]["features"]
    assert result["recommended_process"] in {"cnc_machining", "3d_printing", "unknown"}
    assert result["manufacturing_decision"]["rule_version"]
    assert result["manufacturing_plan"]["recommended_process"] == result["recommended_process"]
    assert result["cost_estimate"]["recommended_process"] == result["recommended_process"]
    assert result["cost_estimate"]["estimated_unit_cost"] is not None
    assert result["dfm_report"]["manufacturing_recommendation"]["recommended_process"] == result["recommended_process"]
    assert result["engineering_report"]["manufacturing_recommendation"]["recommended_process"] == result["recommended_process"]
    assert result["engineering_report"]["report_hash"]


def test_heavy_whatsapp_engineering_request_dispatches_async(monkeypatch) -> None:
    observed: dict[str, object] = {}

    def fake_enqueue(file_id: str) -> str:
        observed["file_id"] = file_id
        return "job-123"

    class _ExplodingRuntime:
        def run(self, *, request, db=None):
            raise AssertionError("runtime should not execute synchronous heavy analysis")

    monkeypatch.setattr("app.workers.tasks.enqueue_engineering_analysis", fake_enqueue)

    request = RuntimeRequest(
        message="analyze mesh volume and dfm",
        context=_context(file_ids=("scx_11111111-1111-1111-1111-111111111111",)),
        top_k=4,
    )

    outcome = execute_channel_runtime(request=request, db=None, runtime=_ExplodingRuntime(), channel="whatsapp")

    assert outcome.reply == ENGINEERING_ASYNC_ACCEPTED_TEXT
    assert outcome.job_id == "job-123"
    assert observed["file_id"] == "scx_11111111-1111-1111-1111-111111111111"
