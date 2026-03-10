# System Boundary Matrix

Updated: 2026-03-08 (UTC)

| Capability | STELL.AI | ORCHESTRA | STELLCODEX | INFRA |
|---|---|---|---|---|
| Listener / planner / executor / reporter | **Owner** | Consumer via jobs | Not owner | Not owner |
| Memory records / founder knowledge / solved cases | **Owner** | Producer for ingestion inputs only | Consumer context only | Backup policy only |
| CKI retrieval query path | **Owner (query)** | Not owner | Consumer only | Not owner |
| CKI ingestion/chunk/embed jobs | Consumer | **Owner** | Not owner | Runtime support |
| Queue, worker registry, retry, DLQ, scheduling | Consumer | **Owner** | Producer/consumer for product jobs | Runtime support |
| Product APIs / file/view/share/approval contracts | Not owner | Not owner | **Owner** | Not owner |
| Deterministic orchestrator/rule/DFM decisions | Not owner | Compute support only | **Owner** | Not owner |
| Audit event ownership (product) | Context consumer | Job/artifact event producer | **Owner** | Retention only |
| Public identity contract (`file_id`) | Consumer | Consumer | **Owner** | Not owner |
| Internal key exposure control (`storage_key`, `revision_id`) | Not owner | Not owner | **Owner + enforced tests** | Not owner |
| Backup/restore release gate | Not owner | Execution support | **Owner** | **Owner** |
| GitHub source of truth | Repo-level | Repo-level | Repo-level | Repo-level |
| Google Drive permanent archive | Memory consumer | Ingestion/eval producer | Artifact/report producer | Governance + retention |
