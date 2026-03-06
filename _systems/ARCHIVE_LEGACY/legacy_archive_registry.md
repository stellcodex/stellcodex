# Legacy Archive Registry

Generated: 2026-03-06T23:19:39Z

This registry tracks legacy/duplicate candidates without destructive deletion.

## Candidate Sources
- /root/workspace/_archive
- /root/workspace/handoff/backups
- *.bak / *.save / *.old patterns under /root/workspace

## Policy
- Never delete automatically.
- Move only after explicit compatibility verification.

## Archived Items
- 2026-03-06T23:34:00Z
  - from: /root/workspace/_knowledge/manuals/STELLCODEX_MASTER_PROMPT_v8.0.md
  - to: /root/workspace/_systems/ARCHIVE_LEGACY/prompts/STELLCODEX_MASTER_PROMPT_v8.0.from_knowledge_manuals.md
  - reason: duplicate prompt filename guardrail (`STELLCODEX_MASTER_PROMPT_v8.0.md`) with canonical `_truth` copy
