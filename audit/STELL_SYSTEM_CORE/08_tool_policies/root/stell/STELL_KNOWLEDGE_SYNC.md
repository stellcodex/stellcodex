# Stell Knowledge Sync

## Source of Truth

- GitHub manages text-first knowledge:
  - `knowledge/`
  - `playbooks/`
  - `policies/`
  - `prompts/`
  - `actions/`
- Google Drive manages heavy and operational files:
  - PDF
  - DOCX
  - XLSX
  - images
  - raw customer packages

## Runtime Model

Stell should not read GitHub or Drive directly during every user request.

Instead:
1. sync sources
2. normalize content
3. write manifests and checksums
4. index approved content locally
5. answer from the local index

## Google Drive Layout

Suggested root: `gdrive:stellcodex-genois`

- `01_inbox/`
- `02_approved/github-seed/`
- `03_archive/`
- `04_exports/`
- `05_whatsapp_ingest/`
- `06_reports/`

## Safety Rules

- no secrets in GitHub knowledge folders
- no large binaries in GitHub knowledge folders
- no direct execution from unapproved Drive inbox files
- keep action logs separate from source knowledge
