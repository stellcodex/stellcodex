from __future__ import annotations

import json

from rank_bm25 import BM25Okapi


def tokenize(text: str) -> list[str]:
    return text.lower().split()


def main() -> int:
    corpus = [
        "deterministic dfm approval rules",
        "share token expiry returns 410",
        "assembly meta is required for ready status",
    ]
    tokenized = [tokenize(item) for item in corpus]
    engine = BM25Okapi(tokenized)
    scores = engine.get_scores(tokenize("which response returns 410"))
    best_index = max(range(len(scores)), key=lambda idx: float(scores[idx]))
    payload = {
        "best_document": corpus[best_index],
        "best_score": float(scores[best_index]),
    }
    assert "410" in payload["best_document"]
    print(json.dumps(payload, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
