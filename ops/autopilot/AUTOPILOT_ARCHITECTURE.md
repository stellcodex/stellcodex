# AUTOPILOT ARCHITECTURE

- Entry point: `/root/workspace/scripts/stellcodex_autopilot.sh`
- Core engine: `/root/workspace/scripts/stellcodex_autopilot.py`
- Locking: `/root/workspace/scripts/stellcodex_lock.sh`
- Outputs: `_jobs/reports/autopilot/`
- Archive path: `gdrive:stellcodex/03_evidence/autopilot`
- Modes: `daily`, `weekly`, `deploy`, `closeout`
- Heavy checks: weekly mode relies on the latest release gate evidence and can be extended to rerun the gate with build disabled.
