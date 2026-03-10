import hashlib
import hmac
import json
import ipaddress
import logging
import os
import re
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

load_dotenv()
sys.path.insert(0, "/root/stell")
from stell_brain import handle_command
from identity_guard import send_to_user, parse_agent_report, identity_escalation_detected

app = FastAPI()
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID", "")
VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN", "Mazda3233")
OWNER_PHONE = os.getenv("STELL_OWNER_PHONE", "")
WHATSAPP_APP_SECRET = (os.getenv("WHATSAPP_APP_SECRET", "") or "").strip()
WHATSAPP_REPLAY_TTL_SECONDS = int((os.getenv("WHATSAPP_REPLAY_TTL_SECONDS", "604800") or "604800").strip())
WHATSAPP_REPLAY_PREFIX = "stell:webhook:processed:"

if not WHATSAPP_APP_SECRET:
    logging.getLogger(__name__).error(
        "SECURITY: WHATSAPP_APP_SECRET not set — incoming webhook requests will be rejected."
    )

BASE_DIR = Path("/root/stell/genois")
INGEST_DIR = BASE_DIR / "05_whatsapp_ingest"
LOG_DIR = BASE_DIR / "logs"
PENDING_APPROVAL_DIR = BASE_DIR / "02_pending_approvals"
APPROVED_DIR = BASE_DIR / "02_approved"
STREAM_KEY = "stell:events:stream"
WORKSPACE_HANDOFF_DIR = Path("/root/workspace/handoff")
LIVE_CONTEXT_JSON_PATH = WORKSPACE_HANDOFF_DIR / "LIVE-CONTEXT.json"
LIVE_CONTEXT_MD_PATH = WORKSPACE_HANDOFF_DIR / "LIVE-CONTEXT.md"
JUDGE_DECISION_PATH = WORKSPACE_HANDOFF_DIR / "judge-last-decision.json"

APPROVAL_WORDS = ("onay", "approve", "approved", "evet", "yes", "ok", "tamam")
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
TOKEN_PATTERN = re.compile(r"(OTONOM_APPROVE_[A-Z0-9_]+)")

for path in (INGEST_DIR, LOG_DIR, PENDING_APPROVAL_DIR, APPROVED_DIR):
    path.mkdir(parents=True, exist_ok=True)


class InternalChatIn(BaseModel):
    message: str


def verify_whatsapp_signature(raw_body: bytes, signature_header: str) -> Tuple[bool, str]:
    """Verify Meta X-Hub-Signature-256 header.

    Returns (True, "ok") when the signature is valid.
    Returns (False, reason) when the secret is missing or the signature is invalid.
    """
    if not WHATSAPP_APP_SECRET:
        append_log("WEBHOOK_SIGNATURE", "FAIL", "WHATSAPP_APP_SECRET missing")
        return False, "app_secret_missing"
    if not signature_header or not signature_header.startswith("sha256="):
        append_log("WEBHOOK_SIGNATURE", "FAIL", "missing or malformed X-Hub-Signature-256")
        return False, "signature_missing"
    expected = "sha256=" + hmac.new(
        WHATSAPP_APP_SECRET.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, signature_header):
        append_log("WEBHOOK_SIGNATURE", "FAIL", "signature mismatch")
        return False, "signature_mismatch"
    return True, "ok"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_iso() -> str:
    return utc_now().isoformat().replace("+00:00", "Z")


def compact_stamp() -> str:
    return utc_now().strftime("%Y%m%d_%H%M%S_%f")


def append_log(action: str, result: str, detail: str) -> None:
    logfile = LOG_DIR / f"{utc_now().strftime('%Y-%m-%d')}.log"
    with logfile.open("a", encoding="utf-8") as handle:
        handle.write(f"[{utc_now().strftime('%Y-%m-%d %H:%M')}] [{action}] [{result}] {detail}\n")


