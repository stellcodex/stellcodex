# Rate Limit + Audit Spec (V7)

Rate limit windows (minimum):
- auth:         10 req / 60s / IP
- upload:       20 req / 60s / user
- share_resolve:30 req / 60s / IP

Redis key format:
rl:{scope}:{identifier}:{window_start_epoch}

Behavior:
- When exceeded: HTTP 429
- Must write audit_event:
  event_type="RATE_LIMIT"
  target_type="endpoint"
  meta_json includes scope, identifier, limit, window

Audit events are append-only.
Secrets must be masked in logs and meta_json.
