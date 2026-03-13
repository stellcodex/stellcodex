#!/usr/bin/env python3
from __future__ import annotations

import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import redis
from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parents[1] / "stellcodex_v7" / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

load_dotenv("/root/stell/webhook/.env")
load_dotenv("/var/www/stellcodex/backend/.env")

from app.core.identity.stell_identity import GENERAL_FAILURE_TEXT, RUNTIME_UNAVAILABLE_TEXT
from app.stellai.channel_runtime import execute_channel_runtime
from app.stellai.service import get_stellai_runtime
from app.stellai.tools import GLOBAL_ALLOWLIST
from app.stellai.types import RuntimeContext, RuntimeRequest

LOG_DIR = Path(os.getenv("STELLCODEX_RPC_LOG_DIR", "/var/log/stellcodex"))
STREAM_KEY = "stell:events:stream"
RPC_REQUESTS_KEY = "stell:rpc:requests"
RPC_RESPONSE_PREFIX = "stell:rpc:response:"
DESTRUCTIVE_KEYWORDS = (
    "deploy",
    "restart",
    "rebuild",
    "sil",
    "delete",
    "truncate",
    "drop",
    "purge",
    "reset",
    "migrate",
    "rollback",
    "reload",
)

LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=str(LOG_DIR / "stell-rpc-bridge.log"),
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger("stell-rpc-bridge")


def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


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


def normalize_text(value: Optional[str]) -> str:
    return (value or "").strip()


def looks_destructive(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in DESTRUCTIVE_KEYWORDS)


def render_reply(result: Any) -> str:
    if isinstance(result, dict):
        return str(result.get("body", ""))
    return str(result)


def run_stell_runtime_message(message: str, sender: str) -> str:
    try:
        context = RuntimeContext(
            tenant_id="0",
            project_id="admin-rpc",
            principal_type="internal",
            principal_id=str(sender or "internal-admin"),
            session_id=f"rpc_{uuid.uuid4().hex[:16]}",
            trace_id=str(uuid.uuid4()),
            allowed_tools=GLOBAL_ALLOWLIST,
        )
        request = RuntimeRequest(message=message, context=context, top_k=4)
        outcome = execute_channel_runtime(
            request=request,
            db=None,
            runtime=get_stellai_runtime(),
            channel="admin",
        )
        return str(outcome.reply or RUNTIME_UNAVAILABLE_TEXT)
    except Exception:
        log.exception("STELL runtime invocation failed")
        return RUNTIME_UNAVAILABLE_TEXT


def publish_event(
    client: redis.Redis,
    event_type: str,
    sender: str,
    correlation_id: str,
    *,
    intent: str,
    text: str,
    risk_level: str = "low",
    destructive: bool = False,
    dsac_stage: str = "dry-run",
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    event = {
        "specversion": "1.0",
        "id": str(uuid.uuid4()),
        "source": "stell-rpc-bridge",
        "type": event_type,
        "time": utc_iso(),
        "subject": f"whatsapp:{sender}",
        "datacontenttype": "application/json",
        "correlation_id": correlation_id,
        "data": {
            "intent": intent,
            "risk_level": risk_level,
            "destructive": destructive,
            "dsac_stage": dsac_stage,
            "approval_token": None,
            "approval_status": None,
            "text": text,
            "meta": extra or {},
        },
    }
    client.xadd(STREAM_KEY, {"payload": json.dumps(event, ensure_ascii=False)})


def write_response(client: redis.Redis, request_id: str, payload: Dict[str, Any]) -> None:
    response_key = f"{RPC_RESPONSE_PREFIX}{request_id}"
    client.rpush(response_key, json.dumps(payload, ensure_ascii=False))
    client.expire(response_key, 120)


def process_request(client: redis.Redis, raw: str) -> None:
    request = json.loads(raw)
    request_id = str(request["request_id"])
    message = normalize_text(str(request.get("message", "")))
    sender = str(request.get("sender") or "internal-admin")
    correlation_id = str(request.get("correlation_id") or request_id)

    if not message:
        write_response(client, request_id, {"ok": False, "reply": GENERAL_FAILURE_TEXT})
        return

    publish_event(
        client,
        "event.incoming",
        sender,
        correlation_id,
        intent="query",
        text=message,
        extra={"channel": "admin-rpc"},
    )

    if looks_destructive(message):
        publish_event(
            client,
            "event.intent.classified",
            sender,
            correlation_id,
            intent="destruction",
            text=message,
            risk_level="high",
            destructive=True,
            dsac_stage="approval",
            extra={"channel": "admin-rpc"},
        )
        write_response(
            client,
            request_id,
            {
                "ok": True,
                "reply": (
                    "STELL-AI bu islemin D-SAC onayi gerektirdigini dogruladi. "
                    "Owner WhatsApp kanalindan approval token alin."
                ),
            },
        )
        return

    publish_event(
        client,
        "event.intent.classified",
        sender,
        correlation_id,
        intent="query",
        text=message,
        risk_level="low",
        destructive=False,
        dsac_stage="dry-run",
        extra={"channel": "admin-rpc"},
    )

    try:
        reply = run_stell_runtime_message(message, sender)
        write_response(client, request_id, {"ok": True, "reply": reply})
    except Exception:
        log.exception("RPC request failed")
        write_response(client, request_id, {"ok": False, "reply": RUNTIME_UNAVAILABLE_TEXT})


def main() -> int:
    client = redis_client()
    log.info("RPC bridge started | queue=%s", RPC_REQUESTS_KEY)
    while True:
        try:
            item = client.blpop(RPC_REQUESTS_KEY, timeout=5)
            if not item:
                continue
            _, raw = item
            process_request(client, raw)
        except redis.RedisError:
            log.exception("Redis error in RPC bridge loop")
            time.sleep(2)
        except Exception:
            log.exception("Unexpected error in RPC bridge loop")
            time.sleep(1)


if __name__ == "__main__":
    raise SystemExit(main())
