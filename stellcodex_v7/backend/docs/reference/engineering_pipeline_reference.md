# Engineering Pipeline Reference

This file is the update-friendly reference for the deterministic engineering
pipeline. Keep it in English so contributors can scan the implementation
surface quickly even when product-facing responses are localized.

Update this file when any of the following change:

- a new engineering artifact is introduced
- a persisted engineering table is added or removed
- a runtime output contract changes
- knowledge indexing begins consuming a new artifact

## Canonical flow

The current deterministic engineering chain is:

`geometry_metrics -> feature_map -> manufacturing_decision -> dfm_report -> cost_estimate -> manufacturing_plan -> engineering_report`

The STELL-AI layer may plan and narrate around this chain, but it does not own
the manufacturing decision authority.

## Source modules

- `app/core/engineering/geometry_metrics.py`
- `app/core/engineering/feature_extraction.py`
- `app/core/engineering/manufacturing.py`
- `app/core/engineering/dfm.py`
- `app/core/engineering/cost_estimation.py`
- `app/core/engineering/manufacturing_planner.py`
- `app/core/engineering/report_generation.py`
- `app/core/engineering_persistence.py`

## Runtime surfaces

- `app/stellai/engineering/analysis.py`
  Returns the full engineering artifact chain for deterministic analysis paths.
- `app/stellai/tools/engineering_tools.py`
  Exposes engineering outputs to the STELL-AI tool layer.
- `app/stellai/agents.py`
  Routes cost, planning, DFM, and report-oriented requests to the engineering
  precheck flow.
- `app/stellai/runtime.py`
  Summarizes deterministic engineering outputs in a safe user reply.

## Persisted tables

- `geometry_metrics`
- `feature_maps`
- `dfm_reports`
- `cost_estimates`
- `manufacturing_plans`
- `engineering_reports`
- `artifact_cache`
- `analysis_runs`
- `worker_nodes`

## Knowledge indexing

The knowledge engine currently normalizes and indexes these engineering-related
artifact types:

- `decision_json`
- `dfm_report`
- `engineering_report`
- `assembly_meta`

The engineering report exists so retrieval can reuse manufacturing process,
cost, planning, and improvement signals without reparsing raw runtime payloads.

## Language baseline

- Code comments, docstrings, and reference docs should use English.
- User-facing messages may be localized.
- Keyword matching may support multiple languages, but the implementation notes
  should still remain English-first.
