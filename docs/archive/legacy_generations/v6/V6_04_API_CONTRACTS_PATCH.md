## Archive Note

- Reason retired: This V6 API patch is now covered by the V10 API and share contracts.
- Replaced by: `docs/v10/05_V10_API_CONTRACTS.md` and `docs/v10/08_V10_SHARE_AND_PUBLIC_ACCESS_CONTRACT.md`
- Historical value: Yes. It preserves the earlier API patch context.

# API Contracts Patch

Zorunlu endpointler:
POST /api/v1/approvals/{session_id}/approve
POST /api/v1/approvals/{session_id}/reject
GET  /api/v1/orchestrator/decision?session_id=

Share:
GET /s/{token}
- expire -> 410
- revoke -> access denied
