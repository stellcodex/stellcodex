---
archive_schema_version: "10.0"
system: "STELLCODEX"
source_domain: "GITHUB"
canonical_status: "ACTIVE_INDEX"
owner_layer: "DATA"
related_release: "V10_CONSTITUTION_ACTIVATION"
hash_sha256: "PENDING"
last_verified_at: "2026-03-16T00:00:00Z"
sync_reference: "docs/data_model/SCHEMA_POLICY.md"
---

# PRODUCT_DATA_MODEL_INDEX

Primary schema policy source:
- `docs/data_model/SCHEMA_POLICY.md`

Core entities under constitutional control:
- users
- tenants
- memberships
- plans
- subscriptions
- projects
- files
- file_versions
- jobs
- shares
- audit_events
- rule_configs

Current schema anchors:
- `backend/app/models/`
- `backend/alembic/`
- `db/`

Model rules:
- Tenant isolation is mandatory.
- Core entities must carry `tenant_id`, `created_at`, and `updated_at`.
- Runtime schema enforcement must be proven by migrations and evidence, not by prompts.
