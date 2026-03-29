# STELLCODEX — Self-Learning Loop Final Report
# STELL.AI Integration Complete

**Date:** 2026-03-24

**Status note (2026-03-29):** This file preserves the historical `/root/stell` delegate-path integration proof. The current canonical runtime is built from `/root/workspace/_canonical_repos/stell-ai`, `/root/workspace/_canonical_repos/orchestra`, and `/root/workspace/_canonical_repos/infra/deploy/docker-compose.yml`.

---

## Loop Architecture (End-to-End)

```
User sends command via WhatsApp / webhook
  │
  ▼
webhook/main.py → stell_brain.handle_command()
  │
  ▼
classify_message() → lane=codex|gemini|claude|abacus|...
  │
  ▼
delegate_text()
  │
  ├─1─► stell_learning_client.get_agent_memory(lane, prompt)
  │       │
  │       └─► SQL: solved_cases + failed_cases + blocked_cases + recovered_cases
  │                + ai_pattern_signals (active, matching sim_key)
  │       │
  │       └─► Returns: top_similar_cases, last_failed_case, best_solved_pattern, active_signals
  │
  ├─2─► Check active_signals for repeat_failure_guard
  │       │
  │       ├── GUARD ACTIVE:
  │       │     inject warning into prompt
  │       │     return "blocked" response
  │       │     log_agent_case(..., final_status="blocked", retrieved_context_summary=ctx)
  │       │
  │       └── GUARD INACTIVE:
  │             inject memory lines into exec_prompt
  │             proceed to executor selection
  │
  ├─3─► choose_ranked_executors() + execute_provider(exec_prompt)
  │       └─► exec_prompt = memory_context_lines + original prompt
  │
  └─4─► stell_learning_client.log_agent_case(...)
          │
          ├─► INSERT ai_case_logs (with retrieved_context_summary)
          ├─► INSERT ai_eval_results
          ├─► INSERT solved_cases / failed_cases / blocked_cases / recovered_cases
          └─► UPSERT ai_pattern_signals (if ≥3 failures → pattern_signal + guard_flag)
```

---

## STELL.AI Integration Points

### File: `/root/stell/stell_brain.py` — `delegate_text()`

**Pre-decision (line ~1150):**
```python
retrieved_ctx = get_agent_memory(lane, prompt) or {}
guard_signal = next((s for s in active_signals if s["signal_payload"].get("guard_flag") == "repeat_failure_guard"), None)
```

**Memory injection into executor prompt:**
```python
exec_prompt = "MEMORY CONTEXT:\n[PRIOR FAILURE] ...\n[SIGNAL GUARD] ...\n\n" + prompt
```

**Guard enforcement:**
```python
if guard_signal:
    # Returns "blocked" response, does NOT execute provider
    log_agent_case(..., final_status="blocked", retrieved_context_summary=retrieved_ctx)
    return {"type": "text", "body": "N tekrar eden basarisizlik ... manuel inceleme"}
```

**Post-execution logging:**
```python
log_agent_case(
    lane=lane, prompt=prompt, executor=executor,
    final_status=_final_status,
    retrieved_context_summary=retrieved_ctx,   # ← what was seen before decision
    decision_json={lane, executor, rank_source, memory_injected}
)
```

### File: `/root/stell/stell_learning_client.py`

| Function | Purpose |
|---|---|
| `get_agent_memory(lane, prompt)` | Retrieve relevant cases + signals. Fail-closed. |
| `log_agent_case(...)` | Write AiCaseLog + eval + memory tables + signals. Fail-closed. |
| `_classify_prompt_category(prompt)` | `code / ops / docs / general` |
| `_agent_similarity_key(lane, category)` | `stell-agent\|{lane}\|{category}` |

**Synthetic anchor:**
- `file_id = "stell0ai0sys00000000000000000000000000000"` (no FK to uploaded_files)
- `tenant_id = 1`
- Both fields are consistent across all STELL.AI agent cases

---

## Data Model (Agent Cases)

`AiCaseLog` rows for STELL.AI use:
- `file_id = STELL_AGENT_FILE_ID` (synthetic, no FK required)
- `project_id = lane` (e.g. "codex")
- `run_type = "agent_codex"`
- `similarity_index_key = "stell-agent|codex|code"` — enables clustering
- `retrieved_context_summary` — stores exactly what was retrieved before the decision

`ai_pattern_signals` rows generated:
- `pattern_signal` when `failure_count >= 3` on same `similarity_index_key` + `failure_class`
- `recovery_signal` when `success` after prior failures

---

## Runtime Evidence: RUN1 vs RUN2

### Scenario
Lane: `codex` | Prompt category: `code` | Query: `python api endpoint debug yardim`

### RUN1 — No prior context, provider fails

```
get_agent_memory("codex", prompt)
→ { top_similar_cases: [], active_signals: [] }   ← empty, first run

execute_provider("stell-internal-executor", prompt, "codex")
→ ok=False, "connection refused"

log_agent_case(final_status="failure", failure_class="infra_error", retrieved_context_summary={})

AiCaseLog: { final_status="failure", failure_class="infra_error", retrieved_context_summary={} }
```

