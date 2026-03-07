from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.format_registry import get_rule_for_filename
from app.core.ids import normalize_scx_id
from app.db.session import get_db
from app.models.file import UploadFile
from app.security.deps import Principal, get_current_principal

router = APIRouter(tags=["explorer"])


class ExplorerFolderOut(BaseModel):
    folder_key: str
    parent_key: str | None = None
    label: str
    item_count: int


class ExplorerTreeOut(BaseModel):
    project_id: str
    folders: list[ExplorerFolderOut]


class ExplorerItemOut(BaseModel):
    file_id: str
    name: str
    ext: str
    kind: str
    mode: str
    size: int
    created_at: datetime
    status: str
    thumb_url: str | None = None
    preview_urls: list[str] | None = None
    bbox_meta: dict[str, Any] | None = None
    part_count: int | None = None
    open_url: str


class ExplorerListOut(BaseModel):
    project_id: str
    folder_key: str | None = None
    total: int
    items: list[ExplorerItemOut]


def _public_file_id(value: str) -> str:
    return normalize_scx_id(value)


def _project_id(row: UploadFile) -> str:
    meta = row.meta if isinstance(row.meta, dict) else {}
    return str(meta.get("project_id") or "default")


def _kind_mode(row: UploadFile) -> tuple[str, str]:
    meta = row.meta if isinstance(row.meta, dict) else {}
    rule = get_rule_for_filename(row.original_filename or "")
    kind = str(meta.get("kind") or (rule.kind if rule else "3d"))
    mode = str(meta.get("mode") or (rule.mode if rule else "brep"))
    return kind, mode


def _folder_key(row: UploadFile) -> str:
    project_id = _project_id(row)
    kind, mode = _kind_mode(row)
    return row.folder_key or f"project/{project_id}/{kind}/{mode}"


def _preview_urls(row: UploadFile) -> list[str] | None:
    if row.status != "ready":
        return None
    meta = row.meta if isinstance(row.meta, dict) else {}
    public_id = _public_file_id(row.file_id)
    if isinstance(meta.get("preview_jpg_keys"), list):
        keys = [k for k in meta["preview_jpg_keys"] if isinstance(k, str) and k]
        if keys:
            return [f"/api/v1/files/{public_id}/preview/{idx}" for idx in range(len(keys))]
    if isinstance(meta.get("pdf_key"), str):
        return [f"/api/v1/files/{public_id}/pdf"]
    if row.thumbnail_key:
        return [f"/api/v1/files/{public_id}/thumbnail"]
    return None


def _bbox_meta(row: UploadFile) -> dict[str, Any] | None:
    meta = row.meta if isinstance(row.meta, dict) else {}
    geometry = meta.get("geometry_meta_json")
    if isinstance(geometry, dict):
        bbox = geometry.get("bbox")
        return bbox if isinstance(bbox, dict) else None
    return None


def _part_count(row: UploadFile) -> int | None:
    meta = row.meta if isinstance(row.meta, dict) else {}
    direct = meta.get("part_count")
    if isinstance(direct, int):
        return direct
    geometry = meta.get("geometry_meta_json")
    if isinstance(geometry, dict) and isinstance(geometry.get("part_count"), int):
        return int(geometry.get("part_count"))
    return None


def _base_query(db: Session, principal: Principal):
    if principal.typ == "guest":
        owner_sub = principal.owner_sub or ""
        return db.query(UploadFile).filter(
            (UploadFile.owner_anon_sub == owner_sub) | (UploadFile.owner_sub == owner_sub)
        )
    return db.query(UploadFile).filter(UploadFile.owner_user_id == principal.user_id)


@router.get("/explorer/tree", response_model=ExplorerTreeOut)
def explorer_tree(
    project_id: str = Query(default="default"),
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    rows = _base_query(db, principal).order_by(UploadFile.created_at.desc()).all()
    counts: dict[str, int] = {}

    for row in rows:
        row_project = _project_id(row)
        if row_project != project_id:
            continue
        key = _folder_key(row)
        parts = key.split("/")
        if len(parts) < 4:
            continue
        prefixes = [
            "/".join(parts[:2]),
            "/".join(parts[:3]),
            "/".join(parts[:4]),
        ]
        for prefix in prefixes:
            counts[prefix] = counts.get(prefix, 0) + 1

    folders: list[ExplorerFolderOut] = []
    for key in sorted(counts):
        parts = key.split("/")
        parent_key = "/".join(parts[:-1]) if len(parts) > 1 else None
        folders.append(
            ExplorerFolderOut(
                folder_key=key,
                parent_key=parent_key,
                label=parts[-1],
                item_count=counts[key],
            )
        )
    return ExplorerTreeOut(project_id=project_id, folders=folders)


@router.get("/explorer/list", response_model=ExplorerListOut)
def explorer_list(
    project_id: str = Query(default="default"),
    folder_key: str | None = Query(default=None),
    q: str | None = Query(default=None),
    sort: str = Query(default="newest"),
    filter: str | None = Query(default=None),
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    rows = _base_query(db, principal).all()
    needle = (q or "").strip().lower()
    filter_value = (filter or "").strip().lower()
    items: list[ExplorerItemOut] = []

    for row in rows:
        if _project_id(row) != project_id:
            continue
        key = _folder_key(row)
        if folder_key and key != folder_key:
            continue
        kind, mode = _kind_mode(row)
        if filter_value and filter_value not in {kind.lower(), mode.lower()}:
            continue
        name = row.original_filename or "unnamed"
        if needle and needle not in name.lower():
            continue
        ext = Path(name).suffix.lower().lstrip(".")
        public_id = _public_file_id(row.file_id)
        items.append(
            ExplorerItemOut(
                file_id=public_id,
                name=name,
                ext=ext,
                kind=kind,
                mode=mode,
                size=int(row.size_bytes),
                created_at=row.created_at,
                status=row.status,
                thumb_url=(f"/api/v1/files/{public_id}/thumbnail" if row.thumbnail_key else None),
                preview_urls=_preview_urls(row),
                bbox_meta=_bbox_meta(row),
                part_count=_part_count(row),
                open_url=f"/view/{public_id}",
            )
        )

    reverse = sort != "oldest"
    items.sort(key=lambda item: item.created_at, reverse=reverse)
    return ExplorerListOut(project_id=project_id, folder_key=folder_key, total=len(items), items=items)
