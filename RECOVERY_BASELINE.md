# RECOVERY BASELINE — STELLCODEX V10
Generated: 2026-03-29

---

## CURRENT PHASE

```
current_phase: SELF_LEARNING_ACTIVE
```

---

## ACTIVE SERVICES & PORTS

| Service | Port | Health Endpoint |
|---------|------|-----------------|
| Backend API (FastAPI) | 8000 | `GET /api/v1/health` → `{"status":"ok"}` |
| STELL-AI Service | 8000 | `GET /api/v1/stell/health` → `{"status":"ok","service":"stell"}` |
| Frontend (Next.js) | 3000 | `GET /` |

---

## GIT STATE

```
latest_commit: e01b0389d75bdb90896437788d99b790907fb1dc
branch: main
remote: origin/main
```

> Fill after snapshot:
```
snapshot_hash: [SEE SNAPSHOT_HASH.txt]
```

---

## DRIVE BACKUP PATH

```
gdrive:STELLCODEX_BACKUPS/
```

Verify with:
```bash
rclone ls gdrive:STELLCODEX_BACKUPS/
```

---

## RESTORE PROCEDURE

### Full restore from snapshot:

```bash
# 1. Clone repo (if server is fresh)
git clone <repo_url> /root/workspace
cd /root/workspace

# 2. Restore snapshot from Drive
rclone copy gdrive:STELLCODEX_BACKUPS/stellcodex_v10_snapshot_<TIMESTAMP>.tar.gz .

# 3. Verify hash
sha256sum -c SNAPSHOT_HASH.txt

# 4. Extract (excluding git to keep fresh clone)
tar -xzf stellcodex_v10_snapshot_<TIMESTAMP>.tar.gz \
  --exclude='.git' \
  --exclude='node_modules' \
  --exclude='.next'

# 5. Install dependencies
cd backend && pip install -r requirements.txt
cd ../frontend && npm install

# 6. Start services
docker compose -f infrastructure/deploy/docker-compose.yml up -d

# 7. Verify
curl http://127.0.0.1:8000/api/v1/health
./ops/preflight_context_guard.sh
```

---

## FORBIDDEN REGRESSIONS

```
NEVER restore to a state where:
  - current_phase is NOT SELF_LEARNING_ACTIVE
  - completed_phases_locked is false
  - forbidden_reopen list is empty
  - GitHub is not the code authority
```

---

## ANTI-PATTERNS (NEVER DO)

- Do not use a server backup as restore source (use Drive + GitHub only)
- Do not restore and then modify without re-running preflight
- Do not skip hash verification
