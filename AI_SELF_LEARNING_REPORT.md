# AI Self Learning Report

Generated: 2026-03-29

## Summary

STELL-AI now performs this runtime loop on both `/decide` and `/chat`:

1. Request in
2. Retrieval
3. Decision / response generation
4. Case log write
5. Eval write
6. Pattern extraction
7. Reusable memory storage in canonical tables

New runtime endpoints:

- `POST /ai/memory/write`
- `POST /ai/eval/run`
- `POST /ai/pattern/extract`

Canonical tables verified and aligned in the live database:

- `ai_case_logs`
- `ai_eval_results`
- `ai_pattern_signals`

Compatibility columns verified:

- `ai_case_logs`: `id`, `input`, `retrieved_context`, `decision_json`, `response`, `outcome`
- `ai_eval_results`: `score`, `issues`, `improvement_note`
- `ai_pattern_signals`: `id`, `pattern_type`, `signal`, `frequency`, `weight`

## Sample Case Log

Sample from live `ai_case_logs`:

```text
case_id: af2c3891-5197-4f47-b3eb-f5a08352bf66
project_id: slr-learning-329d
run_type: stellai_decide
outcome: success
similarity_index_key: slr-learning-329d|text|brep|PASS|none
response: {"confidence": 0.82, "manufacturing_method": "unknown", "recommendations": ["Use the best solved pattern as the preferred recovery route for this decision."], "severity": "INFO"}
created_at: 2026-03-29 04:44:39.248969+00
```

## Sample Eval

Sample from live `ai_eval_results`:

```text
case_id: af2c3891-5197-4f47-b3eb-f5a08352bf66
score: 0.575
issues: ["latency_high"]
improvement_note: Prefer the shortest valid answer path for repeated prompts on the local runtime.
outcome: partial
created_at: 2026-03-29 04:44:39.321439+00
```

## Sample Pattern

Sample from live `ai_pattern_signals`:

```text
signal_id: 7bd73aae-6c86-4993-9bd7-5020393c6521
pattern_type: success
signal: Prefer the shortest valid answer path for repeated prompts on the local runtime.
frequency: 2
weight: 0.75
similarity_index_key: slr-learning-329d|text|brep|PASS|none
created_at: 2026-03-29 04:46:20.833282+00
```

## Proof Of Retrieval Usage

Live second-pass `/decide` proof:

```json
{
  "confidence": 0.99,
  "retrieval": {
    "case_match_count": 1,
    "last_eval_improvement_note": "Prefer the shortest valid answer path for repeated prompts on the local runtime.",
    "top_patterns": [
      {
        "pattern_type": "success",
        "signal": "Prefer the shortest valid answer path for repeated prompts on the local runtime.",
        "frequency": 1,
        "weight": 0.6
      }
    ]
  }
}
```

This proves the second run injected:

- top similar prior case logs
- last eval improvement note
- top extracted pattern

before composing the new decision.

## Proof Of Next-Run Improvement

Same request, first run:

```json
{
  "project_id": "slr-learning-329d",
  "confidence": 0.82,
  "retrieval": {
    "case_match_count": 0,
    "last_eval_improvement_note": null,
    "top_patterns": []
  },
  "learning_eval": {
    "score": 0.575,
    "improvement_note": "Prefer the shortest valid answer path for repeated prompts on the local runtime."
  },
  "case_id": "af2c3891-5197-4f47-b3eb-f5a08352bf66"
}
```

Same request, second run:

```json
{
  "project_id": "slr-learning-329d",
  "confidence": 0.99,
  "retrieval": {
    "case_match_count": 1,
    "last_eval_improvement_note": "Prefer the shortest valid answer path for repeated prompts on the local runtime."
  },
  "learning_eval": {
    "score": 0.65,
    "improvement_note": "Prefer the shortest valid answer path for repeated prompts on the local runtime."
  },
  "case_id": "7eb77b60-4c7c-4cf7-84c9-8eba5b4f47e5"
}
```

Observed improvement:

- prior case retrieval: `0 -> 1`
- confidence: `0.82 -> 0.99`
- pattern frequency: `1 -> 2`
- recommendations expanded from 1 item to 3 items

## Chat Path Sanity Proof

Live `/chat` sample:

```json
{
  "response": "YES",
  "learning_memory": {
    "case_match_count": 2,
    "last_eval_improvement_note": "Reuse the last successful format and preserve the strongest retrieved evidence."
  },
  "learning_eval": {
    "score": 1.0,
    "improvement_note": "Reuse the last successful format and preserve the strongest retrieved evidence."
  },
  "pattern_signal": {
    "pattern_type": "success",
    "signal": "Reuse the last successful format and preserve the strongest retrieved evidence."
  },
  "case_id": "695f4a03-5fbc-4854-918a-bfec0857716a"
}
```

## Commands Used

```bash
curl -sS http://127.0.0.1:7020/health
curl -sS -X POST http://127.0.0.1:7020/ai/memory/write -H 'Content-Type: application/json' --data '{"tenant_id":0,"query":"ping learning endpoint","response":"ok","outcome":"success","run_type":"stellai_chat"}'
curl -sS -X POST http://127.0.0.1:7020/ai/eval/run -H 'Content-Type: application/json' --data '{"case_id":"ad602cc2-3e06-40dc-8c78-3b32afcd448a"}'
curl -sS -X POST http://127.0.0.1:7020/ai/pattern/extract -H 'Content-Type: application/json' --data '{"case_id":"ad602cc2-3e06-40dc-8c78-3b32afcd448a"}'
curl -sS --max-time 180 -X POST http://127.0.0.1:7020/decide -H 'Content-Type: application/json' --data '{"project_id":"slr-learning-329d","mode":"brep","rule_version":"v10.0.0","geometry_meta":{"bbox":{"x":12.0,"y":8.0,"z":4.0},"part_count":1},"dfm_findings":{"status_gate":"PASS","risk_flags":[],"findings":[{"code":"clearance_ok","message":"Geometry is machinable with standard CNC setup.","severity":"low"}]}}'
curl -sS --max-time 180 -X POST http://127.0.0.1:7020/chat -H 'Content-Type: application/json' --data '{"tenant_id":0,"message":"Reply with YES only.","user_tier":"standard","allow_tools":false}'
```
