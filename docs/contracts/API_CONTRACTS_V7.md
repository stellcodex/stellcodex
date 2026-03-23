# API Contracts (V7)

Required endpoints (minimum):

Auth
- `/api/v1/auth/guest` retired in V10 consolidation
- GET  /api/v1/auth/me

Files / Upload
- POST /api/v1/files/upload
- GET  /api/v1/files/{file_id}
- GET  /api/v1/files/{file_id}/status

Orchestrator
- POST /api/v1/orchestrator/start?file_id=...
- GET  /api/v1/orchestrator/decision?file_id=... (or session_id)
- GET  /api/v1/orchestrator/required-inputs?session_id=...

Approvals
- POST /api/v1/approvals/{session_id}/approve
- POST /api/v1/approvals/{session_id}/reject

DFM
- GET /api/v1/dfm/report?file_id=...

Share (Public)
- POST /api/v1/shares
- GET  /s/{token}  (expired => 410)
- POST /api/v1/shares/{share_id}/revoke

Error code standard:
400 validation
401 unauth
403 forbidden
404 not found
410 expired share
429 rate limit
5xx server
