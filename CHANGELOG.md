# Changelog

## 2026-03-10

### Added
- Agent OS foundation modules for event bus, retrieval, task runtime, and tool registry.
- systemd automation for 7/24 orchestration, backup, git sync, and artifact cleanup.
- repository boundary layout for `stell-ai`, `stellcodex`, `infra`, `backend`, `frontend`, and `orchestra`.
- Phase 2, STELLAI, security, contract, and audit documentation bundles.

### Changed
- STELLAI runtime now performs self-evaluation and retry-aware re-evaluation.
- 7/24 orchestrator service now uses the orchestrator's native loop mode.
- backup flow now redacts environment content instead of copying sensitive values.

### Fixed
- runtime response contract and related tests were aligned.
- retry evaluation state handling was corrected.
- planner now avoids invalid file-scoped tool plans without `file_id`.

### Validation
- STELLAI runtime tests passed.
- allowed-tools authority tests passed.
- planner tests passed.
- shell and Python syntax checks passed.
- systemd units passed verification.
- boundary layout verification passed.

### Included Commits
- `fb5d37a` `docs(audit): add phase2 stellai and system audit reports`
- `964af06` `chore(boundary): add repo boundary layout and infrastructure docs`
- `14a438b` `feat(ops): add systemd automation and backup sync guard scripts`
- `4b0ede3` `feat(agent-os): add event bus, retrieval, task runtime and tool registry`
- `f23cf01` `fix(stellai): harden runtime evaluation and ops backup flow`
- `ab3153d` `fix(deploy): track backend alembic config`
- `e7488ec` `feat(ai): harden deploy automation and add isolated AI foundation`
