# GitHub / Repo Normalization Plan

Updated: 2026-03-08 (UTC)

## Target Repositories
- `stell-ai`
- `orchestra`
- `stellcodex`
- `infra`

Each boundary must expose:
- `/src`
- `/docs`
- `/deploy`
- `/scripts`
- `/tests`

## Current Implemented Mapping
- `stell-ai/src -> /root/workspace/AI/stell_ai`
- `orchestra/src -> /root/workspace/ops/orchestra/orchestrator`
- `stellcodex/src -> /root/workspace/stellcodex_v7/backend/app`
- `infra/deploy -> /root/workspace/stellcodex_v7/infrastructure/deploy`

## Boundary Enforcement Rules
- No cross-boundary ownership writes (code or data) without explicit contract.
- Public API contract stays in STELLCODEX and remains `file_id`-only.
- ORCHESTRA owns execution fabric and job pipelines.
- STELL.AI owns memory and retrieval logic.

## Physical Cutover Status
1. Separate remotes created:
   - `https://github.com/stellcodex/stell-ai`
   - `https://github.com/stellcodex/orchestra`
   - `https://github.com/stellcodex/stellcodex`
   - `https://github.com/stellcodex/infra`
2. Per-repo CI gating in place:
   - `stell-ai`: `boundary-gate` latest run `success`
   - `orchestra`: `boundary-gate` latest run `success`
   - `infra`: `boundary-gate` latest run `success`
   - `stellcodex`: `stellcodex-ci` latest run `success`
3. Branch standardization complete:
   - `stell-ai` default branch: `main`
   - `orchestra` default branch: `main`
   - `infra` default branch: `main`
   - `stellcodex` default branch: `main`
4. Branch protection API attempt documented:
   - `stellcodex/main`: required checks `backend-contracts`, `frontend-release-gate`, strict=true, enforce_admins=true.
   - `stell-ai/main`, `orchestra/main`, `infra/main`: required check `verify-boundary-layout`, strict=true, enforce_admins=true.
   - Evidence: `/root/workspace/evidence/github_branch_protection_status_20260308T0525Z.txt`

## Implemented Prep Automation
- Boundary shape validator: `/root/workspace/scripts/verify_boundary_layout.sh`
- Split bundle generator: `/root/workspace/scripts/prepare_repo_split.sh`
- Latest split bundle output: `/root/workspace/_runs/repo_split_20260308T015347Z`
