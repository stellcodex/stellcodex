# STELLCODEX DATABASE AUDIT
Generated: 2026-03-08T14:48:00Z
Database: PostgreSQL @ localhost:15432/stellcodex

## Alembic Version
j1a2b3c4d5e6 (knowledge engine tables — CURRENT)

## Table Row Counts
| Table | Rows |
|-------|------|
| alembic_version | 1 |
| artifact_manifest | 264 |
| artifacts | 0 |
| audit_events | 385 |
| dlq_records | 0 |
| file_read_projections | 44 |
| file_versions | 16 |
| files | 16 |
| job_failures | 0 |
| job_logs | 0 |
| jobs | 0 |
| knowledge_index_jobs | 2 |
| knowledge_records | 535 |
| library_items | 0 |
| memberships | 0 |
| orchestrator_sessions | 44 |
| plans | 0 |
| processed_event_ids | 265 |
| production_orders | 0 |
| projects | 0 |
| quotes | 0 |
| revision_files | 0 |
| revisions | 0 |
| revoked_tokens | 0 |
| rule_configs | 17 |
| shares | 45 |
| stage_locks | 0 |
| subscriptions | 0 |
| tenants | 23 |
| uploaded_files | 44 |
| users | 11 |

## Mandatory Table Verification
| Table | Status |
|-------|--------|
| files | PRESENT (16 rows) |
| uploaded_files | PRESENT (44 rows) |
| projects | PRESENT |
| orchestrator_sessions | PRESENT (44 rows) |
| rule_configs | PRESENT (17 rows) |
| approvals | NOT SEPARATE TABLE — embedded in orchestrator_sessions |
| audit_events | PRESENT (385 rows) |
| knowledge_records | PRESENT (535 rows) — NEW |
| knowledge_index_jobs | PRESENT (2 rows) — NEW |
| processed_event_ids | PRESENT (265 rows) |

## Mandatory Field Verification
- tenant_id: present in files, uploaded_files, knowledge_records, orchestrator_sessions ✓
- file_id: present in knowledge_records, artifacts, file_versions ✓
- decision_json: present in orchestrator_sessions (as JSON column) ✓
- rule_version: present in rule_configs ✓

## Issues
- NONE detected
