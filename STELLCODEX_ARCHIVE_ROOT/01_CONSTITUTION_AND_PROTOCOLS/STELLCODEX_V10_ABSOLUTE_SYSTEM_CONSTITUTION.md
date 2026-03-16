---
archive_schema_version: "10.0"
system: "STELLCODEX"
source_domain: "ARCHIVE"
canonical_status: "ARCHIVE_MIRROR"
owner_layer: "SYSTEM"
related_release: "V10_CONSTITUTION_ACTIVATION"
hash_sha256: "PENDING"
last_verified_at: "2026-03-16T12:30:00Z"
sync_reference: "GITHUB:docs/v10/00_V10_MASTER_CONSTITUTION.md + ARCHIVE:01_CONSTITUTION_AND_PROTOCOLS"
---

# STELLCODEX V10 - ABSOLUTE SYSTEM CONSTITUTION

Archive mirror note:
- Active GitHub authority lives at `docs/v10/00_V10_MASTER_CONSTITUTION.md`.
- This archive file preserves the mirrored V10 constitution inside the continuity archive.

Version: 10.0
Status: ARCHIVE MIRROR OF ACTIVE GITHUB CONSTITUTION
Scope: Entire STELLCODEX platform

## 1. System Identity

Platform: STELLCODEX

Operational Intelligence Layer:
STELL-AI

Purpose:
- Engineering analysis
- Manufacturing intelligence
- Deterministic artifact processing
- Evidence-driven reporting
- Full audit traceability

The system must always produce verifiable runtime artifacts.

## 2. Absolute Architectural Model

STELLCODEX uses three infrastructure domains.

### Domain A - Canonical System Definition

Repository platform:
GitHub

Contains:
- source code
- infra definitions
- migrations
- tests
- contracts
- automation scripts
- release manifests

GitHub defines how the system exists.

### Domain B - Permanent Artifact Archive

Storage platform:
Google Drive

Contains:
- backups
- restore proofs
- audit evidence
- datasets
- exports
- reports
- freeze snapshots

Drive proves what happened in the system.

### Domain C - Runtime Execution

Infrastructure:
VPS / containers

Purpose:
- compute execution
- job processing
- temporary caching

Rule:
Server must be stateless.

If the server disappears, the system must be rebuildable from GitHub + Drive only.

## 3. Source of Truth Hierarchy

When conflicts appear resolve using this order:

1. `docs/v10/00_V10_MASTER_CONSTITUTION.md`
2. `docs/v10/01_V10_SOURCE_HIERARCHY.md`
3. current verified repository reality
4. runtime evidence and passing tests
5. current valid DB, API, and runtime contracts
6. archived historical protocol generations
7. prompts

Prompts are never authoritative.

## 4. Archive Constitution

The platform must enforce a single archive hierarchy.

Root structure:

```text
STELLCODEX_ARCHIVE_ROOT
00_MASTER_INDEX
01_CONSTITUTION_AND_PROTOCOLS
02_GITHUB_CANON
03_GDRIVE_ARCHIVE
04_PRODUCT_SURFACES
05_CORE_ENGINES
06_OPERATIONS
07_STELL_AI
08_PRODUCT_DATA_MODEL
99_DEPRECATED_AND_FROZEN
```

## 5. Master Continuity System

The following files must always exist:

- MASTER_ARCHIVE_INDEX.md
- CONTINUATION_CONTEXT.md
- CURRENT_STATE.md
- ACTIVE_BLOCKERS.md
- LAST_PASSING_RELEASE.md
- NEXT_ACTION_QUEUE.md
- SYSTEM_STATE_LEDGER.md
- SYSTEM_COMPONENT_MAP.md
- RUNTIME_TO_ARCHIVE_MAP.md

These documents prevent context loss between humans and AI agents.

## 6. Naming Constitution

Folder rules:

- 00_
- 01_
- 02_

Upper snake case only.

Forbidden names:

- final
- latest
- latest2
- real_final
- temp
- use_this

These names cause long-term drift.

## 7. Metadata Constitution

Every important document must contain:

- archive_schema_version
- system
- source_domain
- canonical_status
- owner_layer
- related_release
- hash_sha256
- last_verified_at
- sync_reference

This enables artifact verification.

## 8. Release Evidence Protocol

Every release must generate:

- release tag
- release manifest
- release evidence bundle
- drive mirror
- archive index update

Release without evidence = invalid.

## 9. Restore Guarantee

The platform must be rebuildable using:

- GitHub repository
- Drive backups
- environment templates

Restore test must prove:

- database recovery
- object storage recovery
- worker recovery
- API recovery

Restore proof must be archived.

## 10. Deterministic Processing Model

All jobs must follow this execution chain:

1. upload
2. convert
3. assembly_meta
4. rule_engine
5. dfm_engine
6. report
7. pack
8. archive

Jobs must be:

- idempotent
- traceable
- recoverable

## 11. Event Architecture

Service communication must use events.

Format:
CloudEvents 1.0

Event bus example infrastructure:
Redis Streams

All events must contain:

- event_id
- trace_id
- tenant_id
- timestamp

## 12. STELL-AI Operational Intelligence

The AI layer is composed of modules:

- Listener
- Planner
- Executor
- Memory
- Reporter

Responsibilities:

- plan tasks
- execute operations
- retrieve memory
- report outcomes

The AI must never modify the system without audit evidence.

## 13. Product Surface Model

User interface surfaces:

- Dashboard
- Projects
- Files
- Viewer
- Shares
- Admin
- Settings

These represent the entire product UI.

No hidden surfaces are allowed.

## 14. Data Model Constitution

Core entities:

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

Every entity must include:

- tenant_id
- created_at
- updated_at

Tenant isolation is mandatory.

## 15. Security Constitution

Rules:

- No storage_key leaks
- No client-supplied permissions
- Tool execution must use allowlists

Critical operations require approval protocol.

## 16. Deprecation Protocol

Old versions must move to:
99_DEPRECATED_AND_FROZEN

Allowed archives:

- v4
- v5
- v6
- v7_freeze_snapshots

Deprecated content must never remain active.

## 17. Context Loss Rule

Context loss is a SEV-0 failure.

If context is missing:

AI must retrieve:

- archive index
- state ledger
- continuation context

before answering.

## 18. System Guarantee

When this constitution is respected:

STELLCODEX becomes:

- deterministic
- auditable
- recoverable
- expandable

The system will remain operational even if the runtime server is destroyed.

## Final Statement

STELLCODEX must operate under one constitution, one archive, one truth hierarchy.

No parallel protocols are allowed.

Future architecture changes must produce a new constitution version.

Until then:
V10 remains the binding system constitution.
