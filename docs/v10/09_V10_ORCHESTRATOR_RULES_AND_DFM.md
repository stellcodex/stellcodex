# STELLCODEX V10 Orchestrator Rules And DFM

- Document ID: `V10-09`
- Status: `Active Canonical`
- Parent authority: `docs/v10/00_V10_MASTER_CONSTITUTION.md`, `docs/v10/01_V10_SOURCE_HIERARCHY.md`
- Related documents: `docs/v10/04_V10_DATA_MODEL.md`, `docs/v10/05_V10_API_CONTRACTS.md`, `docs/v10/11_V10_RELEASE_GATES_AND_SMOKE.md`
- Last updated: `2026-03-23`
- Language: `English`
- Scope: `State machine, deterministic decision rules, approvals, and DFM handling`
- Replacement rule: `Any change to state transitions, decision_json rules, or DFM flow must update this file before release.`

This document is governed by `docs/v10/00_V10_MASTER_CONSTITUTION.md` and `docs/v10/01_V10_SOURCE_HIERARCHY.md`. If any lower-level file conflicts with these authorities, this file must be updated to comply.

## Locked State Machine

The orchestrator state chain is:
- `S0 Uploaded`
- `S1 Converted`
- `S2 AssemblyReady`
- `S3 Analyzing`
- `S4 DFMReady`
- `S5 AwaitingApproval`
- `S6 Approved`
- `S7 ShareReady`

State skipping is forbidden.

## Deterministic Decision Rules

- `decision_json` is mandatory for orchestrator-backed decisions
- `rule_explanations` must be deterministic and traceable
- `rule_configs` is the runtime threshold source
- `rule_configs == empty` is a hard failure; code-default thresholds are forbidden
- LLM-generated manufacturing decisions are forbidden

## DFM Rules

- DFM reports must come from deterministic processing artifacts
- DFM routes may summarize findings, but they may not invent non-deterministic outcomes
- approvals must be auditable and tied to real session state

## Repo Anchors

- models: `backend/app/models/orchestrator.py`, `backend/app/models/rule_config.py`
- services: `services/orchestra/runtime_app/main.py`, `services/stell_ai/runtime_app/main.py`, `backend/app/services/rule_configs.py`
- routes: `backend/app/api/v1/routes/orchestrator.py`, `backend/app/api/v1/routes/approvals.py`, `backend/app/api/v1/routes/dfm.py`, `backend/app/api/v1/routes/stell_ai.py`
