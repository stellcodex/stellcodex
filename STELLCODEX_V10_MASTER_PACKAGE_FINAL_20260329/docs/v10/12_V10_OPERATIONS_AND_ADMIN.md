# STELLCODEX V10 Operations And Admin

- Document ID: `V10-12`
- Status: `Active Canonical`
- Parent authority: `docs/v10/00_V10_MASTER_CONSTITUTION.md`, `docs/v10/01_V10_SOURCE_HIERARCHY.md`
- Last updated: `2026-03-29`
- Language: `English`
- Scope: `Admin surfaces, operator actions, and operational limits`

## Operational Reality (2026-03-29)

As of the V10 Master Package closure, all operations conform to the following:
- **Runtime Disposability**: The server is a disposable runtime. No authoritative state or context should ever live there exclusively.
- **Evidence Archival**: All operation-critical evidence must be archived to Google Drive.
- **RBAC Enforcement**: Admin actions must be strictly RBAC-protected.

## Admin Scope

The admin domain covers:
- System health and queue monitoring.
- Storage hygiene and file cleanup.
- Public share and access control (Expiry/Revocation).
- User management and RBAC policy updates.
- Approval workflows.
- Audit visibility.

## Critical Operations

The following require explicit approval and audit evidence:
- **Destructive Actions**: Permanent file or project deletion.
- **Restore Drills**: Periodic validation of backup/restore procedures.
- **Policy Changes**: Modifications to security or RBAC policies.
- **Queue Control**: Pausing or restarting high-volume processing queues.

## Repo and Runtime Anchors

- **Admin Routes**: `frontend/src/app/(app)/admin/` and `backend/app/api/v1/routes/admin.py`.
- **Policy**: `security/rbac.policy.json`.
- **Audit Logs**: `security/audit.events.json` (Local) and Drive-archived audit logs.
- **Health Checks**: `backend/app/main.py` health endpoints.

## Operator Limits

Operators must never:
- Bypass fail-closed security protocols.
- Modify frozen V10 UI code.
- Introduce non-deterministic decision paths.
- Store sensitive secrets in the repository or on the runtime server (Use .env or Vault).
