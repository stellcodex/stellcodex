# STELLAI_LIVE_ENDPOINT_TEST

## Endpoint URL Used
- `http://127.0.0.1:18000/api/v1/stell-ai/runtime/execute`

## Request Payload
```json
{
  "message": "show workflow status and decision",
  "tenant_id": "1",
  "project_id": "default",
  "allowed_tools": [
    "runtime.echo"
  ],
  "tool_requests": [
    {
      "name": "runtime.echo",
      "params": {
        "message": "live-endpoint-proof"
      }
    }
  ]
}
```

## Response Payload
```json
{
  "session_id": "sess_711d0c5081a34db8",
  "trace_id": "1db5e358-f2b7-4fe7-b6a8-07d3a7d1d1ec",
  "reply": "Tool results:\n- runtime.echo: ok\nNo grounded context was retrieved for this query.",
  "plan": {
    "graph_id": "tg_3f348f2e1ae04226",
    "nodes": [
      {
        "node_id": "n_12e6e0b1",
        "kind": "retrieve",
        "description": "retrieve relevant context"
      },
      {
        "node_id": "n_2c9b3498",
        "kind": "research",
        "description": "expand context if retrieval signal is weak"
      },
      {
        "node_id": "n_321097e4",
        "kind": "execute_tools",
        "description": "run allowlisted tools with permission checks"
      },
      {
        "node_id": "n_82cec89c",
        "kind": "memory_update",
        "description": "persist session and long-term memory"
      }
    ],
    "metadata": {
      "needs_research": true,
      "tool_count": 1,
      "session_memory_items": 0
    }
  },
  "retrieval": {
    "query": "show workflow status and decision",
    "embedding_dim": 128,
    "filtered_out": 44,
    "used_sources": [
      "artifacts",
      "repository",
      "uploads"
    ],
    "chunks": []
  },
  "tool_results": [
    {
      "tool_name": "runtime.echo",
      "status": "ok",
      "output": {
        "tenant_id": "16",
        "project_id": "default",
        "session_id": "sess_711d0c5081a34db8",
        "message": "live-endpoint-proof"
      }
    }
  ],
  "memory": {
    "session_count": 2,
    "working_count": 2,
    "long_term_count": 0
  }
}
```

## Agent Execution Trace
Observed in response `events`:
1. `runtime.started`
2. `memory.loaded`
3. `planner.planned`
4. `retriever.retrieved`
5. `researcher.expanded`
6. `executor.executed`
7. `memory.updated`
8. `runtime.completed`

Required agents observed:
- `planner`
- `retriever`
- `memory`
- `executor`
- `runtime`

## Success Confirmation
- Live endpoint request returned `200 OK`.
- Planner decision exists (`plan`).
- Retrieval results structure exists (`retrieval`).
- Memory update exists (`memory` + `memory.updated` event).
- Executor tool call exists (`runtime.echo` in `tool_results` and `executor.executed` event).
- Runtime final response exists (`reply` + `runtime.completed` event).

## Evidence Files
- `/root/workspace/evidence/stellai/stellai_live_endpoint_test.json`
- `/root/workspace/evidence/stellai/stellai_live_endpoint_request.json`
- `/root/workspace/evidence/stellai/stellai_live_endpoint_response.json`
- `/root/workspace/evidence/stellai/stellai_live_guest_auth.json`
- `/root/workspace/evidence/stellai/stellai_live_endpoint_openapi_match.txt`
- `/root/workspace/evidence/stellai/stellai_live_backend_tail.log`
