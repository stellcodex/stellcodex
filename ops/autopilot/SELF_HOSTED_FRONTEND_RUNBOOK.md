# SELF-HOSTED FRONTEND RUNBOOK

- Source repo default: `/tmp/stell-main/frontend`
- Live target: `/var/www/stellcodex/frontend`
- Deploy command: `bash /root/workspace/scripts/stellcodex_self_hosted_frontend_deploy.sh`
- Validation path: `curl -k --resolve stellcodex.com:443:127.0.0.1 https://stellcodex.com/`
- This flow updates the server-hosted frontend directly and does not wait for Vercel.
- Public traffic cutover still requires Cloudflare/DNS account access if the public edge is not already pointed at this server.
