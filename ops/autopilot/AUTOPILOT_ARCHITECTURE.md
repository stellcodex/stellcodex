# AUTOPILOT ARCHITECTURE

- Entry point: `/root/workspace/scripts/stellcodex_autopilot.sh`
- Core engine: `/root/workspace/scripts/stellcodex_autopilot.py`
- Self-hosted frontend deploy: `/root/workspace/scripts/stellcodex_self_hosted_frontend_deploy.sh`
- Locking: `/root/workspace/scripts/stellcodex_lock.sh`
- Outputs: `_jobs/reports/autopilot/`
- Archive path: `gdrive:stellcodex/03_evidence/autopilot`
- Modes: `daily`, `weekly`, `deploy`, `closeout`
- Edge posture: public traffic may still be Vercel-backed, but autopilot separately verifies the direct self-hosted nginx path.
- Heavy checks: weekly mode relies on the latest release gate evidence and can be extended to rerun the gate with build disabled.
