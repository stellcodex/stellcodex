# DFM Engine Report (V7 Audit)

Audit timestamp: 2026-03-08 (UTC)
Evidence bundle: `/root/workspace/evidence/v7_fix_run_20260308T032241Z`

## Endpoint verification
`GET /api/v1/dfm/report` response includes:
- `mode`
- `confidence`
- `rule_version`
- `rule_explanations`
- `wall_risks`
- `draft_risks`
- `undercut_risks`
- `shrinkage_warnings`
- `recommendations`

Evidence file:
- `smoke/dfm_report.json`

## Persistence verification
Smoke + DB check verified persisted artifact:
- `metadata.dfm_report_json` exists
- `metadata.dfm_report_json.recommendations` is array

Evidence:
- `smoke/summary.json` contains `dfm_persist_count: 1`
- direct DB query after gate confirms persisted rows > 0.

## Section verdict
PASS
