## Archive Note

- Reason retired: This dated root-level report is historical release evidence, not active authority.
- Replaced by: `docs/v10/11_V10_RELEASE_GATES_AND_SMOKE.md` and `docs/manifests/FINAL_CONSOLIDATION_REPORT.md`
- Historical value: Yes. It preserves a dated validation snapshot from `2026-02-13`.

# STELLCODEX Final Report

- Date/Time: 2026-02-13T16:24:29+03:00
- Git commit hash: 77e772c
- Evidence policy: ignored -> not committed

## Commands And Exit Codes
- Frontend build ('npm run build'): exit=0
  - Evidence: evidence/final_validation_frontend_build_20260213_161442.txt
- Backend unittest ('python3 -m unittest -q backend/tests/test_hybrid_v1_geometry_merge_policy.py'): exit=0
  - Evidence: evidence/final_validation_backend_unittest_20260213_161841.txt
- Smoke gate ('./scripts/smoke_gate.sh'): exit=0
  - Evidence: evidence/final_validation_smoke_gate_20260213_161849.txt
  - Smoke detail log: evidence/smoke_gate_20260213_162358.txt

## Smoke Gate Critical Endpoint Results
- GET /api/v1/admin/health (admin bearer): 200
- GET /api/v1/admin/failures?limit=20 (no auth): 401 (accepted, route exists)
- GET /api/v1/admin/failures?limit=20 (admin bearer): 200
- POST /api/v1/upload: response includes file_id
- GET /api/v1/status/{revision_id}: 200
- GET /api/v1/status/{file_id}: 200
- GET /api/v1/files/{file_id}/lod/lod0: 200
- MinIO artefact listing under models/<project>/<revision>/ includes lod0.glb, meta.json, thumb.webp

## OpenAPI Snapshot
- evidence/openapi_snapshot_20260213_161419.json

## Release Readiness
- PASS
