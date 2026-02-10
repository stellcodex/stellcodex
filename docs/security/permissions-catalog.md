# Permission Catalog

Bu dokuman rbac.policy.json icinden otomatik cikarilmistir.

| Permission Key | Description | Surface | Critical (approval_required) |
|---|---|---|---|
| admin.comments.disable_on_file | Not provided in policy | backend endpoint | no |
| admin.comments.enable_on_file | Not provided in policy | backend endpoint | no |
| admin.files.archive | Not provided in policy | backend endpoint | no |
| admin.files.delete | Not provided in policy | backend endpoint | yes |
| admin.files.hide | Not provided in policy | backend endpoint | no |
| admin.files.purge_versions | Not provided in policy | backend endpoint | yes |
| admin.files.read | Not provided in policy | frontend route / backend endpoint | no |
| admin.files.storage_purge | Not provided in policy | backend endpoint | yes |
| admin.files.unarchive | Not provided in policy | backend endpoint | no |
| admin.files.unhide | Not provided in policy | backend endpoint | no |
| admin.files.view_metadata | Not provided in policy | backend endpoint | no |
| admin.files.view_processing_history | Not provided in policy | backend endpoint | no |
| admin.library.assign_category | Not provided in policy | backend endpoint | no |
| admin.library.curate_basic | Not provided in policy | unmapped | no |
| admin.library.feature | Not provided in policy | backend endpoint | no |
| admin.library.read | Not provided in policy | backend endpoint | no |
| admin.library.remove_from_library | Not provided in policy | backend endpoint | no |
| admin.library.unfeature | Not provided in policy | backend endpoint | no |
| admin.notes.read | Not provided in policy | backend endpoint | no |
| admin.notes.remove | Not provided in policy | backend endpoint | no |
| admin.presentations.delete | Not provided in policy | backend endpoint | yes |
| admin.presentations.lock | Not provided in policy | backend endpoint | no |
| admin.presentations.read | Not provided in policy | backend endpoint | no |
| admin.presentations.unlock | Not provided in policy | backend endpoint | no |
| admin.shares.downgrade_permission | Not provided in policy | backend endpoint | no |
| admin.shares.make_public | Not provided in policy | backend endpoint | yes |
| admin.shares.org_wide | Not provided in policy | backend endpoint | yes |
| admin.shares.read | Not provided in policy | backend endpoint | no |
| admin.shares.remove_expiry | Not provided in policy | backend endpoint | yes |
| admin.shares.revoke | Not provided in policy | backend endpoint | no |
| admin.shares.set_expiry | Not provided in policy | backend endpoint | no |
| admin.shares.set_no_expiry | Not provided in policy | backend endpoint | yes |
| admin.shares.upgrade_permission | Not provided in policy | backend endpoint | no |
| admin.users.delete | Not provided in policy | backend endpoint | yes |
| admin.users.disable_sharing | Not provided in policy | backend endpoint | no |
| admin.users.enable_sharing | Not provided in policy | backend endpoint | no |
| admin.users.read | Not provided in policy | frontend route / backend endpoint | no |
| admin.users.revoke_sessions | Not provided in policy | backend endpoint | no |
| admin.users.suspend | Not provided in policy | backend endpoint | yes |
| admin.users.unsuspend | Not provided in policy | backend endpoint | yes |
| ai.suggestions.approve | Not provided in policy | backend endpoint | no |
| ai.suggestions.read | Not provided in policy | frontend route / backend endpoint | no |
| ai.suggestions.reject | Not provided in policy | backend endpoint | no |
| analytics.read_aggregate | Not provided in policy | backend endpoint | no |
| approvals.approve | Not provided in policy | backend endpoint | yes |
| approvals.cancel | Not provided in policy | backend endpoint | no |
| approvals.execute | Not provided in policy | backend endpoint | yes |
| approvals.read | Not provided in policy | frontend route / backend endpoint | no |
| approvals.reject | Not provided in policy | backend endpoint | yes |
| approvals.request_create | Not provided in policy | backend endpoint | no |
| logs.audit.read | Not provided in policy | frontend route / backend endpoint | no |
| logs.export_full | Not provided in policy | backend endpoint | yes |
| logs.export_redacted | Not provided in policy | backend endpoint | yes |
| logs.system.read_full | Not provided in policy | unmapped | no |
| logs.system.read_redacted | Not provided in policy | backend endpoint | no |
| rbac.assignments.read | Not provided in policy | backend endpoint | no |
| rbac.assignments.update | Not provided in policy | backend endpoint | yes |
| rbac.roles.create | Not provided in policy | backend endpoint | yes |
| rbac.roles.delete | Not provided in policy | backend endpoint | yes |
| rbac.roles.read | Not provided in policy | frontend route / backend endpoint | no |
| rbac.roles.update | Not provided in policy | backend endpoint | yes |
| security.abuse.read | Not provided in policy | backend endpoint | no |
| security.emergency.disable_public_shares | Not provided in policy | backend endpoint | yes |
| security.emergency.disable_uploads | Not provided in policy | backend endpoint | yes |
| security.emergency.enable_public_shares | Not provided in policy | backend endpoint | yes |
| security.emergency.enable_uploads | Not provided in policy | backend endpoint | yes |
| security.emergency.readonly_disable | Not provided in policy | backend endpoint | yes |
| security.emergency.readonly_enable | Not provided in policy | backend endpoint | yes |
| security.files.quarantine | Not provided in policy | backend endpoint | no |
| security.files.unquarantine | Not provided in policy | backend endpoint | no |
| security.ip.block | Not provided in policy | backend endpoint | no |
| security.ip.unblock | Not provided in policy | backend endpoint | no |
| security.policies.read | Not provided in policy | backend endpoint | no |
| security.policies.update | Not provided in policy | backend endpoint | yes |
| system.backups.read | Not provided in policy | backend endpoint | no |
| system.backups.restore_test | Not provided in policy | backend endpoint | yes |
| system.deploy.read | Not provided in policy | backend endpoint | no |
| system.deploy.rollback | Not provided in policy | backend endpoint | yes |
| system.queues.pause | Not provided in policy | backend endpoint | yes |
| system.queues.read | Not provided in policy | backend endpoint | no |
| system.queues.resume | Not provided in policy | backend endpoint | yes |
| system.queues.set_concurrency | Not provided in policy | backend endpoint | yes |
| system.secrets.rotate | Not provided in policy | backend endpoint | yes |
| system.status.read | Not provided in policy | frontend route / backend endpoint | no |
| system.workers.restart | Not provided in policy | backend endpoint | yes |
| system.workers.scale | Not provided in policy | backend endpoint | yes |
