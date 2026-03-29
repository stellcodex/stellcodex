# STELLCODEX V10 Data Model

- Document ID: `V10-04`
- Status: `Active Canonical`
- Parent authority: `docs/v10/00_V10_MASTER_CONSTITUTION.md`, `docs/v10/01_V10_SOURCE_HIERARCHY.md`
- Last updated: `2026-03-29`
- Language: `English`
- Scope: `Core entities, identity discipline, and tenant isolation`

## Identity Discipline

STELLCODEX V10 enforces an absolute public identity discipline.
- **Public Identity**: `file_id`-only for all public-facing routes, shares, and viewer surfaces.
- **Leak Protection**: Internal fields like `storage_key`, `object_key`, `bucket_id`, `internal_path`, or provider URLs must never be exposed to users or viewers.
- **Deterministic ID**: `file_id` must be stable across job retries and version updates.

## Core Entities

The platform data model includes at minimum:
- **Core**: users, tenants, memberships, plans, subscriptions.
- **Workflow**: projects, files, file_versions, jobs.
- **Collaboration**: shares, viewer_sessions, audit_events.
- **Decision Engine**: rule_configs, orchestrator_sessions, decision_json.

## Required Entity Rules

Every tenant-scoped entity must include:
- `tenant_id` (Mandatory Isolation)
- `created_at`
- `updated_at`

## Locked Data Contracts

- `decision_json`: Required for all manufacturing decisions.
- `rule_configs`: Threshold source (no hardcoded thresholds).
- `assembly_meta`: Required for assembly-aware viewer workflows.
- `fail_closed`: Every data access must verify membership and tenant isolation.

## Repo Anchors

- **ORM Models**: `backend/app/models/`
- **Migrations**: `db/migrations/` and `backend/alembic/versions/`
- **Schemas**: `backend/app/schemas.py` and `schemas/` directory.
