"""
Stell Chat API — Admin Panel Endpoint
POST /api/v1/stell/chat  (admin JWT zorunlu)
İç ağda stell-webhook (port 4500) ile konuşur.
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error
from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from pydantic import BaseModel

from app.security.deps import require_role, Principal

router = APIRouter(prefix="/stell", tags=["stell"])

# Docker host IP üzerinden webhook'a ulaş
STELL_INTERNAL_URL = "http://172.17.0.1:4500/stell/internal/chat"


class ChatIn(BaseModel):
    message: str


class ChatOut(BaseModel):
    reply: str


@router.post("/chat", response_model=ChatOut)
def stell_chat(
    body: ChatIn,
    principal: Principal = Depends(require_role("admin")),
):
    """Admin panelden Stell'e mesaj gönder."""
    try:
        payload = json.dumps({"message": body.message.strip()}).encode()
        req = urllib.request.Request(
            STELL_INTERNAL_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
            return ChatOut(reply=data["reply"])
    except urllib.error.URLError as e:
        raise HTTPException(status_code=503, detail=f"Stell servisi yanıt vermiyor: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hata: {e}")
