#!/usr/bin/env bash
set -euo pipefail

cat <<'TXT'
Provider live audit quickstart
==============================

1) Populate credentials (no secrets are printed by this script):
   - Use template:
     /root/workspace/audit/STELL_SYSTEM_CORE/10_reports/provider/PROVIDER_AUDIT_ENV_TEMPLATE.env
   - Scope guide:
     /root/workspace/audit/STELL_SYSTEM_CORE/10_reports/provider/PROVIDER_AUDIT_SCOPE_GUIDE.md
   - Preferred (secure):
     mkdir -p /root/workspace/.secrets && chmod 700 /root/workspace/.secrets
     cp /root/workspace/audit/STELL_SYSTEM_CORE/10_reports/provider/PROVIDER_AUDIT_ENV_TEMPLATE.env /root/workspace/.secrets/provider_audit.env
     chmod 600 /root/workspace/.secrets/provider_audit.env
   - Put keys into one of (fallback):
     /root/workspace/.secrets/provider_audit.env
     /root/workspace/.env
     /root/stell/.env
     /root/stell/webhook/.env

2) Validate credential presence (no value output):
   /root/workspace/audit/scripts/provider_credential_status.sh

3) Run live provider audit:
   /root/workspace/audit/scripts/provider_live_audit.sh

4) Run monthly audit (includes provider live audit):
   /root/workspace/audit/scripts/monthly_prompt_audit.sh

5) One-shot full finalize flow:
   /root/workspace/audit/scripts/finalize_provider_audit.sh

6) Check latest outputs:
   ls -1t /root/workspace/audit/STELL_SYSTEM_CORE/10_reports/provider/provider_live_audit_*.md | head -n1
   ls -1t /root/workspace/audit/STELL_SYSTEM_CORE/10_reports/provider/provider_credential_status_*.md | head -n1
   ls -1t /root/workspace/audit/STELL_SYSTEM_CORE/10_reports/monthly/monthly_audit_*.md | head -n1
TXT
