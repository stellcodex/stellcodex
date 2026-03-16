# STELLCODEX V10 Data Model

- Document ID: `V10-04`
- Status: `Active Canonical`
- Parent authority: `docs/v10/00_V10_MASTER_CONSTITUTION.md`, `docs/v10/01_V10_SOURCE_HIERARCHY.md`
- Related documents: `docs/v10/05_V10_API_CONTRACTS.md`, `docs/v10/09_V10_ORCHESTRATOR_RULES_AND_DFM.md`, `docs/v10/10_V10_DEPLOY_BACKUP_RESTORE.md`
- Last updated: `2026-03-16`
- Language: `English`
- Scope: `Core entities, tenant isolation, and required fields`
- Replacement rule: `Data model changes require updates here, in migrations, and in contract tests before release.`

This document is governed by `docs/v10/00_V10_MASTER_CONSTITUTION.md` and `docs/v10/01_V10_SOURCE_HIERARCHY.md`. If any lower-level file conflicts with these authorities, this file must be updated to comply.

## Core Entities

The platform data model includes at minimum:
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
- orchestrator_sessions
- rule_configs

## Required Entity Rules

Every tenant-scoped entity must include:
- `tenant_id`
- `created_at`
- `updated_at`

Tenant isolation is mandatory.

## Locked Contracts

- `decision_json` is required for orchestrator-backed manufacturing decisions
- `rule_configs` is the threshold source; hardcoded thresholds are forbidden
- `assembly_meta` is required before a file can be treated as fully ready for viewer workflows
- public contracts must expose `file_id`, not storage internals

## Repo Anchors

- ORM models: `backend/app/models/`
- service logic: `backend/app/services/`
- SQL migrations: `db/migrations/`
- alembic migrations: `backend/alembic/versions/`
