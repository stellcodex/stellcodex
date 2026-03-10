# Rule Engine Report (V7 Audit)

Audit timestamp: 2026-03-08 (UTC)
Code evidence:
- `/root/workspace/stellcodex_v7/backend/app/core/rule_engine.py`
- `/root/workspace/stellcodex_v7/backend/app/services/orchestrator_engine.py`

## Deterministic rule coverage
Implemented deterministic rules:
- quantity threshold
- tolerance impact
- wall thickness
- draft requirement
- undercut detection
- shrinkage logic
- volume/quantity conflict

Each rule returns:
- `rule_id`
- `triggered`
- `severity`
- `explanation`
- `reference`
- `deterministic_reasoning`

## Threshold source
Thresholds loaded from `rule_configs` (not hardcoded gate constants).
Evidence: schema gate listed enabled rule keys including `volume_mm3_high`, `tolerance_mm_tight`, `wall_mm_min`, `wall_mm_max`, `draft_min_deg`, `undercut_count_warn`, `shrinkage_*`, `volume_quantity_conflict_limit`.

## Runtime proof
- Contract tests passed in `/root/workspace/evidence/v7_fix_run_20260308T032241Z/contract_tests.log`.

## Section verdict
PASS
