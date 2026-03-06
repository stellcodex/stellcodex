# RAG Runtime Constraints (Python 3.8)

## Baseline
- Runtime: `/root/workspace/AI/.venv/bin/python`
- Python: 3.8.x

## Constraint
- `langgraph` modern releases are not available for Python 3.8.
- `chromadb` requires sqlite >= 3.35 at runtime.

## Enforced Compatibility
1. Install `langgraph==0.0.8` with `--no-deps`.
2. Keep langchain family pinned:
   - `langchain==0.2.17`
   - `langchain-core==0.2.43`
   - `langchain-community==0.2.19`
   - `langchain-text-splitters==0.2.4`
3. Install `pysqlite3-binary`.
4. Write `zz_sqlite_patch.pth` into venv `site-packages`:
   - `import sys,pysqlite3;sys.modules["sqlite3"]=pysqlite3`

## Bootstrap
- Use: `/root/workspace/_systems/STELL_CORE/10_rag/bootstrap_rag_runtime.sh`
