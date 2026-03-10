from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

import pysqlite3

sys.modules["sqlite3"] = pysqlite3

import chromadb
from sentence_transformers import SentenceTransformer


VECTOR_ROOT = Path(os.environ.get("STELL_AI_VECTOR_STORE", "/root/workspace/_vector_store"))
CHROMA_DIR = VECTOR_ROOT / "chroma_smoke"
MODEL_CACHE_DIR = Path(os.environ.get("HF_HOME", "/root/workspace/_models"))
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def main() -> int:
    if CHROMA_DIR.exists():
        shutil.rmtree(CHROMA_DIR)
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_or_create_collection(name="stellcodex-smoke")
    model = SentenceTransformer(MODEL_NAME, cache_folder=str(MODEL_CACHE_DIR))
    documents = [
        "Deterministic rule engine enforces manufacturing approvals.",
        "Share links expire with HTTP 410 and revoke immediately.",
        "Assembly meta is mandatory before a file becomes ready.",
    ]
    embeddings = model.encode(documents, show_progress_bar=False).tolist()
    collection.add(
        ids=["doc-1", "doc-2", "doc-3"],
        documents=documents,
        embeddings=embeddings,
        metadatas=[
            {"topic": "orchestrator"},
            {"topic": "share"},
            {"topic": "viewer"},
        ],
    )
    query_embedding = model.encode(["Which contract requires HTTP 410?"], show_progress_bar=False).tolist()
    result = collection.query(query_embeddings=query_embedding, n_results=2)
    ids = result.get("ids", [[]])[0]
    assert ids
    payload = {
        "persist_dir": str(CHROMA_DIR),
        "top_ids": ids,
        "vector_store_root": str(VECTOR_ROOT),
        "model_cache_dir": str(MODEL_CACHE_DIR),
    }
    print(json.dumps(payload, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
