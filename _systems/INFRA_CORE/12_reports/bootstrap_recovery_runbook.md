# Bootstrap Recovery Runbook

1. Restore infrastructure prerequisites (network, storage, database, queue)
2. Restore manifests from `_systems`
3. Restore database snapshot and object mirror
4. Start ORCHESTRA runtime services
5. Start STELLCODEX runtime services
6. Run health + smoke + share contract checks
7. Re-enable scheduled watchdog and backups
