# STELLCODEX Orchestra

Isolated orchestration entrypoint under `ops/orchestra`.

## What This Runs
- **Gemini**: conductor (plan/router/merge)
- **Codex**: code writer (single writer)
- **Claude**: reviewer (single reviewer)
- **Abacus**: analyst (analysis/report)
- **Ollama local agents (optional)**: checklists/alternatives only

Safety flow is automatic and non-interactive:
- `DRY-RUN -> APPLY -> SMOKE/TEST -> AUTO-ROLLBACK`
- Quota-aware deferral and replay when cooldown expires

## Run (One Command)
```bash
cd ops/orchestra
./run.sh
```

Optional fail-fast smoke mode (bounded startup validation):
```bash
cd ops/orchestra
SMOKE_FAILFAST=1 SMOKE_MAX_TIME=120 ./run.sh
```
Optional profile probe timeout override:
```bash
cd ops/orchestra
PROFILE_MAX_TIME=10 ./run.sh
```

`run.sh` automatically:
- discovers provider keys from workspace config/env files
- writes `ops/orchestra/.env` without printing secrets
- starts/updates compose stack
- warms local Ollama models for free fallback
- runs `profile/mini` + smoke orchestration
- prints `READY` or `DEGRADED (needs paid keys)`
- optional: `SMOKE_FAILFAST=1` pins startup smoke to deterministic defer paths to avoid long role waits

## First-Time Profile
```bash
curl -X POST http://localhost:7010/profile/mini
```

## One-Command Usage (User Entry)
```bash
curl -X POST http://localhost:7010/orchestrate -H "Content-Type: application/json" -d '{"task":"..."}'
```

Local wrapper (recommended):
```bash
./orchestra.sh "..."
```

## Acceptance Test (A/B/C/D)
```bash
./acceptance.sh
```

Optional pin override in request body:
```json
{
  "task": "...",
  "pin": {
    "gemini": "gemini_conductor",
    "codex": "codex_executor",
    "claude": "claude_reviewer",
    "abacus": "abacus_analyst"
  }
}
```

## Ports And Health
- LiteLLM: `http://localhost:4000`
- Orchestrator: `http://localhost:7010`
- STELL.AI: `http://localhost:7020/stellai/status`
- Health: `curl -s http://localhost:7010/health`
- State: `curl -s http://localhost:7010/state`
- Quota: `curl -s http://localhost:7010/quota`

## Full Autonomous Mode
Start full loop with preflight, backup, orchestra, autopilot, watchdog, and STELL.AI:

```bash
cd /root/workspace/ops/orchestra
./autopilot.sh start /root/workspace/_jobs
```

Task inbox (supported: `.md`, `.txt`):

- `/root/workspace/_jobs/inbox/`

Output layout per task:

- `/root/workspace/_jobs/output/<task_id>/final_output.md`
- `/root/workspace/_jobs/output/<task_id>/routing.json`
- `/root/workspace/_jobs/output/<task_id>/results.json`
- `/root/workspace/_jobs/output/<task_id>/status.json`

Runtime logs/reports:

- `/root/workspace/_jobs/logs/PREFLIGHT_REPORT.md`
- `/root/workspace/_jobs/logs/PREFLIGHT_SNAPSHOT.json`
- `/root/workspace/_jobs/logs/events.jsonl`
- `/root/workspace/_jobs/logs/DAILY_REPORT_<YYYY-MM-DD>.md`

Manual controls:

```bash
./autopilot.sh status /root/workspace/_jobs
./autopilot.sh stop /root/workspace/_jobs
./watchdog.sh
```

## Optional Local Models (Ollama)
`run.sh` enables Ollama and tries to pull CPU-friendly models automatically.
Manual pull examples:
```bash
docker compose exec ollama ollama pull tinyllama
docker compose exec ollama ollama pull qwen2.5:0.5b
```

## Quota Cooldown Test Endpoint
Testing-only endpoint:
```bash
curl -X POST http://localhost:7010/quota/reset -H "Content-Type: application/json" -d '{"model":"codex_executor","cooldown_minutes":120}'
```

## Notes
- No secrets are committed; use `.env` only.
- State is persisted in `ops/orchestra/state/`.
- `routing_events.jsonl` is append-only.
- `_jobs/backups/<timestamp>/` is created before first execution and before startup.
