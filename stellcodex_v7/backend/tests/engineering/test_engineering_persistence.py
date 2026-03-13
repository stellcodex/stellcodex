from __future__ import annotations

import unittest
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.artifact_cache import get_manifest_row, get_manifest_row_by_geometry, upsert_manifest
from app.core.engineering_persistence import finalize_analysis_run, persist_engineering_analysis, start_analysis_run
from app.db.base import Base
from app.models.engineering import (
    AnalysisRun,
    ArtifactCacheEntry,
    CostEstimateRecord,
    CostOptimizationRecord,
    DesignIntentRecord,
    DesignOptimizationRecord,
    DfmReportRecord,
    EngineeringReportRecord,
    FeatureMap,
    GeometryMetric,
    ManufacturingPlanRecord,
    ProcessSimulationRecord,
)
from app.models.file import UploadFile
from app.models.master_contract import Tenant
from app.models.phase2 import ArtifactManifest


class EngineeringPersistenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        self.Session = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
        Base.metadata.create_all(
            bind=self.engine,
            tables=[
                Tenant.__table__,
                UploadFile.__table__,
                ArtifactManifest.__table__,
                GeometryMetric.__table__,
                FeatureMap.__table__,
                DesignIntentRecord.__table__,
                DfmReportRecord.__table__,
                CostEstimateRecord.__table__,
                CostOptimizationRecord.__table__,
                ManufacturingPlanRecord.__table__,
                ProcessSimulationRecord.__table__,
                EngineeringReportRecord.__table__,
                DesignOptimizationRecord.__table__,
                ArtifactCacheEntry.__table__,
                AnalysisRun.__table__,
            ],
        )
        self.db = self.Session()
        self.db.add(
            Tenant(
                id=101,
                code="tenant-101",
                name="Tenant 101",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        )
        self.row = UploadFile(
            file_id="scx_33333333-3333-3333-3333-333333333333",
            owner_sub="guest-1",
            tenant_id=101,
            owner_user_id=None,
            owner_anon_sub="guest-1",
            is_anonymous=True,
            privacy="private",
            bucket="tenant-101",
            object_key="uploads/tenant_101/demo.stl",
            original_filename="demo.stl",
            content_type="model/stl",
            size_bytes=512,
            meta={
                "project_id": "p1",
                "kind": "3d",
                "mode": "mesh_approx",
                "geometry_meta_json": {
                    "units": "mm",
                    "bbox": {"x": 10.0, "y": 8.0, "z": 4.0},
                    "triangle_count": 12,
                    "part_count": 1,
                },
                "geometry_report": {"critical_unknowns": []},
                "part_count": 1,
            },
            decision_json={},
            status="ready",
            visibility="private",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.db.add(self.row)
        self.db.commit()

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()

    def test_persist_engineering_analysis_creates_geometry_feature_dfm_and_cache_rows(self) -> None:
        result = {
            "file_id": self.row.file_id,
            "mode": "mesh_approx",
            "confidence": 0.78,
            "capability_status": "supported",
            "volume": 12.5,
            "surface_area": 44.2,
            "bounding_box": {
                "min": [0.0, 0.0, 0.0],
                "max": [10.0, 8.0, 4.0],
                "size": [10.0, 8.0, 4.0],
            },
            "feature_flags": {
                "hole_count": 2,
                "thread_hints": True,
                "face_count": 12,
                "part_count": 1,
            },
            "dfm_risk": [{"code": "thin_section_proxy", "severity": "medium"}],
            "recommendations": ["Review thin sections against process minimum wall guidance."],
            "rule_version": "engineering_dfm.v1",
            "rule_explanations": ["DFM confidence is reduced because the mesh is not watertight."],
            "design_intent": {
                "schema": "stellcodex.v10.design_intent",
                "file_id": "scx_33333333-3333-3333-3333-333333333333",
                "functional_features": [{"name": "holes", "count": 2}],
                "structural_features": [{"name": "part_count", "value": 1}],
                "critical_dimensions": {"bbox_size_mm": [10.0, 8.0, 4.0]},
                "manufacturing_sensitive_features": [{"name": "thin_walls", "severity": "medium"}],
            },
            "process_simulation": {
                "schema": "stellcodex.v10.process_simulation",
                "machining_feasibility": "feasible",
                "collision_risk": "low",
                "tool_accessibility": "good",
                "setup_complexity": "low",
            },
            "cost_optimization": {
                "schema": "stellcodex.v10.cost_optimization",
                "baseline_cost": 120.0,
                "optimized_cost": 110.0,
                "cost_drivers": ["setup_count=1"],
                "optimization_suggestions": ["Reduce setup count."],
            },
            "design_optimization": {
                "schema": "stellcodex.v10.design_optimization",
                "status": "actionable",
                "suggestions": [{"id": "stabilize_thin_sections"}],
            },
            "engineering_decision": {
                "schema": "stellcodex.v10.engineering_decision",
                "recommended_process": "cnc_machining",
                "manufacturing_plan": {"recommended_process": "cnc_machining"},
                "cost_estimate": {"estimated_unit_cost": 24.2},
                "design_risks": [],
                "design_recommendations": ["Reduce setup count."],
            },
            "engineering_master_report": {
                "schema": "stellcodex.v10.engineering_master_report",
                "file_id": "scx_33333333-3333-3333-3333-333333333333",
                "manufacturing_recommendation": {"recommended_process": "cnc_machining"},
                "process_simulation": {"machining_feasibility": "feasible"},
                "report_hash": "abc123",
            },
            "unavailable_reason": None,
        }

        run = start_analysis_run(
            self.db,
            row=self.row,
            run_type="engineering_analysis",
            session_id="job-1",
            metrics={"job_id": "job-1"},
        )
        self.db.flush()
        geometry_hash = persist_engineering_analysis(
            self.db,
            row=self.row,
            result=result,
            analysis_type="engineering_analysis",
            session_id="job-1",
        )
        finalize_analysis_run(
            self.db,
            run,
            result=result,
            geometry_hash=geometry_hash,
            error_code=None,
        )
        self.db.commit()

        metrics = self.db.query(GeometryMetric).one()
        feature_map = self.db.query(FeatureMap).one()
        design_intent = self.db.query(DesignIntentRecord).one()
        dfm_report = self.db.query(DfmReportRecord).one()
        cost_estimate = self.db.query(CostEstimateRecord).one()
        cost_optimization = self.db.query(CostOptimizationRecord).one()
        manufacturing_plan = self.db.query(ManufacturingPlanRecord).one()
        process_simulation = self.db.query(ProcessSimulationRecord).one()
        engineering_report = self.db.query(EngineeringReportRecord).one()
        design_optimization = self.db.query(DesignOptimizationRecord).one()
        artifact_cache = self.db.query(ArtifactCacheEntry).all()
        analysis_run = self.db.query(AnalysisRun).one()

        self.assertEqual(len(geometry_hash), 64)
        self.assertEqual(metrics.geometry_hash, geometry_hash)
        self.assertEqual(metrics.mode, "MESH_APPROX")
        self.assertEqual(metrics.part_count, 1)
        self.assertTrue(metrics.wall_thickness_stats)
        self.assertEqual(feature_map.feature_map_json["features"]["holes"]["count"], None)
        self.assertEqual(feature_map.feature_map_json["features"]["threads"]["count"], None)
        self.assertEqual(feature_map.feature_map_json["features"]["thin_walls"]["detection_mode"], "bounding_box_proxy")
        self.assertEqual(design_intent.intent_json["functional_features"][0]["name"], "holes")
        self.assertEqual(dfm_report.report_json["file_id"], self.row.file_id)
        self.assertTrue(dfm_report.report_json["manufacturing_recommendation"])
        self.assertTrue(dfm_report.report_json["risks"])
        self.assertEqual(cost_estimate.recommended_process, manufacturing_plan.recommended_process)
        self.assertGreater(cost_estimate.estimated_unit_cost, 0.0)
        self.assertEqual(cost_optimization.optimization_json["optimized_cost"], 110.0)
        self.assertEqual(process_simulation.simulation_json["machining_feasibility"], "feasible")
        self.assertEqual(
            engineering_report.report_json["manufacturing_recommendation"]["recommended_process"],
            manufacturing_plan.recommended_process,
        )
        self.assertEqual(design_optimization.optimization_json["status"], "actionable")
        self.assertTrue(manufacturing_plan.plan_json["process_sequence"])
        self.assertEqual(engineering_report.report_json["file_id"], self.row.file_id)
        self.assertTrue(engineering_report.report_json["report_hash"])
        self.assertEqual(
            {row.analysis_type for row in artifact_cache},
            {
                "engineering_analysis",
                "design_intent",
                "process_simulation",
                "cost_optimization",
                "design_optimization",
                "engineering_decision",
                "engineering_master_report",
            },
        )
        self.assertEqual(analysis_run.status, "completed")
        self.assertEqual(analysis_run.metrics_json["geometry_hash"], geometry_hash)

    def test_artifact_manifest_geometry_hash_lookup_is_exact(self) -> None:
        row = upsert_manifest(
            self.db,
            file_id=self.row.file_id,
            version_no=1,
            stage="convert",
            geometry_hash="geom-1",
            input_hash="input-1",
            artifact_uri="converted/demo.glb",
            artifact_payload={"file_id": self.row.file_id, "geometry_hash": "geom-1"},
        )
        self.db.commit()

        self.assertEqual(row.geometry_hash, "geom-1")
        self.assertIsNotNone(
            get_manifest_row_by_geometry(
                self.db,
                file_id=self.row.file_id,
                version_no=1,
                stage="convert",
                geometry_hash="geom-1",
            )
        )
        self.assertIsNone(
            get_manifest_row_by_geometry(
                self.db,
                file_id=self.row.file_id,
                version_no=1,
                stage="convert",
                geometry_hash="geom-2",
            )
        )
        self.assertIsNotNone(get_manifest_row(self.db, self.row.file_id, 1, "convert"))
