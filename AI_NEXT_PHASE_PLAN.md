# AI Next Phase Plan

1. Add retrieval-backed orchestration adapters that read from `/root/workspace/_vector_store` instead of the legacy knowledge path.
2. Introduce CPU-only PyTorch sourcing or an internal wheel mirror to cut the AI environment footprint.
3. Add CI smoke for `/root/workspace/AI/scripts/run_import_smoke.sh` and `/root/workspace/AI/scripts/run_retrieval_smoke.sh`.
4. Bind MemoryRecord ingestion into `AI/stell_ai` workflows and persist normalized records to Drive-backed evidence archives.
