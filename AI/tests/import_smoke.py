from __future__ import annotations

import importlib
import json
import sys


MODULES = {
    "litellm": "litellm",
    "langchain": "langchain",
    "langgraph": "langgraph",
    "llama_index": "llama_index",
    "chromadb": "chromadb",
    "qdrant_client": "qdrant_client",
    "rank_bm25": "rank_bm25",
    "sentence_transformers": "sentence_transformers",
    "openai": "openai",
    "google.genai": "google.genai",
    "cloudevents": "cloudevents",
    "redis": "redis",
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
    "httpx": "httpx",
    "tenacity": "tenacity",
    "dotenv": "dotenv",
    "sqlalchemy": "sqlalchemy",
    "psycopg2": "psycopg2",
    "alembic": "alembic",
    "opentelemetry": "opentelemetry",
    "pytest": "pytest",
    "pydantic": "pydantic",
    "orjson": "orjson",
    "tiktoken": "tiktoken",
}


def main() -> int:
    loaded = {}
    try:
        pysqlite3 = importlib.import_module("pysqlite3")
        sys.modules["sqlite3"] = pysqlite3
        loaded["sqlite3"] = getattr(pysqlite3, "__file__", "built-in")
    except ModuleNotFoundError:
        pass
    for label, module_name in MODULES.items():
        module = importlib.import_module(module_name)
        loaded[label] = getattr(module, "__file__", "built-in")
    json.dump({"imports": loaded}, sys.stdout, indent=2, ensure_ascii=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
