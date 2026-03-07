from __future__ import annotations

import ipaddress
import json
import os
import time
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import redis
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

app = FastAPI()

STREAM_KEY = os.getenv("EVENT_STREAM", "stell:events:stream")
RPC_REQUESTS_KEY = os.getenv("RPC_REQUESTS_KEY", "stell:rpc:requests")
RPC_RESPONSE_PREFIX = os.getenv("RPC_RESPONSE_PREFIX", "stell:rpc:response:")
APPROVAL_STORE = os.getenv("APPROVAL_STORE", "/root/stell/genois/02_pending_approvals")
HANDOFF_DIR = Path(os.getenv("HANDOFF_DIR", "/root/workspace/handoff"))
LIVE_CONTEXT_JSON_PATH = Path(os.getenv("LIVE_CONTEXT_JSON_PATH", str(HANDOFF_DIR / "LIVE-CONTEXT.json")))
LIVE_CONTEXT_MD_PATH = Path(os.getenv("LIVE_CONTEXT_MD_PATH", str(HANDOFF_DIR / "LIVE-CONTEXT.md")))
JUDGE_DECISION_PATH = Path(os.getenv("JUDGE_DECISION_PATH", str(HANDOFF_DIR / "judge-last-decision.json")))


class InternalChatIn(BaseModel):
    message: str


def redis_client() -> redis.Redis:
    redis_url = (os.getenv("REDIS_URL") or "").strip()
    if redis_url:
        parsed = urlparse(redis_url)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or 6379
        db = int((parsed.path or "/0").lstrip("/") or "0")
        return redis.Redis(host=host, port=port, db=db, decode_responses=True)
    host = os.getenv("REDIS_HOST", "127.0.0.1")
    port = int(os.getenv("REDIS_PORT", "6379") or "6379")
    return redis.Redis(host=host, port=port, db=0, decode_responses=True)


def read_json_file(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def read_text_file(path: Path, limit: int = 12000) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")[:limit]
    except Exception:
        return ""


def is_internal_request(request: Request) -> bool:
    host = (request.client.host if request.client else "") or ""
    if not host:
        return False
    try:
        address = ipaddress.ip_address(host)
        return address.is_private or address.is_loopback
    except ValueError:
        return host == "localhost"


def rpc_chat(message: str, timeout: int = 60) -> dict[str, Any]:
    client = redis_client()
    request_id = str(uuid.uuid4())
    response_key = f"{RPC_RESPONSE_PREFIX}{request_id}"
    payload = {
        "request_id": request_id,
        "correlation_id": request_id,
        "sender": "internal-admin",
        "message": message,
        "requested_at": time.time(),
    }
    client.rpush(RPC_REQUESTS_KEY, json.dumps(payload, ensure_ascii=False))
    result = client.blpop(response_key, timeout=timeout)
    if not result:
        raise TimeoutError("RPC bridge yanit vermedi.")
    _, raw = result
    client.delete(response_key)
    return json.loads(raw)


@app.get("/stell/health")
def health() -> dict[str, str]:
    return {
        "status": "healthy",
        "brain": "active",
        "approval_store": APPROVAL_STORE,
        "event_stream": STREAM_KEY,
    }


@app.post("/stell/internal/chat")
def internal_chat(body: InternalChatIn, request: Request) -> dict[str, str]:
    if not is_internal_request(request):
        raise HTTPException(status_code=403, detail="Forbidden")
    message = body.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Bos mesaj")
    result = rpc_chat(message, timeout=90)
    return {"reply": str(result.get("reply", ""))}


@app.get("/stell/internal/context")
def internal_context(request: Request) -> dict[str, Any]:
    if not is_internal_request(request):
        raise HTTPException(status_code=403, detail="Forbidden")
    live_context = read_json_file(LIVE_CONTEXT_JSON_PATH) or {}
    judge_decision = read_json_file(JUDGE_DECISION_PATH)
    agent_status_path = Path(str(live_context.get("agent_status_path") or ""))
    session_path = Path(str(live_context.get("session_path") or ""))
    return {
        "status": "ok",
        "live_context": live_context,
        "judge_decision": judge_decision,
        "agent_status_markdown": read_text_file(agent_status_path) if agent_status_path else "",
        "session_markdown": read_text_file(session_path, limit=24000) if session_path else "",
        "live_context_markdown": read_text_file(LIVE_CONTEXT_MD_PATH),
        "paths": {
            "live_context_json": str(LIVE_CONTEXT_JSON_PATH),
            "live_context_markdown": str(LIVE_CONTEXT_MD_PATH),
            "judge_decision": str(JUDGE_DECISION_PATH),
        },
    }
