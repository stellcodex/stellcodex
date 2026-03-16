## Archive Note

- Reason retired: This enforcement protocol has been subsumed into the V10 release, security, and evidence rules.
- Replaced by: `docs/v10/07_V10_SECURITY_LIMITS_AND_COMPLIANCE.md` and `docs/v10/11_V10_RELEASE_GATES_AND_SMOKE.md`
- Historical value: Yes. It records the old V7 release-blocking rule set.

# V7 Enforcement Protocol

1) V10 is the sole binding top-level constitution.
2) V7_MASTER remains enforceable only as a subordinate constitution under the V10 truth hierarchy.
3) Hot patching is forbidden: Repo -> Commit -> Build -> Recreate -> Proof only.
4) Any violation of:
   - storage_key leak
   - file_id contract
   - decision_json NULL
   - missing rule_configs usage
   - missing assembly_meta
   - share expire != 410
   - bypass approvals
   blocks release.
5) PASS must be backed by evidence artifacts.
