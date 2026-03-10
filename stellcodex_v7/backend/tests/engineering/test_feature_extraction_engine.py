from __future__ import annotations

from app.core.engineering import MODE_BREP, MODE_VISUAL_ONLY, build_feature_map, build_runtime_geometry_metrics


def test_feature_map_uses_brep_signals_for_holes_threads_and_drafts() -> None:
    geometry_metrics = build_runtime_geometry_metrics(
        file_id="sample",
        mode="brep",
        source_type="step_runtime",
        confidence=0.92,
        bbox={"size": [120.0, 80.0, 6.0]},
        volume=1000.0,
        surface_area=None,
        part_count=1,
        triangle_count=None,
        feature_flags={"face_count": 24},
        metadata={"capability_status": "brep_ready"},
    )

    feature_map = build_feature_map(
        mode="brep",
        geometry_metrics=geometry_metrics,
        feature_flags={
            "hole_count": 3,
            "thread_hints": True,
            "surface_breakdown": {"conical": 2},
        },
        source_signals={"thread_hints": ["HELICOIDAL_SURFACE entity detected"]},
    )

    assert feature_map["mode"] == MODE_BREP
    assert feature_map["features"]["holes"]["count"] == 3
    assert feature_map["features"]["threads"]["count"] == 1
    assert feature_map["features"]["drafts"]["count"] == 2
    assert feature_map["features"]["thin_walls"]["count"] == 1


def test_feature_map_fails_closed_for_visual_only_mode() -> None:
    geometry_metrics = build_runtime_geometry_metrics(
        file_id="sample",
        mode="visual_only",
        source_type="analysis_unavailable",
        confidence=0.2,
        bbox=None,
        volume=None,
        surface_area=None,
        part_count=None,
        triangle_count=None,
        metadata={"capability_status": "preview_only"},
    )

    feature_map = build_feature_map(
        mode="visual_only",
        geometry_metrics=geometry_metrics,
        feature_flags={},
        source_signals={},
    )

    assert feature_map["mode"] == MODE_VISUAL_ONLY
    assert feature_map["features"]["holes"]["supported"] is False
    assert feature_map["features"]["threads"]["supported"] is False
    assert feature_map["features"]["drafts"]["supported"] is False
