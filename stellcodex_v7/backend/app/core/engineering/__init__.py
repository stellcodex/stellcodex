from __future__ import annotations

from app.core.engineering.cost_estimation import build_cost_estimate
from app.core.engineering.dfm import ENGINEERING_DFM_VERSION, SCHEMA_VERSION as DFM_SCHEMA_VERSION, build_engineering_dfm_report
from app.core.engineering.feature_extraction import FEATURE_EXTRACTOR_VERSION, build_feature_map
from app.core.engineering.geometry_metrics import (
    MODE_BREP,
    MODE_MESH_APPROX,
    MODE_VISUAL_ONLY,
    build_geometry_hash,
    build_geometry_metrics_payload,
    build_runtime_geometry_metrics,
    bbox_size_vector,
    infer_wall_thickness_stats,
    normalize_geometry_mode,
)
from app.core.engineering.manufacturing import KNOWN_PROCESSES, RULE_VERSION as MANUFACTURING_RULE_VERSION, build_manufacturing_decision
from app.core.engineering.manufacturing_planner import build_manufacturing_plan
from app.core.engineering.report_generation import build_engineering_report

__all__ = [
    "DFM_SCHEMA_VERSION",
    "ENGINEERING_DFM_VERSION",
    "FEATURE_EXTRACTOR_VERSION",
    "KNOWN_PROCESSES",
    "MANUFACTURING_RULE_VERSION",
    "MODE_BREP",
    "MODE_MESH_APPROX",
    "MODE_VISUAL_ONLY",
    "bbox_size_vector",
    "build_cost_estimate",
    "build_feature_map",
    "build_engineering_dfm_report",
    "build_geometry_hash",
    "build_geometry_metrics_payload",
    "build_manufacturing_decision",
    "build_manufacturing_plan",
    "build_engineering_report",
    "build_runtime_geometry_metrics",
    "infer_wall_thickness_stats",
    "normalize_geometry_mode",
]
