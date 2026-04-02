# STELLCODEX V10 API Contracts

- Document ID: `V10-05`
- Status: `Active Canonical`
- Parent authority: `docs/v10/00_V10_MASTER_CONSTITUTION.md`, `docs/v10/01_V10_SOURCE_HIERARCHY.md`
- Related documents: `docs/v10/04_V10_DATA_MODEL.md`, `docs/v10/08_V10_SHARE_AND_PUBLIC_ACCESS_CONTRACT.md`, `docs/v10/09_V10_ORCHESTRATOR_RULES_AND_DFM.md`
- Last updated: `2026-04-02`
- Language: `English`
- Scope: `Public and operator-facing API contracts`
- Replacement rule: `API contract changes must update this file, tests, and runtime evidence before they are considered active.`

This document is governed by `docs/v10/00_V10_MASTER_CONSTITUTION.md` and `docs/v10/01_V10_SOURCE_HIERARCHY.md`. If any lower-level file conflicts with these authorities, this file must be updated to comply.

## Public Identifier Rule

- `file_id` is the public file identifier
- `storage_key` must never appear in public response bodies
- deprecated aliases may exist temporarily, but they may not replace the canonical `file_id` contract

## Minimum Endpoint Families

- `auth`: member/admin session auth, Google sign-in, identity, session state
- `files`: upload, detail, status, viewer metadata, version history, new version upload, archive access
- `jobs`: processing status and job details
- `orchestrator`: start, decision state, required inputs
- `approvals`: approve and reject protected decisions
- `dfm`: DFM report surfaces
- `stell-ai`: proxy surface for plan, analyze, decide, and memory endpoints backed by the internal STELL.AI service
- `shares`: create, resolve, revoke
- `admin`: health, files, shares, users, approvals, queues, RBAC, audit, system state
- `internal-runtime`: internal case logging, memory retrieval, decision logs, and experience write/search used by STELL.AI and Orchestra

## Contract Rules

- expired public shares must return `410`
- rate limits must return `429` and write audit evidence
- unauthenticated access must return `401`
- forbidden access must return `403`
- no endpoint may leak storage internals or client-supplied permissions
- `/api/v1/auth/guest` is retired and must not be reintroduced
- backend route handlers may proxy to STELL.AI and Orchestra, but they may not own intelligence or workflow transition rules
- backend `orchestrator` routes are gateway surfaces: backend enforces auth/ownership before proxying, while workflow decisions and transitions remain Orchestra-owned
- `internal-runtime` endpoints are non-public service surfaces and must require the internal service token (`X-Internal-Token`) on every route
- internal AI case logging may persist `retrieved_context_summary` when the caller injects pre-decision memory context
- `repeat_failure_guard` is a recovery-input signal in intelligence and orchestration payloads; approval state remains owned by Orchestra
- backend `stell-ai` proxy routes must inject backend-derived `tenant_id` into forwarded STELL.AI payloads; caller-supplied tenant scope is not trusted
- when `file_id` is provided to `stell-ai` proxy routes, backend must resolve and forward canonical file identity only after ownership validation
- two distinct approval surfaces exist: owner-initiated (`/approvals/{session_id}/approve|reject`, guarded by file ownership) and admin-initiated (`/admin/approvals/{id}:approve|reject`, guarded by admin role); both proxy to the same Orchestra endpoint and Orchestra is the state-transition authority for both paths

## Current File Endpoint Minimums

- `POST /api/v1/files/upload`
- `GET /api/v1/files/{file_id}`
- `GET /api/v1/files/{file_id}/status`
- `GET /api/v1/files/{file_id}/versions`
- `POST /api/v1/files/{file_id}/new-version`

## Internal Runtime Minimums

All `internal-runtime` endpoints require the `X-Internal-Token` header. These
surfaces are non-public; they are called by Orchestra and STELL.AI only.

### File and rule context (consumed by Orchestra and STELL.AI)

- `GET /api/v1/internal/runtime/files/{file_id}/context`
- `GET /api/v1/internal/runtime/rule-config`

### Orchestrator session persistence (write authority: Orchestra)

- `GET /api/v1/internal/runtime/orchestrator/sessions/by-file/{file_id}`
- `GET /api/v1/internal/runtime/orchestrator/sessions/by-id/{session_id}`
- `POST /api/v1/internal/runtime/orchestrator/sessions/upsert`

### AI case logging and memory (write authority: STELL.AI)

- `POST /api/v1/internal/runtime/ai/cases/log`
- `POST /api/v1/internal/runtime/ai/memory/context`
- `POST /api/v1/internal/runtime/ai/decision-log`
- `POST /api/v1/internal/runtime/ai/experience/write`
- `POST /api/v1/internal/runtime/ai/experience/search`

## Repo Anchors

- router root: `backend/app/api/v1/router.py`
- route modules: `backend/app/api/v1/routes/`
- STELL.AI internal client: `_canonical_repos/stell-ai/runtime_app/lib/backend_client.py`
- Orchestra internal client: `_canonical_repos/orchestra/runtime_app/lib/backend_client.py`
- supporting schemas: `backend/app/schemas.py`, `schemas/decision_json.schema.json`
