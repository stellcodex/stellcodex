# STELLCODEX V10 API Contracts

- Document ID: `V10-05`
- Status: `Active Canonical`
- Parent authority: `docs/v10/00_V10_MASTER_CONSTITUTION.md`, `docs/v10/01_V10_SOURCE_HIERARCHY.md`
- Related documents: `docs/v10/04_V10_DATA_MODEL.md`, `docs/v10/08_V10_SHARE_AND_PUBLIC_ACCESS_CONTRACT.md`, `docs/v10/09_V10_ORCHESTRATOR_RULES_AND_DFM.md`
- Last updated: `2026-03-16`
- Language: `English`
- Scope: `Public and operator-facing API contracts`
- Replacement rule: `API contract changes must update this file, tests, and runtime evidence before they are considered active.`

This document is governed by `docs/v10/00_V10_MASTER_CONSTITUTION.md` and `docs/v10/01_V10_SOURCE_HIERARCHY.md`. If any lower-level file conflicts with these authorities, this file must be updated to comply.

## Public Identifier Rule

- `file_id` is the public file identifier
- `storage_key` must never appear in public response bodies
- deprecated aliases may exist temporarily, but they may not replace the canonical `file_id` contract

## Minimum Endpoint Families

- `auth`: guest auth, identity, session state
- `files`: upload, detail, status, viewer metadata, archive access
- `jobs`: processing status and job details
- `orchestrator`: start, decision state, required inputs
- `approvals`: approve and reject protected decisions
- `dfm`: DFM report surfaces
- `shares`: create, resolve, revoke
- `admin`: health, files, shares, users, approvals, queues, RBAC, audit, system state

## Contract Rules

- expired public shares must return `410`
- rate limits must return `429` and write audit evidence
- unauthenticated access must return `401`
- forbidden access must return `403`
- no endpoint may leak storage internals or client-supplied permissions

## Repo Anchors

- router root: `backend/app/api/v1/router.py`
- route modules: `backend/app/api/v1/routes/`
- supporting schemas: `backend/app/schemas.py`, `schemas/decision_json.schema.json`
