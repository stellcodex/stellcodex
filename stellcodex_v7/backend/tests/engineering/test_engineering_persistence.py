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
    DfmReportRecord,
    EngineeringReportRecord,
    FeatureMap,
    GeometryMetric,
    ManufacturingPlanRecord,
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
                DfmReportRecord.__table__,
                CostEstimateRecord.__table__,
                ManufacturingPlanRecord.__table__,
                EngineeringReportRecord.__table__,
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
        dfm_report = self.db.query(DfmReportRecord).one()
        cost_estimate = self.db.query(CostEstimateRecord).one()
        manufacturing_plan = self.db.query(ManufacturingPlanRecord).one()
        engineering_report = self.db.query(EngineeringReportRecord).one()
        artifact_cache = self.db.query(ArtifactCacheEntry).one()
        analysis_run = self.db.query(AnalysisRun).one()

        self.assertEqual(len(geometry_hash), 64)
        self.assertEqual(metrics.geometry_hash, geometry_hash)
        self.assertEqual(metrics.mode, "MESH_APPROX")
        self.assertEqual(metrics.part_count, 1)
        self.assertTrue(metrics.wall_thickness_stats)
        self.assertEqual(feature_map.feature_map_json["features"]["holes"]["count"], None)
        self.assertEqual(feature_map.feature_map_json["features"]["threads"]["count"], None)
        self.assertEqual(feature_map.feature_map_json["features"]["thin_walls"]["detection_mode"], "bounding_box_proxy")
        self.assertEqual(dfm_report.report_json["file_id"], self.row.file_id)
        self.assertTrue(dfm_report.report_json["manufacturing_recommendation"])
        self.assertTrue(dfm_report.report_json["risks"])
        self.assertEqual(cost_estimate.recommended_process, manufacturing_plan.recommended_process)
        self.assertGreater(cost_estimate.estimated_unit_cost, 0.0)
        self.assertEqual(
            engineering_report.report_json["manufacturing_recommendation"]["recommended_process"],
            manufacturing_plan.recommended_process,
        )
        self.assertTrue(manufacturing_plan.plan_json["process_sequence"])
        self.assertEqual(engineering_report.report_json["file_id"], self.row.file_id)
        self.assertTrue(engineering_report.report_json["report_hash"])
        self.assertEqual(artifact_cache.analysis_type, "engineering_analysis")
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
