from __future__ import annotations

from fastapi import APIRouter

from app.core.format_registry import as_public_rows, grouped_payload

router = APIRouter(tags=["formats"])


@router.get("/formats")
def list_formats():
    return {
        "items": as_public_rows(),
        "groups": grouped_payload(),
    }
