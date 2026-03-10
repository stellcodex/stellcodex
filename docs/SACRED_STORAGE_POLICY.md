# Sacred Storage Policy

## Canonical Stores

### GitHub
- Source code
- Infra config
- Docker/build/deploy scripts
- Canonical documentation
- Architecture definitions

### Google Drive (`gdrive:stellcodex`)
- `STELL/00_ARCHIVE`
- `STELL/01_BACKUPS`
- `STELL/02_DATASETS`
- `STELL/03_EVIDENCE`
- `STELL/04_REPORTS`
- `STELL/05_MODEL_OUTPUTS`
- `STELL/06_COMPANY_DOCS`
- `STELL/07_EXPORTS`
- `STELL/08_STELL_AI_MEMORY`
- `STELL/09_STELLCODEX_ARTIFACTS`
- `STELL/10_ORCHESTRA_JOBS`

### Server
- Runtime containers
- Active databases
- Cache
- Transient logs

Server data is disposable by policy. If server state is lost, recovery must be possible from GitHub + Drive.
