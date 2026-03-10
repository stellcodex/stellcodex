# Canonical Knowledge Index (CKI) Architecture

Updated: 2026-03-08 (UTC)

## Purpose
Rebuildable index layer that maps permanent Google Drive knowledge into retrievable chunks for STELL.AI.

## Source-of-Truth Rule
- Permanent truth: Google Drive (`STELL/...`).
- Rebuildable derived index: CKI store.
- Runtime servers are disposable and non-authoritative.

## Ownership
- ORCHESTRA owns CKI ingestion jobs:
  - artifact discovery
  - parsing/chunking
  - embedding generation
  - retry/DLQ handling
  - index export publication
- STELL.AI owns CKI retrieval consumption:
  - semantic search
  - context assembly for planner/executor/reporter
  - memory-aware response flow

## Implemented Scaffolding
- Ingestion builder: `/root/workspace/ops/orchestra/orchestrator/ingestion/cki_ingest.py`
- Retrieval client: `/root/workspace/AI/stell_ai/cki/retrieval.py`

## CKI Record Contract
- `artifact_id`
- `drive_path`
- `checksum`
- `chunk_id`
- `chunk_text`
- `embedding_vector`
- `source_link`
- `ingested_at`

## Rebuild Path
1. Export Drive artifact inventory/content snapshots.
2. Run ORCHESTRA ingestion to produce CKI records.
3. Publish CKI artifact for STELL.AI retrieval.
4. Rebuild on demand from Drive + GitHub only.
