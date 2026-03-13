from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import json
import os
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.identity.stell_identity import GENERAL_FAILURE_TEXT, RUNTIME_UNAVAILABLE_TEXT
from app.core.ids import format_scx_file_id, normalize_scx_file_id
from app.db.session import get_db
from app.models.file import UploadFile
from app.services.tenant_identity import resolve_or_create_tenant_id
from app.stellai.channel_runtime import execute_channel_runtime
from app.stellai.service import get_stellai_runtime
from app.stellai.tools import GLOBAL_ALLOWLIST
from app.stellai.types import RuntimeContext, RuntimeRequest

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])


class WhatsAppWebhookOut(BaseModel):
    status: str
    reply: str
    mode: str | None = None
    job_id: str | None = None


@dataclass(frozen=True)
class NormalizedWhatsAppMessage:
    sender: str
    message: str
    file_ids: tuple[str, ...]
    trace_id: str | None = None


def _normalize_file_id(value: str) -> str:
    return format_scx_file_id(normalize_scx_file_id(value))


def _normalize_sender(value: str) -> str:
    raw = str(value or "").strip()
    return "".join(ch for ch in raw if ch.isdigit() or ch == "+") or "unknown"


def _whatsapp_owner_sub(sender: str) -> str:
    return f"whatsapp:{_normalize_sender(sender)}"


def _extract_text(message: dict[str, Any]) -> str:
    text = message.get("text")
    if isinstance(text, dict):
        return str(text.get("body") or "").strip()
    if isinstance(message.get("button"), dict):
        return str(message["button"].get("text") or "").strip()
    if isinstance(message.get("interactive"), dict):
        interactive = message["interactive"]
        if isinstance(interactive.get("button_reply"), dict):
            return str(interactive["button_reply"].get("title") or "").strip()
        if isinstance(interactive.get("list_reply"), dict):
            return str(interactive["list_reply"].get("title") or "").strip()
    return str(message.get("message") or message.get("body") or "").strip()


def normalize_whatsapp_payload(payload: dict[str, Any]) -> NormalizedWhatsAppMessage:
    sender = _normalize_sender(str(payload.get("sender") or payload.get("from") or ""))
    message = str(payload.get("message") or payload.get("text") or "").strip()
    file_ids = payload.get("file_ids") if isinstance(payload.get("file_ids"), list) else []
    trace_id = str(payload.get("trace_id") or "").strip() or None

    if message and sender != "unknown":
        return NormalizedWhatsAppMessage(
            sender=sender,
            message=message,
            file_ids=tuple(_normalize_file_id(item) for item in file_ids),
            trace_id=trace_id,
        )

    entries = payload.get("entry")
    if isinstance(entries, list):
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            for change in entry.get("changes") or []:
                if not isinstance(change, dict):
                    continue
                value = change.get("value")
                if not isinstance(value, dict):
                    continue
                messages = value.get("messages")
                if not isinstance(messages, list):
                    continue
                for item in messages:
                    if not isinstance(item, dict):
                        continue
                    sender = _normalize_sender(str(item.get("from") or sender))
                    message = _extract_text(item)
                    if message:
                        return NormalizedWhatsAppMessage(
                            sender=sender,
                            message=message,
                            file_ids=tuple(_normalize_file_id(token) for token in file_ids),
                            trace_id=trace_id,
                        )

    raise HTTPException(status_code=400, detail="Invalid WhatsApp payload")


