# Founder Approval Policy

The following actions require explicit founder approval before execution:

1. Production data destructive operations (drop, purge, irreversible delete)
2. Security posture changes affecting public access
3. External connector credential rotation with service impact
4. Cross-organ authority boundary exceptions
5. Rollback to a snapshot older than 7 days

Approval record must include:
- approver identity
- timestamp
- reason
- scope
- rollback plan
