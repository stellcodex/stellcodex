# V7 Completion Matrix

Updated: 2026-03-10 (UTC)

| Requirement | Implemented | Verified |
|---|---|---|
| `file_id` is the only public identity | Yes | `test_public_contract_leaks.py` + smoke artifacts in `/root/workspace/evidence/v7_gate_20260308T014732Z/smoke/` |
| Public contract forbids `revision_id` | Yes | OpenAPI assertion `test_openapi_contract_has_no_revision_or_storage_key` |
| Public contract forbids `storage_key` / internal object keys | Yes | leak test + smoke outputs do not expose internal keys |
| Legacy product status route does not emit presigned URLs containing internal keys | Yes | `product.py` contract hardening + `test_product_route_no_storage_key_presign_contract` |
| `orchestrator_sessions.decision_json` NOT NULL + required fields | Yes | schema check output `/root/workspace/evidence/v7_gate_20260308T014732Z/db_schema_check.txt` |
| `rule_configs` drives thresholds (no hardcoded policy path) | Yes | schema+tests (`test_v7_contracts.py`, `test_orchestrator_core.py`) |
| Strict state model S0..S7 with no illegal skip | Yes | orchestrator tests + gate smoke |
| Manual approval path (S4/S5 -> S7) deterministic and stable | Yes | regression test `test_manual_approval_keeps_s7_when_required_inputs_pending` |
| Deterministic manufacturing rules (7 required rules) | Yes | `app/core/rule_engine.py` + `test_v7_deterministic_engines.py` |
| DFM engine JSON + PDF with metadata | Yes | `app/core/dfm_engine.py` + smoke `dfm_report.json` |
| Assembly contract enforces `assembly_meta` + occurrence based part count | Yes | `test_v7_contracts.py` + smoke `manifest.json` |
| Share token >=64, expiry required, expired=410, revoke invalidation, rate limits | Yes | smoke artifacts: `share_expired_410.json`, `share_revoke_denied.json`, `share_rate_429.json` |
| MIME/extension/size validation | Yes | format/upload tests + gate smoke uploads |
| Format capability matrix is explicit and repo-truth locked | Yes | `docs/execution/format_capability_matrix.md` |
| Deterministic format extraction exists for STL / OBJ / STEP / DXF / PDF / DOCX | Yes | `test_format_intelligence.py` |
| Extraction failures for supported formats fail closed and persist safe status | Yes | `test_format_intelligence.py` + `test_upload_contracts.py` |
| Extraction payloads remain `file_id`-based and storage-agnostic | Yes | `test_public_contract_leaks.py` + `test_upload_contracts.py` |
| Async virus scan stage exists in worker pipeline | Yes | `app/workers/tasks.py` (`security` stage + `virus_scan_status`) |
| Immutable audit/evidence includes session/rule/risk/decision hash references | Yes | orchestrator event payload generation in `app/core/orchestrator.py` |
| Backup + restore + post-restore smoke gate mandatory | Yes | `release_gate_v7.sh` PASS + restore/smoke PASS markers |
