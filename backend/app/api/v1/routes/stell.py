"""
Stell Chat API — Admin Panel Endpoint
POST /api/v1/stell/chat  (admin JWT zorunlu)
İç ağda stell-webhook (port 4500) ile konuşur.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from urllib.parse import urlparse
import urllib.request
import urllib.error
from typing import Any, Dict, Optional

import redis
from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from pydantic import BaseModel

from app.security.deps import require_role, Principal

router = APIRouter(prefix="/stell", tags=["stell"])

DEFAULT_WEBHOOK_PORT = int(os.getenv("STELL_WEBHOOK_PORT", "4500") or "4500")
HTTP_BRIDGE_TIMEOUT = int(os.getenv("STELL_HTTP_BRIDGE_TIMEOUT", "3") or "3")
INTERNAL_BRIDGE_HOST = (os.getenv("STELL_WEBHOOK_BRIDGE_HOST") or "").strip()
CHAT_TRANSPORT = (os.getenv("STELL_INTERNAL_CHAT_TRANSPORT", "http_first") or "http_first").strip().lower()
STREAM_KEY = "stell:events:stream"
CHECKPOINT_EVENT_TYPE = "system.context.checkpointed"
RPC_REQUESTS_KEY = "stell:rpc:requests"
RPC_RESPONSE_PREFIX = "stell:rpc:response:"


class ChatIn(BaseModel):
    message: str


class ChatOut(BaseModel):
    reply: str


def default_gateway_host() -> Optional[str]:
    route_path = "/proc/net/route"
    try:
        with open(route_path, "r", encoding="utf-8") as handle:
            next(handle, None)
            for raw_line in handle:
                columns = raw_line.strip().split()
                if len(columns) < 3 or columns[1] != "00000000":
                    continue
                gateway_hex = columns[2]
                octets = [str(int(gateway_hex[index:index + 2], 16)) for index in range(0, 8, 2)]
                octets.reverse()
                return ".".join(octets)
    except Exception:
        return None
    return None


def webhook_base_urls() -> list[str]:
    candidates: list[str] = []
    explicit = (os.getenv("STELL_WEBHOOK_BASE_URL") or "").strip()
    if explicit:
        candidates.append(explicit.rstrip("/"))
    if INTERNAL_BRIDGE_HOST:
        candidates.append(f"http://{INTERNAL_BRIDGE_HOST}:{DEFAULT_WEBHOOK_PORT}")
    gateway = default_gateway_host()
    if gateway:
        candidates.append(f"http://{gateway}:{DEFAULT_WEBHOOK_PORT}")
    candidates.append(f"http://172.17.0.1:{DEFAULT_WEBHOOK_PORT}")
    deduped: list[str] = []
    for item in candidates:
        if item not in deduped:
            deduped.append(item)
    return deduped


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


def latest_checkpoint_snapshot() -> Dict[str, Any]:
    client = redis_client()
    entries = client.xrevrange(STREAM_KEY, count=100)
    for _msg_id, fields in entries:
        raw = fields.get("payload")
        if not raw:
            continue
        event = json.loads(raw)
        if event.get("type") != CHECKPOINT_EVENT_TYPE:
            continue
        data = event.get("data", {})
        return {
            "status": "ok",
            "checkpoint_event": event,
            "live_context": data.get("live_context", {}),
            "paths": {
                "live_context_json": data.get("live_context_json"),
                "live_context_markdown": data.get("live_context_markdown"),
            },
        }
    raise LookupError("Checkpoint event bulunamadi.")


def rpc_chat(message: str, timeout: int = 30) -> Dict[str, Any]:
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


def fetch_json(path: str, payload: Optional[bytes] = None, method: str = "GET", timeout: int = 20) -> Dict[str, Any]:
    last_error: Optional[Exception] = None
    for base_url in webhook_base_urls():
        url = f"{base_url}{path}"
        try:
            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method=method,
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read())
        except Exception as exc:
            last_error = exc
            continue
    if last_error is not None:
        raise last_error
    raise RuntimeError("No webhook base URL candidates available")


def chat_transport_sequence() -> list[str]:
    if CHAT_TRANSPORT == "rpc_only":
        return ["rpc"]
    if CHAT_TRANSPORT == "rpc_first":
        return ["rpc", "http"]
    if CHAT_TRANSPORT == "http_only":
        return ["http"]
    return ["http", "rpc"]


@router.post("/chat", response_model=ChatOut)
def stell_chat(
    body: ChatIn,
    principal: Principal = Depends(require_role("admin")),
):
    """Admin panelden Stell'e mesaj gönder."""
    message = body.message.strip()
    payload = json.dumps({"message": message}).encode()
    failures: list[str] = []
    for transport in chat_transport_sequence():
        if transport == "rpc":
            try:
                rpc_result = rpc_chat(message, timeout=40)
                return ChatOut(reply=str(rpc_result.get("reply", "")))
            except TimeoutError as exc:
                failures.append(f"rpc timeout: {exc}")
            except redis.RedisError as exc:
                failures.append(f"rpc redis: {exc}")
            except Exception as exc:
                failures.append(f"rpc error: {exc}")
            continue
        try:
            data = fetch_json("/stell/internal/chat", payload=payload, method="POST", timeout=HTTP_BRIDGE_TIMEOUT)
            return ChatOut(reply=data["reply"])
        except urllib.error.URLError as exc:
            failures.append(f"http bridge: {exc}")
        except Exception as exc:
            failures.append(f"http error: {exc}")
    detail = "; ".join(failures) if failures else "bilinmeyen transport hatasi"
    raise HTTPException(status_code=503, detail=f"Stell servisi yanit vermiyor: {detail}")


@router.get("/context")
def stell_context(
    principal: Principal = Depends(require_role("admin")),
):
    """Admin panel için ortak canlı context snapshotını döndür."""
    try:
        return latest_checkpoint_snapshot()
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except redis.RedisError as e:
        raise HTTPException(status_code=503, detail=f"Checkpoint stream erişilemiyor: {e}")
    except urllib.error.URLError as e:
        raise HTTPException(status_code=503, detail=f"Stell context servisi yanıt vermiyor: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hata: {e}")
