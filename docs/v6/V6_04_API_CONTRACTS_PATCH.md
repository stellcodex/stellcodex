# API Contracts Patch

Zorunlu endpointler:
POST /api/v1/approvals/{session_id}/approve
POST /api/v1/approvals/{session_id}/reject
GET  /api/v1/orchestrator/decision?session_id=

Share:
GET /s/{token}
- expire -> 410
- revoke -> access denied
