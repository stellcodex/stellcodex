# V7 Enforcement Protocol

1) Only V7_MASTER is binding.
2) Hot patching is forbidden: Repo → Commit → Build → Recreate → Proof only.
3) Any violation of:
   - storage_key leak
   - file_id contract
   - decision_json NULL
   - missing rule_configs usage
   - missing assembly_meta
   - share expire != 410
   - bypass approvals
   blocks release.
4) PASS must be backed by evidence artifacts.