def redis_cli_base() -> List[str]:
    redis_cli = shutil.which("redis-cli")
    if redis_cli:
        return [redis_cli]
    return ["docker", "exec", "stellcodex-redis", "redis-cli"]


def run_redis_command(*args: str) -> Tuple[bool, str]:
    try:
        proc = subprocess.run(
            [*redis_cli_base(), *args],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return True, proc.stdout.strip()
    except Exception as exc:
        append_log("REDIS", "FAIL", f"args={' '.join(args)} err={exc}")
        log.warning("Redis command failed: %s", exc)
        return False, str(exc)


def reserve_message_id(message_id: str) -> Tuple[bool, str]:
    key = f"{WHATSAPP_REPLAY_PREFIX}{message_id}"
    ok, output = run_redis_command("SET", key, utc_iso(), "NX", "EX", str(WHATSAPP_REPLAY_TTL_SECONDS))
    if not ok:
        return False, "redis_unavailable"
    if output == "OK":
        return True, "stored"
    return False, "duplicate"


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
        return address.is_loopback or address.is_private
    except ValueError:
        return host in {"localhost"}


def send_whatsapp(to: str, text: str, media_url: Optional[str] = None, media_type: str = "text") -> bool:
    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}

    if media_url and media_type == "image":
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "image",
            "image": {"link": media_url, "caption": text},
        }
    elif media_url and media_type == "video":
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "video",
            "video": {"link": media_url, "caption": text},
        }
    else:
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text[:4096]},
        }

    try:
        response = httpx.post(url, headers=headers, json=payload, timeout=30.0)
        response.raise_for_status()
        append_log("SEND_WHATSAPP", "SUCCESS", f"to={to}")
        return True
    except Exception as exc:
        append_log("SEND_WHATSAPP", "FAIL", f"to={to} err={exc}")
        log.error("Send error: %s", exc)
        return False


def publish_event(
    event_type: str,
    sender: str,
    correlation_id: str,
    *,
    intent: str,
    text: str,
    risk_level: str = "low",
    destructive: bool = False,
    dsac_stage: str = "dry-run",
    approval_token: Optional[str] = None,
    approval_status: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> str:
    event = {
        "specversion": "1.0",
        "id": str(uuid.uuid4()),
        "source": "stell-gate",
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
            "approval_token": approval_token,
            "approval_status": approval_status,
            "text": text,
            "meta": extra or {},
        },
    }
    try:
        payload = json.dumps(event, ensure_ascii=False)
        redis_cli = shutil.which("redis-cli")
        if redis_cli:
            cmd = [redis_cli, "XADD", STREAM_KEY, "*", "payload", payload]
        else:
            cmd = ["docker", "exec", "stellcodex-redis", "redis-cli", "XADD", STREAM_KEY, "*", "payload", payload]
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=5)
        append_log("EVENT_SPINE", "SUCCESS", f"type={event_type} corr={correlation_id}")
    except Exception as exc:
        append_log("EVENT_SPINE", "FAIL", f"type={event_type} corr={correlation_id} err={exc}")
        log.warning("Event publish failed: %s", exc)
    return event["id"]


