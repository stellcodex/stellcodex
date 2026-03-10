# Event Spine Ownership Model

Updated: 2026-03-08 (UTC)

## Producers and Event Domains
- STELLCODEX (product/application events):
  - `upload.created`, `share.created`, `share.revoked`, `approval.approved`, `approval.rejected`, `dfm.report_generated`, `orchestrator.decision_generated`
- ORCHESTRA (execution/job/artifact events):
  - `job.queued`, `job.started`, `job.succeeded`, `job.failed`, `artifact.generated`, `retention.purge`
- STELL.AI (memory/planning/reporting events):
  - `memory.ingested`, `plan.generated`, `task.executed`, `report.generated`

## Required Event Payload Anchors
- `file_id` (public identity)
- `session_id` for orchestrator/approval flow events
- `rules_fired`, `risks`, `decision_hash` for deterministic decision evidence
- Artifact references only by public-safe links/ids (no `storage_key` leakage)

## Boundary Safeguards
- STELLCODEX never writes STELL.AI private memory stores directly.
- STELL.AI never mutates STELLCODEX product state directly.
- ORCHESTRA executes jobs and publishes results; it does not own product contract semantics.
