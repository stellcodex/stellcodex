# STELLCODEX V7 MASTER — Technical Constitution (Binding)

STELLCODEX = CAD → Deterministic Decision → DFM → Approval → Secure Share.

Viewer, Share, AI Chat are modules; core product is:
- Orchestrator
- Deterministic Rule Engine
- DFM Risk Engine
- State Machine Enforcement

## ID CONTRACT (Release-Blocking)
- Single public identifier: file_id
- revision_id is not a public contract
- storage_key MUST NEVER appear in any public response body
- share URL must not expose file_id directly

## State Machine (Locked)
S0 Uploaded
S1 Converted
S2 AssemblyReady
S3 Analyzing
S4 DFMReady
S5 AwaitingApproval
S6 Approved
S7 ShareReady
State skipping is forbidden.

## decision_json (Mandatory)
For every file_id:
- decision_json JSONB NOT NULL
- rule_version required
- mode: brep|mesh_approx|visual_only
- confidence: 0..1
- manufacturing_method
- rule_explanations[] required
LLM manufacturing decision is forbidden.

## rule_configs (Mandatory)
Hardcoded thresholds are forbidden. Thresholds must come from rule_configs.

## Viewer Meta (Mandatory)
assembly_meta is required; without it status=ready is forbidden.
Part count = selectable occurrences (not mesh node count).

## Share Contract (Mandatory)
- token >= 64 random
- expires required
- expired => HTTP 410
- revoke immediate invalidation
- rate limit => 429 and audit

## Ops & Release Gate (Mandatory)
- daily DB dump + object mirror + integrity check
- weekly restore test + smoke gate
- deploy blocked unless all gates PASS
