# Language Conventions

This repository contains product-facing text, internal implementation notes, and
test fixtures across backend, frontend, and infrastructure surfaces. To avoid
confusion, follow these rules for new engineering and STELL-AI work.

## Locked baseline

- Internal code comments: English
- Module docstrings: English
- Reference docs: English
- Migration notes: English
- Test names and structural assertions: English
- Frontend fallback messages and empty states: English unless the route is a
  dedicated localized content page
- Deployment notes and Dockerfile comments: English

## Allowed exceptions

- Dedicated localized legal or content pages may remain localized.
- Tool planners and message classifiers may match Turkish and English keywords.
- Compatibility checks may accept legacy Turkish transport messages while still
  returning English-first UI copy.
- Intentional exceptions must be listed in
  `docs/reference/language_audit_allowlist.md`.

## Update rule

When you add a new engineering module or artifact:

1. Add or update an English docstring or file-local note in the source file.
2. Update `docs/reference/engineering_pipeline_reference.md` if the artifact
   changes the pipeline surface.
3. Update `docs/reference/language_audit_allowlist.md` when a multilingual
   exception is intentional.
4. Keep public contract names stable even if UI copy is localized.
5. Run `python3 scripts/audit_language_consistency.py` and
   `python3 scripts/audit_repo_language_consistency.py` before closing the task.

## Why this exists

The platform supports multilingual product usage, but the implementation layer
must stay easy to maintain. English-first notes reduce ambiguity when the
runtime, tests, and deployment scripts evolve in parallel.
