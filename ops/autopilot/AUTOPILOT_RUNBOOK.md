# AUTOPILOT RUNBOOK

## Manual Commands

- `bash /root/workspace/scripts/stellcodex_autopilot.sh daily --archive`
- `bash /root/workspace/scripts/stellcodex_autopilot.sh weekly --archive`
- `bash /root/workspace/scripts/stellcodex_autopilot.sh deploy --archive`
- `bash /root/workspace/scripts/stellcodex_autopilot.sh closeout --archive`

## Failure Handling

- `FAIL`: treat as blocking and inspect the generated JSON plus evidence bundle.
- `PARTIAL`: investigate drift or missing external verification before claiming readiness.
- `BLOCKED`: external credentials or access are missing.
