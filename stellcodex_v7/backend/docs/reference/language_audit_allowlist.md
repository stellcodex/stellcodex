# Language Audit Allowlist

This file records the small set of repository files that may intentionally
contain Turkish text or Turkish keyword matching.

## Allowed multilingual files

- `backend/app/core/runtime/message_mode.py`
  Reason: multilingual message classification keywords.
- `backend/app/stellai/agents.py`
  Reason: multilingual tool inference keywords.
- `backend/app/stellai/channel_runtime.py`
  Reason: multilingual async routing keywords.
- `frontend/components/ChatShell.tsx`
  Reason: bilingual quick-start intent matching.
- `frontend/components/viewer/DxfViewer.tsx`
  Reason: legacy Turkish pending-state compatibility detection.
- `frontend/app/(viewer)/view/[scx_id]/page.tsx`
  Reason: legacy Turkish transport error compatibility detection.
- `frontend/lib/workspace-store.ts`
  Reason: legacy default project identifier compatibility mapping.
- `frontend/content/privacy.tr.md`
  Reason: dedicated Turkish privacy content.
- `frontend/content/terms.tr.md`
  Reason: dedicated Turkish terms content.

## Update rule

Only add a file here when:

1. The multilingual content is deliberate.
2. Removing it would break compatibility or remove a supported localized page.
3. The reason is specific enough that a later cleanup can revisit it.
