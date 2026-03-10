# AI Environment Operations

## Create
1. Run `/root/workspace/AI/scripts/create_venv.sh`.
2. Run `/root/workspace/AI/scripts/install_requirements.sh`.
3. Run `/root/workspace/AI/scripts/run_import_smoke.sh`.
4. Run `/root/workspace/AI/scripts/run_retrieval_smoke.sh`.

## Upgrade
1. Update `/root/workspace/AI/requirements.in`.
2. Re-run `/root/workspace/AI/scripts/install_requirements.sh`.
3. Re-run both smoke scripts and inspect `/root/workspace/AI/logs`.

## Rollback
1. Review `/root/workspace/PRE_AI_INSTALL_RUNTIME_STATE.json`.
2. Review `/root/workspace/PRE_AI_INSTALL_DISK_STATE.txt`.
3. Stop using `/root/workspace/AI/.venv` and restore from `/root/workspace/AI/.venv.py38.bak_20260310T0930` if needed.

## Paths
- cache_path: /root/workspace/_models
- vector_path: /root/workspace/_vector_store
- log_path: /root/workspace/AI/logs
- venv_path: /root/workspace/AI/.venv

## Offload Policy
- Remains on server: `/root/workspace/AI/.venv`, `/root/workspace/_models`, `/root/workspace/_vector_store`, `/root/workspace/AI/logs`.
- Must be offloaded after verification when large: backup dumps, storage mirrors, evidence bundles, exported artifacts, transient datasets.
