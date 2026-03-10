# Language Conventions

This repository contains product-facing text, internal implementation notes, and
test fixtures. To avoid confusion, follow these rules for new engineering and
STELL-AI work.

## Locked baseline

- Internal code comments: English
- Module docstrings: English
- Reference docs: English
- Migration notes: English
- Test names and structural assertions: English

## Allowed exceptions

- User-facing copy may be localized when the product surface requires it.
- Tool planners and message classifiers may match Turkish and English keywords.
- Existing legacy localized files do not need bulk rewriting during unrelated
  work.

## Update rule

When you add a new engineering module or artifact:

1. Add or update an English docstring in the source file.
2. Update `docs/reference/engineering_pipeline_reference.md` if the artifact
   changes the pipeline surface.
3. Keep public contract names stable even if UI copy is localized.
4. Run `python3 scripts/audit_language_consistency.py` before closing the task.

## Why this exists

The platform supports multilingual product usage, but the implementation layer
must stay easy to maintain. English-first notes reduce ambiguity when the
runtime, tests, and deployment scripts evolve in parallel.
