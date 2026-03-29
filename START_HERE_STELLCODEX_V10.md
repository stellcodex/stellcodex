# START HERE — STELLCODEX V10
**STATE: LOCKED** | Generated: 2026-03-29

---

## CURRENT PHASE

```
current_phase: SELF_LEARNING_ACTIVE
```

---

## COMPLETED PHASES — LOCKED (NO REOPEN)

| Phase | Name | Status |
|-------|------|--------|
| V1–V7 | Legacy Builds | ARCHIVED |
| V8 | AI Ops Core | COMPLETE — LOCKED |
| V9 | Snapshot Pipeline + Async | COMPLETE — LOCKED |
| V10 | Self-Learning + State Lock | ACTIVE |

> **HARD RULE:** Completed phases CANNOT be reopened. No exceptions.

---

## FORBIDDEN OPERATIONS

```
FORBIDDEN:
  - UI_REBUILD          # Frontend architecture is frozen
  - V7_V8_CORE_REWORK   # Core engine is locked
  - FRONTEND_REDESIGN   # UI/UX contract is sealed
```

---

## ARCHITECTURE

```
STELLCODEX  = product layer (viewer, files, projects, quotes)
STELL-AI    = intelligence layer (learning, memory, orchestration)
ORCHESTRA   = execution layer (jobs, workers, async pipeline)
```

---

## INFRA AUTHORITY RULES

```
GITHUB  = CODE AUTHORITY    → source of truth for all code
DRIVE   = ARCHIVE AUTHORITY → permanent backup / snapshots
SERVER  = DISPOSABLE RUNTIME → can be rebuilt from GitHub + Drive
```

> The server is NOT the source of truth.
> If server state diverges from GitHub — GitHub WINS.
> If a snapshot is needed — restore from Drive.

---

## WHAT TO DO FIRST (every session)

1. Read `SYSTEM_STATE.json` — verify `current_phase`
2. Run `ops/preflight_context_guard.sh` — assert `CONTEXT_OK=1`
3. Check `OPERATOR_RULES.md` — do not violate any rule
4. Proceed with task

---

## RECOVERY

See `RECOVERY_BASELINE.md` for full restore procedure.
