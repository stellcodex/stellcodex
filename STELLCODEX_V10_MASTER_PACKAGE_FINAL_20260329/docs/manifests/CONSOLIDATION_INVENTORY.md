# STELLCODEX Consolidation Inventory

- Status: `Active Canonical Manifest`
- Parent authority: `docs/v10/00_V10_MASTER_CONSTITUTION.md`, `docs/v10/01_V10_SOURCE_HIERARCHY.md`
- Last updated: `2026-03-16`
- Language: `English`

## Inventory Scope

This inventory covers the discovered protocol, constitution, contract, execution, UI, deployment, security, archive, prompt, and evidence files that were used to build the V10 package.

| File path | Title | Current language | Current role | Recommended fate | Authority level | Merge target | Archive target if retired |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `STELLCODEX_ARCHIVE_ROOT/01_CONSTITUTION_AND_PROTOCOLS/STELLCODEX_V10_ABSOLUTE_SYSTEM_CONSTITUTION.md` | V10 archive constitution mirror | English | archive constitution | keep as archive mirror | canonical input | `docs/v10/00_V10_MASTER_CONSTITUTION.md` | stay in archive root |
| `STELLCODEX_ARCHIVE_ROOT/00_MASTER_INDEX/CONTINUATION_CONTEXT.md` | archive continuation context | English | continuity context | keep as archive continuity support | supporting input | `docs/v10/16_V10_CONTEXT_CONTINUATION_PROTOCOL.md` | stay in archive root |
| `STELLCODEX_ARCHIVE_ROOT/00_MASTER_INDEX/CURRENT_STATE.md` | archive current state | English | archive status ledger | keep as archive continuity support | supporting input | `docs/v10/16_V10_CONTEXT_CONTINUATION_PROTOCOL.md` | stay in archive root |
| `STELLCODEX_ARCHIVE_ROOT/02_GITHUB_CANON/GITHUB_CANON_MANIFEST.md` | GitHub canon manifest | English | archive manifest | keep active as archive manifest | archive manifest candidate | `docs/v10/01_V10_SOURCE_HIERARCHY.md`, `docs/v10/15_V10_GITHUB_REPOSITORY_MAP.md` | stay in archive root |
| `STELLCODEX_ARCHIVE_ROOT/03_GDRIVE_ARCHIVE/GDRIVE_ARCHIVE_MANIFEST.md` | Drive archive manifest | English | archive manifest | keep active as archive manifest | archive manifest candidate | `docs/v10/14_V10_DRIVE_ARCHIVE_HIERARCHY.md` | stay in archive root |
| `STELLCODEX_ARCHIVE_ROOT/03_GDRIVE_ARCHIVE/RESTORE_PROOF_REGISTER.md` | restore proof register | English | restore evidence register | keep active as archive manifest | archive manifest candidate | `docs/v10/10_V10_DEPLOY_BACKUP_RESTORE.md`, `docs/v10/11_V10_RELEASE_GATES_AND_SMOKE.md` | stay in archive root |
| `docs/archive/legacy_generations/v7_constitution/STELLCODEX_V7_MASTER.md` | V7 master constitution | English | retired constitution | keep archived | historical reference | `docs/v10/00_V10_MASTER_CONSTITUTION.md`, `docs/v10/09_V10_ORCHESTRATOR_RULES_AND_DFM.md` | `docs/archive/legacy_generations/v7_constitution/` |
| `docs/archive/legacy_generations/v7_constitution/HIERARCHY.md` | V7 hierarchy | English | retired hierarchy | keep archived | historical reference | `docs/v10/01_V10_SOURCE_HIERARCHY.md` | `docs/archive/legacy_generations/v7_constitution/` |
| `docs/archive/legacy_generations/v7_constitution/V7_ENFORCEMENT_PROTOCOL.md` | V7 enforcement protocol | English | retired enforcement protocol | keep archived | historical reference | `docs/v10/07_V10_SECURITY_LIMITS_AND_COMPLIANCE.md`, `docs/v10/11_V10_RELEASE_GATES_AND_SMOKE.md` | `docs/archive/legacy_generations/v7_constitution/` |
| `docs/archive/legacy_generations/v6/V6_00_CONSTITUTION.md` | V6 constitution | Turkish | retired constitution | keep archived | historical reference | `docs/v10/00_V10_MASTER_CONSTITUTION.md` | `docs/archive/legacy_generations/v6/` |
| `docs/archive/legacy_generations/v6/V6_01_SOURCE_HIERARCHY.md` | V6 source hierarchy | English | retired hierarchy | keep archived | historical reference | `docs/v10/01_V10_SOURCE_HIERARCHY.md` | `docs/archive/legacy_generations/v6/` |
| `docs/archive/legacy_generations/STELLCODEX_MASTER_V1.3.md` | legacy product master | Turkish | retired product and UI authority | keep archived | obsolete active conflict | `docs/v10/02_V10_PRODUCT_SCOPE_AND_IDENTITY.md`, `docs/v10/06_V10_VIEWER_AND_UI_CONTRACT.md`, `docs/v10/19_V10_FRONTEND_SURFACE_CONTRACT.md` | `docs/archive/legacy_generations/` |
| `docs/contracts/API_CONTRACTS_V7.md` | V7 API contracts | English | contract reference | keep as supporting input | supporting input | `docs/v10/05_V10_API_CONTRACTS.md` | n/a |
| `docs/contracts/DECISION_JSON_SCHEMA.md` | decision_json schema note | English | contract reference | keep as supporting input | supporting input | `docs/v10/04_V10_DATA_MODEL.md`, `docs/v10/09_V10_ORCHESTRATOR_RULES_AND_DFM.md` | n/a |
| `docs/contracts/RATE_LIMIT_AND_AUDIT_SPEC.md` | rate limit and audit spec | English | contract reference | keep as supporting input | supporting input | `docs/v10/07_V10_SECURITY_LIMITS_AND_COMPLIANCE.md` | n/a |
| `docs/data_model/SCHEMA_POLICY.md` | schema policy | English | data-model reference | keep as supporting input | supporting input | `docs/v10/04_V10_DATA_MODEL.md` | n/a |
| `docs/security/permissions-catalog.md` | permissions catalog | Mixed | security inventory | keep as supporting input | supporting input | `docs/v10/07_V10_SECURITY_LIMITS_AND_COMPLIANCE.md`, `docs/v10/12_V10_OPERATIONS_AND_ADMIN.md` | n/a |
| `docs/security/role-permission-template.md` | role permission template | English | security template | keep as supporting input | supporting input | `docs/v10/07_V10_SECURITY_LIMITS_AND_COMPLIANCE.md` | n/a |
| `docs/compatibility/viewer-v1.md` | viewer feature lock | English | viewer reference | keep as supporting input | supporting input | `docs/v10/06_V10_VIEWER_AND_UI_CONTRACT.md` | n/a |
| `docs/compatibility/formats-matrix.md` | format matrix | Turkish | format reference | keep as supporting input | supporting input | `docs/v10/06_V10_VIEWER_AND_UI_CONTRACT.md`, `docs/v10/19_V10_FRONTEND_SURFACE_CONTRACT.md` | n/a |
| `docs/archive/historical_protocols/REBUILD_EXECUTION_PROTOCOL.md` | rebuild execution protocol | Mixed | retired execution plan | keep archived | historical reference | `docs/v10/13_V10_EXECUTION_ROADMAP.md`, `docs/v10/18_V10_EVIDENCE_AND_MANIFEST_STANDARD.md` | `docs/archive/historical_protocols/` |
| `docs/archive/frozen_reports/CONTRACT_GAP_MATRIX.md` | contract gap matrix | Mixed | frozen gap report | keep archived | runtime report | `docs/v10/05_V10_API_CONTRACTS.md`, `docs/v10/19_V10_FRONTEND_SURFACE_CONTRACT.md` | `docs/archive/frozen_reports/` |
| `docs/ops/evidence/PHASE_00_BASELINE.md` | baseline evidence | English | evidence | keep as evidence | evidence | `docs/v10/18_V10_EVIDENCE_AND_MANIFEST_STANDARD.md` | n/a |
| `docs/ops/evidence/PHASE_01_CONTRACT_FREEZE.md` | contract freeze evidence | English | evidence | keep as evidence | evidence | `docs/v10/18_V10_EVIDENCE_AND_MANIFEST_STANDARD.md` | n/a |
| `docs/ops/evidence/PHASE_02_DATA_MODEL_RUNTIME.md` | data-model runtime evidence | English | evidence | keep as evidence | evidence | `docs/v10/18_V10_EVIDENCE_AND_MANIFEST_STANDARD.md` | n/a |
| `docs/ops/evidence/PHASE_03_BACKEND_CONTRACT_SURFACE.md` | backend contract surface evidence | English | evidence | keep as evidence | evidence | `docs/v10/18_V10_EVIDENCE_AND_MANIFEST_STANDARD.md` | n/a |
| `docs/ops/evidence/PHASE_03_SHARE_CONTRACT_ALIGNMENT.md` | share alignment evidence | English | evidence | keep as evidence | evidence | `docs/v10/18_V10_EVIDENCE_AND_MANIFEST_STANDARD.md` | n/a |
| `docs/ops/evidence/PHASE_04_ADMIN_APPROVALS_UI.md` | admin approvals evidence | English | evidence | keep as evidence | evidence | `docs/v10/18_V10_EVIDENCE_AND_MANIFEST_STANDARD.md` | n/a |
| `docs/ops/evidence/PHASE_05_STORAGE_HYGIENE.md` | storage hygiene evidence | English | evidence | keep as evidence | evidence | `docs/v10/18_V10_EVIDENCE_AND_MANIFEST_STANDARD.md` | n/a |
| `docs/archive/evidence_v7_gate_fix_20260227_023017.md` | V7 gate fix evidence | English | archived evidence | keep archived | evidence | `docs/v10/11_V10_RELEASE_GATES_AND_SMOKE.md` | `docs/archive/` |
| `docs/archive/evidence_deploy_routing_fix_20260227_120420.md` | deploy routing evidence | English | archived evidence | keep archived | evidence | `docs/v10/18_V10_EVIDENCE_AND_MANIFEST_STANDARD.md` | `docs/archive/` |
| `docs/archive/evidence_phase2_chatgpt_layout_20260227_063049.md` | layout evidence | English | archived evidence | keep archived | evidence | `docs/v10/19_V10_FRONTEND_SURFACE_CONTRACT.md` | `docs/archive/` |
| `docs/archive/evidence_phase2_partcount_fix_20260227_060826.md` | part count evidence | English | archived evidence | keep archived | evidence | `docs/v10/06_V10_VIEWER_AND_UI_CONTRACT.md` | `docs/archive/` |
| `docs/archive/old_prompts/README_MASTER.md` | UI and route prompt | Turkish | archived prompt | keep archived | historical reference | `docs/v10/06_V10_VIEWER_AND_UI_CONTRACT.md`, `docs/v10/19_V10_FRONTEND_SURFACE_CONTRACT.md` | `docs/archive/old_prompts/` |
| `docs/archive/old_prompts/CLAUDE.md` | operator context prompt | Turkish | archived prompt | keep archived | historical reference | `docs/v10/15_V10_GITHUB_REPOSITORY_MAP.md`, `docs/v10/16_V10_CONTEXT_CONTINUATION_PROTOCOL.md` | `docs/archive/old_prompts/` |
| `docs/archive/old_prompts/V6_08_CODEX_MEGA_PROMPT_V6.md` | V6 mega prompt | English | archived prompt | keep archived | historical reference | `docs/v10/16_V10_CONTEXT_CONTINUATION_PROTOCOL.md`, `docs/v10/17_V10_LEGACY_RETIREMENT_MAP.md` | `docs/archive/old_prompts/` |
| `docs/archive/frozen_reports/FINAL_REPORT_20260213.md` | dated final report | English | archived report | keep archived | runtime report | `docs/v10/11_V10_RELEASE_GATES_AND_SMOKE.md`, `docs/manifests/FINAL_CONSOLIDATION_REPORT.md` | `docs/archive/frozen_reports/` |
| `docs/archive/frozen_reports/FINAL_EVIDENCE_20260227.md` | dated final evidence | Turkish | archived evidence report | keep archived | evidence | `docs/v10/18_V10_EVIDENCE_AND_MANIFEST_STANDARD.md`, `docs/manifests/FINAL_CONSOLIDATION_REPORT.md` | `docs/archive/frozen_reports/` |
| `frontend/RELEASE_GATE.md` | frontend release gate | English | frontend release note | keep as supporting input | supporting input | `docs/v10/11_V10_RELEASE_GATES_AND_SMOKE.md` | n/a |
| `frontend/docs/deploy.md` | frontend deploy guide | English | deployment note | keep as supporting input | supporting input | `docs/v10/10_V10_DEPLOY_BACKUP_RESTORE.md` | n/a |
| `frontend/docs/migration.md` | frontend migration note | English | migration note | keep as supporting input | supporting input | `docs/v10/10_V10_DEPLOY_BACKUP_RESTORE.md` | n/a |
