# OPERATOR RULES — STELLCODEX V10
**Authority: LOCKED** | Violation = STOP IMMEDIATELY

---

## HARD RULES

### 1. NEVER reopen completed phases
Phases V1–V9 are sealed. Any agent or operator attempting to "redo" or "revisit" a prior phase
must halt and escalate. There is no exception.

### 2. NEVER rebuild the UI
The frontend architecture is frozen. `UI_REBUILD` is forbidden.
UI bug fixes follow the patch process — not a redesign cycle.

### 3. NEVER assume missing core
If a core component appears absent, check GitHub before concluding it is missing.
The server is disposable — absence on server ≠ absence in repo.

### 4. ALWAYS read SYSTEM_STATE.json first
Every session, every agent, every execution:
```
cat SYSTEM_STATE.json | jq .current_phase
```
If `current_phase` is not `SELF_LEARNING_ACTIVE` — STOP and report.

### 5. ALWAYS run preflight before execution
```
./ops/preflight_context_guard.sh
```
Must output `CONTEXT_OK=1` before any task proceeds.

### 6. SERVER = DISPOSABLE
The runtime server can be destroyed and rebuilt.
Never treat server state as canonical.
Never make irreversible changes to server-only state.

### 7. GITHUB = SOURCE OF TRUTH
All code changes must be committed and pushed.
Unpushed changes are at risk. Do not leave code only on server.

### 8. DRIVE = PERMANENT STORAGE
All snapshots, backups, and archives must be synced to Google Drive.
Drive path: `gdrive:STELLCODEX_BACKUPS/`

---

## FORBIDDEN OPERATIONS (machine-enforceable)

```json
[
  "UI_REBUILD",
  "CORE_REWRITE",
  "FRONTEND_RESET",
  "PHASE_REOPEN",
  "SERVER_AS_AUTHORITY"
]
```

---

## ESCALATION

If any rule conflict arises, escalate to human operator immediately.
Do not resolve rule conflicts autonomously.
