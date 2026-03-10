# Viewer Contract Report (V7 Audit)

Audit timestamp: 2026-03-08 (UTC)
Evidence bundle: `/root/workspace/evidence/v7_fix_run_20260308T032241Z`

## Assembly meta contract
Manifest/runtime includes required assembly fields:
- `occurrence_id`
- `part_id`
- `display_name`
- `children`
- GLTF index mapping

Evidence:
- `smoke/manifest.json`

## Part-count rule
- `part_count` is occurrence-based and consistent between manifest and file detail.

## Enforcement rule
- If `assembly_meta` removed from a `ready` file, status endpoint returns `failed`.
- DB status persists as `failed` (not only response-level).

Evidence:
- `smoke/ready_without_assembly_status.json` (`state=failed`)
- runtime DB check for same file (`status=failed`)

## Section verdict
PASS