def _resolve_whatsapp_scope(
    *,
    db: Session,
    sender: str,
    requested_file_ids: tuple[str, ...],
) -> tuple[str, tuple[str, ...]]:
    owner_sub = _whatsapp_owner_sub(sender)
    if not requested_file_ids:
        tenant_id = str(resolve_or_create_tenant_id(db, owner_sub))
        return tenant_id, ()

    rows = db.query(UploadFile).filter(UploadFile.file_id.in_(requested_file_ids)).all()
    found = {row.file_id: row for row in rows}
    missing = [file_id for file_id in requested_file_ids if file_id not in found]
    if missing:
        raise HTTPException(status_code=404, detail="File not found")
    tenant_ids = {str(row.tenant_id) for row in found.values()}
    if len(tenant_ids) != 1:
        raise HTTPException(status_code=400, detail="Mixed tenant input is not allowed")
    for row in found.values():
        allowed_owners = {str(row.owner_sub or ""), str(row.owner_anon_sub or "")}
        if owner_sub not in allowed_owners and _normalize_sender(sender) not in allowed_owners:
            raise HTTPException(status_code=403, detail="Forbidden")
    return sorted(tenant_ids)[0], requested_file_ids


def _verify_whatsapp_signature(request: Request, raw_body: bytes) -> None:
    secret = str(os.getenv("WHATSAPP_APP_SECRET", "") or "").strip()
    if not secret:
        return

    signature = str(request.headers.get("x-hub-signature-256") or "").strip()
    if not signature.startswith("sha256="):
        raise HTTPException(status_code=403, detail="Forbidden")

    provided = signature.split("=", 1)[1].strip().lower()
    expected = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest().lower()
    if not hmac.compare_digest(provided, expected):
        raise HTTPException(status_code=403, detail="Forbidden")


@router.get("/webhook", response_class=PlainTextResponse)
def verify_whatsapp_webhook(
    mode: str = Query(default="", alias="hub.mode"),
    verify_token: str = Query(default="", alias="hub.verify_token"),
    challenge: str = Query(default="", alias="hub.challenge"),
):
    expected = str(os.getenv("WHATSAPP_VERIFY_TOKEN", "") or "").strip()
    if mode == "subscribe" and expected and verify_token == expected:
        return challenge
    raise HTTPException(status_code=403, detail="Forbidden")


@router.post("/webhook", response_model=WhatsAppWebhookOut)
async def whatsapp_webhook(request: Request, db: Session = Depends(get_db)):
    raw_body = await request.body()
    _verify_whatsapp_signature(request, raw_body)
    try:
        payload = json.loads(raw_body.decode("utf-8")) if raw_body else {}
    except json.JSONDecodeError:
        return WhatsAppWebhookOut(status="error", reply=GENERAL_FAILURE_TEXT)
    if not isinstance(payload, dict):
        return WhatsAppWebhookOut(status="error", reply=GENERAL_FAILURE_TEXT)

    try:
        normalized = normalize_whatsapp_payload(payload)
        tenant_id, file_ids = _resolve_whatsapp_scope(
            db=db,
            sender=normalized.sender,
            requested_file_ids=normalized.file_ids,
        )
        context = RuntimeContext(
            tenant_id=tenant_id,
            project_id="whatsapp",
            principal_type="whatsapp",
            principal_id=_whatsapp_owner_sub(normalized.sender),
            session_id=f"wa_{uuid4().hex[:16]}",
            trace_id=normalized.trace_id or str(uuid4()),
            file_ids=file_ids,
            allowed_tools=GLOBAL_ALLOWLIST,
        )
        request = RuntimeRequest(
            message=normalized.message,
            context=context,
            top_k=4,
            metadata_filters={"project_id": "whatsapp"},
        )
        outcome = execute_channel_runtime(
            request=request,
            db=db,
            runtime=get_stellai_runtime(),
            channel="whatsapp",
        )
        return WhatsAppWebhookOut(
            status="ok",
            reply=str(outcome.reply or RUNTIME_UNAVAILABLE_TEXT),
            mode=outcome.mode.value,
            job_id=outcome.job_id,
        )
    except HTTPException:
        return WhatsAppWebhookOut(status="error", reply=GENERAL_FAILURE_TEXT)
    except Exception:
        return WhatsAppWebhookOut(status="error", reply=RUNTIME_UNAVAILABLE_TEXT)
