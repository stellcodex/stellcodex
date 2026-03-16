---
archive_schema_version: "10.0"
system: "STELLCODEX"
source_domain: "GITHUB"
canonical_status: "ACTIVE_INDEX"
owner_layer: "STELL_AI"
related_release: "V10_CONSTITUTION_ACTIVATION"
hash_sha256: "PENDING"
last_verified_at: "2026-03-16T00:00:00Z"
sync_reference: "backend/app/api/v1/routes/stell_ai.py"
---

# STELL_AI_INDEX

Constitutional modules:
- Listener
- Planner
- Executor
- Memory
- Reporter

Current implementation anchors:
- API surface: `backend/app/api/v1/routes/stell_ai.py`
- Prompt and routing state: `ops/orchestra/orchestrator/prompt_templates.json`
- Runtime memory/state stores: `ops/orchestra/state/`

Control rule:
- STELL-AI may assist planning and reporting.
- STELL-AI must not modify the system without audit evidence.
- Full module decomposition remains subject to explicit archived evidence.
