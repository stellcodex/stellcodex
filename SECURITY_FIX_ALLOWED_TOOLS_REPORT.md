# SECURITY_FIX_ALLOWED_TOOLS_REPORT

## Root Cause
`/api/v1/stell-ai/runtime/execute` accepted `allowed_tools` from client payload and forwarded it into `RuntimeContext.allowed_tools`, so clients could attempt self-granted tool permissions.

## Exact Code Paths Changed
- `/root/workspace/stellcodex_v7/backend/app/api/v1/routes/stell_ai.py`
  - Added server authority resolver and role policy constants: lines 117-176.
  - `RuntimeExecuteIn.allowed_tools` retained but explicitly documented as ignored: lines 33-34.
  - Replaced client-derived permissions with server-derived permissions in runtime context: lines 196-212.
- `/root/workspace/stellcodex_v7/backend/app/stellai/tools/__init__.py`
  - Added `_error_result(...)` structured error payload helper: lines 203-210.
  - Updated denied/failed paths in `_execute_one(...)` to return structured `output.error.reason`: lines 95, 103-126, 131-133.
- `/root/workspace/stellcodex_v7/backend/tests/test_stellai_allowed_tools_authority.py`
  - Added authority-focused tests: lines 80-148.
- `/root/workspace/stellcodex_v7/backend/scripts/stellai_allowed_tools_fix_evidence.py`
  - Added reproducible security evidence generator for client-ignored permissions and authority-backed access behavior.

## Old Insecure Behavior
- API request body field `allowed_tools` was treated as authority and inserted directly into `RuntimeContext`.
- Permission checks existed in executor, but authority source was untrusted client input.

## New Secure Behavior
- API ignores client authority for tool permissions.
- Effective allowed tools are derived server-side via `_resolve_server_allowed_tools(...)` from trusted principal context.
- Runtime/executor now receives authority-backed `allowed_tools` only.
- Unknown or low-trust role defaults to least privilege (`runtime.echo` only).
- Denied actions return structured payloads (`{"error": {"reason": ...}}`) and are audited.

## Server-Side Permission Resolution Model
Implemented in `/root/workspace/stellcodex_v7/backend/app/api/v1/routes/stell_ai.py:160-176`:
- `guest` -> `_GUEST_TOOLS`
- `user` + privileged role (`admin|owner|founder|service`) -> `GLOBAL_ALLOWLIST`
- `user` + standard role (`user|member|engineer|operator|analyst`) -> `_STANDARD_USER_TOOLS`
- unknown/missing role -> `_LEAST_PRIVILEGE_TOOLS`

This model is deterministic, server-controlled, and does not consume client `allowed_tools` as an authority source.

## Tests Run
Commands executed:

```bash
cd /root/workspace/stellcodex_v7/backend
pytest -q tests/test_stellai_allowed_tools_authority.py tests/test_stellai_tool_ecosystem.py tests/test_stellai_runtime.py
```

Result:
- `19 passed in 21.19s` (latest artifact-backed run)

Additional regression check:

```bash
cd /root/workspace/stellcodex_v7/backend
pytest -q tests/test_phase2_event_pipeline.py tests/test_orchestrator_core.py
```

Result:
- `10 passed in 14.07s`

Permission token check:

```bash
cd /root/workspace/stellcodex_v7/backend
DATABASE_URL='postgresql://test:test@localhost:5432/test_stellcodex' \
JWT_SECRET='test-secret-key-for-unit-tests-only-32chars!!' \
PYTHONPATH=. python3 - <<'PY'
from app.stellai.tools import SafeToolExecutor, ToolCall
from app.stellai.types import RuntimeContext
exe = SafeToolExecutor(allowlist=frozenset({'runtime.echo'}))
for token in ['scope:stellai.runtime.read', 'category:core', 'runtime.echo']:
    ctx = RuntimeContext(tenant_id='1', project_id='default', principal_type='user', principal_id='u1', session_id='s', trace_id='t', allowed_tools=frozenset({token}))
    res = exe.execute_calls(context=ctx, db=None, calls=[ToolCall(name='runtime.echo', params={'message': token})])[0]
    print(token, res.status, res.reason)
PY
```

Result:
- `scope:stellai.runtime.read ok None`
- `category:core ok None`
- `runtime.echo ok None`

## Evidence Produced
Generated/verified artifacts:
- `/root/workspace/evidence/stellai/tool_client_allowed_tools_ignored.json`
- `/root/workspace/evidence/stellai/tool_authority_backed_permissions.json`
- `/root/workspace/evidence/stellai/tool_permission_fix_summary.json`
- `/root/workspace/evidence/stellai/tool_permission_fix_audit.jsonl`
- `/root/workspace/evidence/stellai/tool_permission_fix_pytest_20260308T074130Z.txt`

Key evidence outcomes:
- client payload requested `write_file`, but effective guest permissions excluded it.
- guest `write_file` call denied with `tool_not_permitted_for_request`.
- admin role allowed `write_file` through server-authority policy.
- denied action present in structured audit log.

## Final Security Blocker Status
Resolved.
- Client-supplied `allowed_tools` no longer grants permissions.
- Runtime/executor receives allowed tools from trusted server policy only.
