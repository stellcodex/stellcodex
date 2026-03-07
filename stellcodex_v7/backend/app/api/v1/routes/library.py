from __future__ import annotations

import re
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.ids import format_scx_file_id, normalize_scx_file_id, normalize_scx_id
from app.db.session import get_db
from app.models.file import UploadFile as UploadFileModel
from app.models.library_item import LibraryItem
from app.models.share import Share
from app.security.deps import Principal, get_current_principal

router = APIRouter(tags=["library"])


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9\\-\\s_]", "", value or "").strip().lower()
    cleaned = re.sub(r"[\\s_]+", "-", cleaned)
    cleaned = re.sub(r"-{2,}", "-", cleaned).strip("-")
    return cleaned or "model"


def _normalize_file_uuid(value: str) -> UUID:
    try:
        return normalize_scx_file_id(value)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file id")


def _public_file_id(value: str) -> str:
    try:
        return normalize_scx_id(value)
    except ValueError:
        return value


def _get_file_by_identifier(db: Session, value: str) -> UploadFileModel | None:
    uid = _normalize_file_uuid(value)
    canonical = format_scx_file_id(uid)
    legacy = str(uid)
    return db.query(UploadFileModel).filter(UploadFileModel.file_id.in_((canonical, legacy))).first()


def _owner_key(principal: Principal) -> str:
    if principal.typ == "user" and principal.user_id:
        return f"user:{principal.user_id}"
    if principal.owner_sub:
        return f"guest:{principal.owner_sub}"
    raise HTTPException(status_code=401, detail="Unauthorized")


def _assert_file_access(f: UploadFileModel, principal: Principal) -> None:
    if principal.typ == "guest":
        owner_sub = principal.owner_sub or ""
        if f.owner_anon_sub != owner_sub and f.owner_sub != owner_sub:
            raise HTTPException(status_code=403, detail="Forbidden")
        return
    if str(f.owner_user_id or "") != str(principal.user_id or ""):
        raise HTTPException(status_code=403, detail="Forbidden")


def _ensure_share_token(db: Session, file_id: str) -> str:
    active = (
        db.query(Share)
        .filter(Share.file_id == file_id, Share.revoked_at.is_(None), Share.expires_at > _now())
        .order_by(Share.created_at.desc())
        .first()
    )
    if active:
        return active.token

    token = secrets.token_urlsafe(24)
    share = Share(
        file_id=file_id,
        created_by_user_id=None,
        token=token,
        permission="view",
        expires_at=_now() + timedelta(days=365),
    )
    db.add(share)
    db.flush()
    return token


class LibraryPublishIn(BaseModel):
    file_id: str
    visibility: str = Field(default="public", pattern="^(private|unlisted|public)$")
    title: str | None = None
    description: str | None = None
    tags: list[str] | None = None


class LibraryUpdateIn(BaseModel):
    title: str | None = None
    description: str | None = None
    tags: list[str] | None = None
    visibility: str | None = Field(default=None, pattern="^(private|unlisted|public)$")


class LibraryUnpublishIn(BaseModel):
    item_id: str


class LibraryItemOut(BaseModel):
    id: str
    file_id: str
    visibility: str
    slug: str
    title: str
    description: str | None
    tags: list[str]
    cover_thumb: str | None
    share_url: str | None
    stats: dict
    created_at: datetime
    updated_at: datetime


def _serialize_item(item: LibraryItem) -> LibraryItemOut:
    return LibraryItemOut(
        id=str(item.id),
        file_id=_public_file_id(item.file_id),
        visibility=item.visibility,
        slug=item.slug,
        title=item.title,
        description=item.description,
        tags=item.tags or [],
        cover_thumb=item.cover_thumb,
        share_url=(f"/s/{item.share_token}" if item.share_token else None),
        stats=item.stats or {},
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.post("/library/publish", response_model=LibraryItemOut)
def publish_library_item(
    payload: LibraryPublishIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    f = _get_file_by_identifier(db, payload.file_id)
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(f, principal)
    if f.status != "ready":
        raise HTTPException(status_code=409, detail="File not ready")

    owner_key = _owner_key(principal)
    existing = db.query(LibraryItem).filter(LibraryItem.owner_key == owner_key, LibraryItem.file_id == f.file_id).first()
    title = (payload.title or f.original_filename or _public_file_id(f.file_id)).strip()
    base_slug = _slugify(title)
    slug = base_slug
    while db.query(LibraryItem).filter(LibraryItem.slug == slug).first() and (not existing or existing.slug != slug):
        slug = f"{base_slug}-{secrets.token_hex(2)}"

    share_token = _ensure_share_token(db, f.file_id)
    cover_thumb = f"/api/v1/files/{_public_file_id(f.file_id)}/thumbnail" if f.thumbnail_key else None

    if existing:
        existing.visibility = payload.visibility
        existing.slug = slug
        existing.title = title
        existing.description = payload.description
        existing.tags = payload.tags or []
        existing.cover_thumb = cover_thumb
        existing.share_token = share_token
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return _serialize_item(existing)

    item = LibraryItem(
        owner_key=owner_key,
        owner_user_id=UUID(principal.user_id) if principal.typ == "user" and principal.user_id else None,
        file_id=f.file_id,
        visibility=payload.visibility,
        slug=slug,
        title=title,
        description=payload.description,
        tags=payload.tags or [],
        cover_thumb=cover_thumb,
        share_token=share_token,
        stats={"views": 0},
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return _serialize_item(item)


@router.patch("/library/item/{item_id}", response_model=LibraryItemOut)
def update_library_item(
    item_id: str,
    payload: LibraryUpdateIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    owner_key = _owner_key(principal)
    item = db.query(LibraryItem).filter(LibraryItem.id == item_id, LibraryItem.owner_key == owner_key).first()
    if not item:
        raise HTTPException(status_code=404, detail="Library item not found")

    if payload.title is not None:
        item.title = payload.title.strip() or item.title
    if payload.description is not None:
        item.description = payload.description
    if payload.tags is not None:
        item.tags = payload.tags
    if payload.visibility is not None:
        item.visibility = payload.visibility

    db.add(item)
    db.commit()
    db.refresh(item)
    return _serialize_item(item)


@router.post("/library/unpublish")
def unpublish_library_item(
    payload: LibraryUnpublishIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    owner_key = _owner_key(principal)
    item = db.query(LibraryItem).filter(LibraryItem.id == payload.item_id, LibraryItem.owner_key == owner_key).first()
    if not item:
        raise HTTPException(status_code=404, detail="Library item not found")
    item.visibility = "private"
    db.add(item)
    db.commit()
    return {"status": "ok"}


@router.get("/library/feed")
def library_feed(
    q: str | None = None,
    sort: str = Query(default="new", pattern="^(new|old)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=24, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(LibraryItem).filter(LibraryItem.visibility == "public")
    if q:
        token = f"%{q.strip()}%"
        query = query.filter((LibraryItem.title.ilike(token)) | (LibraryItem.description.ilike(token)))
    total = query.count()
    ordering = LibraryItem.created_at.desc() if sort == "new" else LibraryItem.created_at.asc()
    rows = query.order_by(ordering).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [_serialize_item(row).model_dump() for row in rows], "total": total, "page": page, "page_size": page_size}


@router.get("/library/item/{slug}", response_model=LibraryItemOut)
def library_item_by_slug(slug: str, db: Session = Depends(get_db)):
    row = db.query(LibraryItem).filter(LibraryItem.slug == slug, LibraryItem.visibility == "public").first()
    if not row:
        raise HTTPException(status_code=404, detail="Library item not found")
    return _serialize_item(row)