def persist_ingest(
    raw_data: Dict[str, Any],
    sender: Optional[str],
    text: Optional[str],
    correlation_id: str,
    message_id: Optional[str],
) -> Path:
    path = INGEST_DIR / f"{compact_stamp()}__event.json"
    payload = {
        "received_at": utc_iso(),
        "sender": sender,
        "text": text,
        "correlation_id": correlation_id,
        "message_id": message_id,
        "raw": raw_data,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def normalize_text(value: Optional[str]) -> str:
    return (value or "").strip()


def is_owner(sender: Optional[str]) -> bool:
    return bool(sender) and bool(OWNER_PHONE) and sender == OWNER_PHONE


def looks_destructive(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in DESTRUCTIVE_KEYWORDS)


def parse_approval_token(text: str) -> Optional[str]:
    match = TOKEN_PATTERN.search(text.upper())
    return match.group(1) if match else None


def is_approval_message(text: str, token: Optional[str]) -> bool:
    if not token:
        return False
    lowered = text.lower()
    return any(word in lowered for word in APPROVAL_WORDS)


def create_approval(sender: str, text: str, correlation_id: str) -> dict:
    token = "OTONOM_APPROVE_" + uuid.uuid4().hex[:12].upper()
    record = {
        "token": token,
        "status": "pending",
        "requested_at": utc_iso(),
        "sender": sender,
        "text": text,
        "correlation_id": correlation_id,
        "risk_level": "high",
        "destructive": True,
        "dsac_stage": "approval",
    }
    pending_path = PENDING_APPROVAL_DIR / f"{token}.json"
    pending_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    publish_event(
        "approval.requested",
        sender,
        correlation_id,
        intent="destruction",
        text=text,
        risk_level="high",
        destructive=True,
        dsac_stage="approval",
        approval_token=token,
        approval_status="pending",
        extra={"pending_path": str(pending_path)},
    )
    append_log("APPROVAL", "REQUESTED", f"sender={sender} token={token}")
    return record


def approve_pending(token: str, sender: str, text: str, correlation_id: str) -> Optional[Dict[str, Any]]:
    pending_path = PENDING_APPROVAL_DIR / f"{token}.json"
    if not pending_path.exists():
        return None

    record = json.loads(pending_path.read_text(encoding="utf-8"))
    record["status"] = "approved"
    record["approved_at"] = utc_iso()
    record["approved_by"] = sender
    record["approval_message"] = text

    approved_path = APPROVED_DIR / f"{token}.json"
    approved_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    pending_path.unlink(missing_ok=True)

    publish_event(
        "approval.granted",
        sender,
        correlation_id,
        intent="approval",
        text=text,
        risk_level=record.get("risk_level", "high"),
        destructive=record.get("destructive", True),
        dsac_stage="approval",
        approval_token=token,
        approval_status="approved",
        extra={"approved_path": str(approved_path), "requested_text": record.get("text")},
    )
    append_log("APPROVAL", "GRANTED", f"sender={sender} token={token}")
    return record


def render_reply(result: Any) -> str:
    if isinstance(result, dict):
        return str(result.get("body", ""))
    return str(result)


@app.get("/stell/webhook")
async def verify(request: Request):
    params = request.query_params
    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == VERIFY_TOKEN:
        return int(params.get("hub.challenge"))
    return "Invalid token"


@app.post("/stell/webhook")
async def webhook(request: Request):
    raw_body = await request.body()
    sig_header = request.headers.get("X-Hub-Signature-256", "")
    signature_ok, signature_reason = verify_whatsapp_signature(raw_body, sig_header)
    if not signature_ok:
        status_code = 503 if signature_reason == "app_secret_missing" else 403
        append_log(
            "WEBHOOK_SIGNATURE",
            "REJECTED",
            f"reason={signature_reason} host={request.client.host if request.client else '?'}",
        )
        log.warning("SECURITY: webhook request rejected | reason=%s", signature_reason)
        return JSONResponse({"status": "rejected", "reason": signature_reason}, status_code=status_code)
    try:
        data = json.loads(raw_body)
    except Exception:
        return JSONResponse({"status": "bad_request"}, status_code=400)
    correlation_id = str(uuid.uuid4())
    sender = None
    text = None
    ingest_path = None

    try:
        entry = data.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        message = value.get("messages", [{}])[0]

        if not message:
            append_log("WEBHOOK", "IGNORED", "message payload missing")
            return JSONResponse({"status": "ok"})

        message_id = normalize_text(message.get("id"))
        if not message_id:
            append_log("WEBHOOK_REPLAY", "FAIL", "message id missing")
            return JSONResponse({"status": "bad_request", "reason": "message_id_missing"}, status_code=400)

        reserved, replay_reason = reserve_message_id(message_id)
        if not reserved:
            append_log("WEBHOOK_REPLAY", "REJECTED", f"message_id={message_id} reason={replay_reason}")
            if replay_reason == "duplicate":
                return JSONResponse({"status": "duplicate", "message_id": message_id})
            return JSONResponse({"status": "unavailable", "reason": replay_reason}, status_code=503)

        sender = message.get("from")
        text = normalize_text(message.get("text", {}).get("body")) if message.get("type") == "text" else ""
        ingest_path = persist_ingest(data, sender, text, correlation_id, message_id)

        publish_event(
            "event.incoming",
            sender or "unknown",
            correlation_id,
            intent="query",
            text=text,
            dsac_stage="dry-run",
            extra={"ingest_path": str(ingest_path), "message_type": message.get("type"), "message_id": message_id},
        )

        if not is_owner(sender):
            publish_event(
                "incident.anomaly.detected",
                sender or "unknown",
                correlation_id,
                intent="query",
                text=text,
                risk_level="medium",
                dsac_stage="dry-run",
                extra={"reason": "unauthorized_sender", "ingest_path": str(ingest_path), "message_id": message_id},
            )
            append_log("AUTH", "DENY", f"sender={sender}")
            return JSONResponse({"status": "ok"})

        token = parse_approval_token(text)
        if is_approval_message(text, token):
            record = approve_pending(token, sender, text, correlation_id)
            if record is None:
                send_to_user(f"Gecersiz approval token: {token}", to=sender,
                             caller_id="stell_ai_core", send_fn=send_whatsapp)
            else:
                send_to_user(
                    f"Approval alindi.\nToken: {token}\nDurum: APPROVED\nKayit: {record.get('requested_at')}",
                    to=sender, caller_id="stell_ai_core", send_fn=send_whatsapp,
                )
                
                # Resuming modular AI session if correlation_id is a session ID
                corr_id = record.get("correlation_id")
                if corr_id and len(corr_id) == 36: # Simple UUID check
                    from runtime_staging.stell_ai_core import StellAI
                    ai = StellAI(owner_phone=sender)
                    try:
                        # Attempt to resume the session
                        res_report = ai.resume_session(uuid.UUID(corr_id))
                        # Note: res_report already sent via send_whatsapp in resume_session
                    except Exception as e:
                        log.error(f"Failed to resume session {corr_id}: {e}")
            return JSONResponse({"status": "ok"})

        if looks_destructive(text):
            publish_event(
                "event.intent.classified",
                sender,
                correlation_id,
                intent="destruction",
                text=text,
                risk_level="high",
                destructive=True,
                dsac_stage="approval",
                extra={"ingest_path": str(ingest_path), "message_id": message_id},
            )
            record = create_approval(sender, text, correlation_id)
            send_to_user(
                (
                    "Bu islem D-SAC onayi gerektiriyor.\n"
                    f"Token: {record['token']}\n"
                    "Onaylamak icin su sekilde yanit verin:\n"
                    f"ONAY {record['token']}"
                ),
                to=sender, caller_id="stell_ai_core", send_fn=send_whatsapp,
            )
            return JSONResponse({"status": "ok"})

        publish_event(
            "event.intent.classified",
            sender,
            correlation_id,
            intent="query",
            text=text,
            risk_level="low",
            dsac_stage="dry-run",
            extra={"ingest_path": str(ingest_path), "message_id": message_id},
        )

        result = handle_command(text, sender)
        if isinstance(result, dict):
            send_to_user(result.get("body", ""), to=sender, caller_id="stell_ai_core",
                         send_fn=send_whatsapp, media_url=result.get("url"),
                         media_type=result.get("type", "text"))
        else:
            send_to_user(str(result), to=sender, caller_id="stell_ai_core",
                         send_fn=send_whatsapp)
        append_log("WEBHOOK", "SUCCESS", f"sender={sender} corr={correlation_id}")
    except Exception as exc:
        append_log("WEBHOOK", "FAIL", f"sender={sender} corr={correlation_id} err={exc}")
        log.error("Webhook error: %s", exc)
        if sender:
            send_to_user("Istek islenirken bir hata olustu.", to=sender,
                         caller_id="stell_ai_core", send_fn=send_whatsapp)

    return JSONResponse({"status": "ok"})


@app.post("/stell/internal/chat")
async def internal_chat(body: InternalChatIn):
    correlation_id = str(uuid.uuid4())
    text = normalize_text(body.message)
    sender = "internal-admin"

    if not text:
        return JSONResponse({"reply": "Bos mesaj alindi."}, status_code=400)

    publish_event(
        "event.incoming",
        sender,
        correlation_id,
        intent="query",
        text=text,
        dsac_stage="dry-run",
        extra={"channel": "admin"},
    )

    if looks_destructive(text):
        publish_event(
            "event.intent.classified",
            sender,
            correlation_id,
            intent="destruction",
            text=text,
            risk_level="high",
            destructive=True,
            dsac_stage="approval",
            extra={"channel": "admin"},
        )
        append_log("INTERNAL_CHAT", "BLOCKED", f"corr={correlation_id} destructive_request")
        return {"reply": "Bu islem D-SAC onayi gerektirir. Owner WhatsApp kanalindan approval token alin."}

    publish_event(
        "event.intent.classified",
        sender,
        correlation_id,
        intent="query",
        text=text,
        risk_level="low",
        dsac_stage="dry-run",
        extra={"channel": "admin"},
    )

    try:
        result = handle_command(text, sender)
        reply = render_reply(result)
        append_log("INTERNAL_CHAT", "SUCCESS", f"corr={correlation_id}")
        return {"reply": reply}
    except Exception as exc:
        append_log("INTERNAL_CHAT", "FAIL", f"corr={correlation_id} err={exc}")
        log.error("Internal chat error: %s", exc)
        return JSONResponse({"reply": "Istek islenirken bir hata olustu."}, status_code=500)


@app.get("/stell/internal/context")
async def internal_context(request: Request):
    if not is_internal_request(request):
        append_log("INTERNAL_CONTEXT", "BLOCKED", f"host={request.client.host if request.client else '?'}")
        return JSONResponse({"detail": "Forbidden"}, status_code=403)

    live_context = read_json_file(LIVE_CONTEXT_JSON_PATH) or {}
    console_view = read_json_file(Path("/root/workspace/handoff/console-view.json")) or {}
    status_path = Path(live_context.get("agent_status_path", "")) if live_context.get("agent_status_path") else None
    session_path = Path(live_context.get("session_path", "")) if live_context.get("session_path") else None
    append_log("INTERNAL_CONTEXT", "SUCCESS", f"host={request.client.host if request.client else '?'}")
    return {
        "status": "ok",
        "live_context": live_context,
        "console_view": console_view,
        "judge_decision": read_json_file(JUDGE_DECISION_PATH),
        "agent_status_markdown": read_text_file(status_path) if status_path else "",
        "session_markdown": read_text_file(session_path) if session_path else "",
        "live_context_markdown": read_text_file(LIVE_CONTEXT_MD_PATH),
        "paths": {
            "live_context_json": str(LIVE_CONTEXT_JSON_PATH),
            "live_context_markdown": str(LIVE_CONTEXT_MD_PATH),
            "judge_decision": str(JUDGE_DECISION_PATH),
        },
    }


@app.get("/stell/health")
async def health():
    return {
        "status": "healthy",
        "brain": "active",
        "approval_store": str(PENDING_APPROVAL_DIR),
        "event_stream": STREAM_KEY,
        "signature_verification": "strict" if WHATSAPP_APP_SECRET else "misconfigured",
        "replay_store_prefix": WHATSAPP_REPLAY_PREFIX,
        "replay_ttl_seconds": WHATSAPP_REPLAY_TTL_SECONDS,
    }
