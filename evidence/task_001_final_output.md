MERGED PLAN
1. Confirm scope and constraints.
2. Apply minimal patch or patch-plan output.
3. Run smoke tests and inspect logs.
4. Roll back immediately on failed checks.

APPLY STEPS
- Use Codex output if unified diff is present; otherwise follow degraded patch-plan.
- Execute only isolated `ops/orchestra` changes.

TESTS/SMOKE
- curl -s http://localhost:7010/state
- curl -s -X POST http://localhost:7010/orchestrate -H 'Content-Type: application/json' -d '{"task":"smoke"}'

ROLLBACK PLAN
- Revert modified files in ops/orchestra and restart compose services.

READINESS
- FAIL

DEFERRED SUMMARY
- {"newly_deferred": [{"id": "1f9df530-6696-424f-9205-e7be3341ff83", "role": "gemini", "task_type": "plan", "model": "gemini_conductor", "earliest_retry_at": "2026-03-05T15:49:51.546144Z", "reason": "primary_model_in_cooldown"}, {"id": "f60a22b9-a5cb-4991-a8fa-456a7d94abf7", "role": "codex", "task_type": "code", "model": "local_reason", "earliest_retry_at": "2026-03-05T15:49:51.548158Z", "reason": "primary_model_in_cooldown"}, {"id": "2804de17-f687-4281-b0ee-6955afacab6c", "role": "abacus", "task_type": "analysis", "model": "abacus_analyst", "earliest_retry_at": "2026-03-05T15:49:51.549365Z", "reason": "primary_model_in_cooldown"}, {"id": "d42080c1-5bdc-4e32-bfa8-4bab3039cb4e", "role": "claude", "task_type": "review", "model": "local_reason", "earliest_retry_at": "2026-03-05T15:49:51.550690Z", "reason": "primary_model_in_cooldown"}, {"id": "656adb6d-a2b5-4e06-8738-0afab93b18ba", "role": "local_ops_check", "task_type": "ops_check", "model": "local_fast", "earliest_retry_at": "2026-03-05T15:49:51.551893Z", "reason": "no_available_model"}, {"id": "aa23eadb-43c5-4643-9f79-c8397c43f05b", "role": "local_doc", "task_type": "doc", "model": "local_fast", "earliest_retry_at": "2026-03-05T15:49:51.552897Z", "reason": "no_available_model"}], "queue_count": 27}