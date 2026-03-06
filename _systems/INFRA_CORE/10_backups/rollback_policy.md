# Rollback Policy

Rollback scopes:
1. Configuration rollback
2. Code rollback
3. Manifest rollback
4. Infrastructure rollback

Required steps:
- identify failure code
- freeze writes
- restore latest verified backup
- run smoke gate
- reopen traffic after health checks