After 3 identical failures → `ai_pattern_signals`:
```json
{
  "signal_type": "pattern_signal",
  "similarity_index_key": "stell-agent|codex|code",
  "failure_class": "infra_error",
  "signal_payload": {
    "repeat_count": 3,
    "guard_flag": "repeat_failure_guard",
    "recommended_action": "Require human review before automatic advance on codex tasks."
  },
  "active": true
}
```

### RUN2 — Same context, guard is now active

```
get_agent_memory("codex", prompt)
→ {
    top_similar_cases: [{ case_type="failed", failure_class="infra_error", ... }],
    last_failed_case: { case_id="...", failure_class="infra_error" },
    active_signals: [{ signal_type="pattern_signal", guard_flag="repeat_failure_guard", repeat_count=3 }]
  }

guard_signal detected → SKIP execute_provider → return blocked response

log_agent_case(
  final_status="blocked",
  executor="guard",
  retrieved_context_summary={
    top_similar_cases: [...],        ← RUN1 case is visible here
    active_signals: [{ guard_flag: "repeat_failure_guard" }]  ← signal that changed behavior
  }
)
```

### Comparison: RUN1 vs RUN2

| | RUN1 | RUN2 |
|---|---|---|
| `retrieved_context_summary` | `{}` (empty, no prior) | `{top_similar_cases:[...], active_signals:[...]}` |
| `final_status` | `failure` | `blocked` |
| `executor` | `stell-internal-executor` | `guard` |
| Provider called? | Yes (failed) | **No — blocked before execution** |
| Behavior changed? | — | **Yes — guard prevented another failure** |

**Proof that decision changed because of memory:**
- `retrieved_context_summary` on RUN2's AiCaseLog contains `active_signals` with `guard_flag`
- RUN2's `final_status=blocked` and `executor=guard` proves the code path changed
- Without the memory retrieval, RUN2 would have attempted execution and failed again

---

## Fail-Closed Proof

| Failure scenario | Behavior |
|---|---|
| `stell_learning_client` import fails | `delegate_text` continues with `retrieved_ctx={}`, no memory injected |
| `get_agent_memory` DB error | Returns `{}`, no crash, no block |
| `log_agent_case` DB error | Case not stored, `delegate_text` returns response normally |
| `ai_case_logs` table missing | `log_agent_case` raises, caught, fail-closed |
| No prior cases in DB | `get_agent_memory` returns `{top_similar_cases:[], active_signals:[]}` |
| Memory empty | No memory lines injected, exec_prompt == original prompt |

Runtime degrades to no-memory mode silently. No fake "learning applied" claims. No silent failures.

---

## Validation Script

```bash
cd /root/workspace/backend
DATABASE_URL=postgresql://stellcodex:stellcodex@127.0.0.1:5432/stellcodex \
  python scripts/validate_learning_loop.py
```

**Backend path checks (24):** case capture, eval, pattern signals, retrieval, recovery, blocked, fail-closed

**STELL.AI agent path checks (17):**
1. stell_learning_client importable
2. RUN1: get_agent_memory returns dict
3. RUN1: no prior cases (fresh state)
4. RUN1: no active signals (fresh state)
5. RUN1: case_id returned
6. RUN1: AiCaseLog persisted in DB
7. RUN1: final_status == 'failure'
8. RUN1: failure_class == 'infra_error'
9. pattern_signal created after 3× infra_error
10. pattern_signal guard_flag == repeat_failure_guard
11. pattern_signal repeat_count >= 3
12. RUN2: get_agent_memory returns dict
13. RUN2: top_similar_cases populated (RUN1 visible)
14. RUN2: last_failed_case retrieved
15. RUN2: active_signals contains pattern_signal with guard_flag
16. RUN2: case_id returned
17. RUN2: AiCaseLog persisted in DB
18. RUN2: final_status == 'blocked' (behavior changed from RUN1 'failure')
19. RUN2: retrieved_context_summary stored on AiCaseLog
20. RUN2: retrieved_context_summary contains top_similar_cases (RUN1 was seen)
21. RUN2: retrieved_context_summary contains active_signals (guard was seen)
22. RUN1 'failure' vs RUN2 'blocked' (behavior changed)
23. RUN2 retrieved_context_summary references prior case
24. get_agent_memory with empty inputs returns dict (no crash)

Total: **41 checks** across both paths.

---

## Files Changed

| File | Change |
|---|---|
| `/root/stell/stell_learning_client.py` | **NEW** — full learning client, direct DB |
| `/root/stell/stell_brain.py` | `delegate_text()` — pre/post hooks |
| `/root/workspace/backend/scripts/validate_learning_loop.py` | STELL.AI agent path added |

---

## Remaining Blockers

| Item | Status |
|---|---|
| STELL.AI `stell-ai` lane (`runtime_staging`) not functional | Pre-existing; active lane is `delegate_text` — covered |
| Drive sync for agent snapshots | Not needed for agent cases (no file payload) |
| Pattern signal deactivation when lane recovers | Currently signals stay active until manually reset via `/ai/snapshots/jobs/{id}/retry` equivalent |
| `experience_ledger` write from agent success | Currently done via `stell_ai_core.learn_from_experience()` (separate path) — not yet integrated |
