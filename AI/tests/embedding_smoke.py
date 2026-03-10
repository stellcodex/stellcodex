from __future__ import annotations

import json
import os
from pathlib import Path

from sentence_transformers import SentenceTransformer


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
MODELS_DIR = Path(os.environ.get("HF_HOME", "/root/workspace/_models"))


def main() -> int:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    model = SentenceTransformer(MODEL_NAME, cache_folder=str(MODELS_DIR))
    embeddings = model.encode(["stellcodex deterministic rule engine", "share contract 410"], show_progress_bar=False)
    payload = {
        "model_name": MODEL_NAME,
        "embedding_count": int(len(embeddings)),
        "embedding_dim": int(len(embeddings[0])),
        "cache_dir": str(MODELS_DIR),
        "cache_exists": MODELS_DIR.exists(),
    }
    assert payload["embedding_count"] == 2
    assert payload["embedding_dim"] > 0
    print(json.dumps(payload, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
