from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.v1.routes.files import download_content, get_file as get_file_detail
from app.api.v1.routes.me import me as get_me
from app.api.v1.routes.share import ShareCreateIn, create_share
from app.core.config import settings
from app.db.session import get_db
from app.models.core import Privacy, Project
from app.models.file import UploadFile as UploadFileModel
from app.security.deps import Principal, get_current_principal, get_optional_principal
from app.security.jwt import clear_session_cookie
from app.services.auth_access import revoke_token
from app.workers.tasks import (
    enqueue_convert_file,
    enqueue_mesh2d3d_export,
    enqueue_moldcodes_export,
)

router = APIRouter(tags=["platform-contract"])


class LogoutOut(BaseModel):
    ok: bool = True


class ProjectCreateIn(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class ProjectFileOut(BaseModel):
    file_id: str
    original_filename: str
    status: str
    kind: str | None = None
    mode: str | None = None
    created_at: datetime | None = None


class ProjectOut(BaseModel):
    id: str
    name: str
    file_count: int
    updated_at: datetime | None = None
    files: list[ProjectFileOut] = Field(default_factory=list)


class ShareCreateAliasIn(BaseModel):
    file_id: str
    permission: str = Field(default="view", pattern="^(view|comment|download)$")
    expires_in_seconds: int = Field(default=7 * 24 * 60 * 60, ge=60, le=30 * 24 * 60 * 60)


class JobFileIn(BaseModel):
    file_id: str


class MoldcodesExportIn(BaseModel):
    project_id: str = Field(default="default", min_length=1, max_length=128)
    category: str = Field(min_length=1, max_length=64)
    family: str = Field(min_length=1, max_length=64)
    params: dict[str, Any] = Field(default_factory=dict)


class JobEnqueueOut(BaseModel):
    job_id: str


class ViewerContractOut(BaseModel):
    status: str = "ok"
    default_app: str = "viewer3d"
    mappings: dict[str, list[str]]
    deep_link_template: str = "/view/{file_id}"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _project_id_from_meta(row: UploadFileModel) -> str:
    meta = row.meta if isinstance(row.meta, dict) else {}
    return str(meta.get("project_id") or "default")


def _project_name_from_row(row: Project | None, project_id: str) -> str:
    if row is not None and row.name:
        return row.name
    if project_id == "default":
        return "Default Project"
    return project_id


def _owner_key(principal: Principal) -> str:
    if principal.typ == "user" and principal.user_id:
        return str(principal.user_id)
    if principal.owner_sub:
        return str(principal.owner_sub)
    return "anonymous"


def _scoped_uploads(db: Session, principal: Principal) -> list[UploadFileModel]:
    if principal.typ == "guest":
        owner_sub = principal.owner_sub or ""
        return (
            db.query(UploadFileModel)
            .filter(
                (UploadFileModel.owner_anon_sub == owner_sub)
                | (UploadFileModel.owner_sub == owner_sub)
            )
            .order_by(UploadFileModel.created_at.desc())
            .all()
        )
    return (
        db.query(UploadFileModel)
        .filter(UploadFileModel.owner_user_id == principal.user_id)
        .order_by(UploadFileModel.created_at.desc())
        .all()
    )


def _serialize_project_file(row: UploadFileModel) -> ProjectFileOut:
    meta = row.meta if isinstance(row.meta, dict) else {}
    return ProjectFileOut(
        file_id=row.file_id,
        original_filename=row.original_filename,
        status=row.status,
        kind=str(meta.get("kind")) if meta.get("kind") is not None else None,
        mode=str(meta.get("mode")) if meta.get("mode") is not None else None,
        created_at=row.created_at,
    )


def _project_rows_for_owner(db: Session, principal: Principal) -> dict[str, Project]:
    rows = (
        db.query(Project)
        .filter(Project.owner_id == _owner_key(principal))
        .order_by(Project.created_at.desc())
        .all()
    )
    return {str(row.id): row for row in rows}


@router.get("/auth/me")
def auth_me(
    principal: Principal | None = Depends(get_optional_principal),
    db: Session = Depends(get_db),
):
    return get_me(principal=principal, db=db)


@router.post("/auth/logout", response_model=LogoutOut)
def auth_logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    auth_header = str(request.headers.get("Authorization") or "").strip()
    token = ""
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()
    if not token:
        token = str(request.cookies.get(settings.auth_session_cookie_name) or "").strip()
    if token:
        revoke_token(db, token, reason="logout")
    clear_session_cookie(response, secure=(request.headers.get("x-forwarded-proto") or request.url.scheme) == "https")
    return LogoutOut()


@router.get("/viewer", response_model=ViewerContractOut)
def viewer_contract():
    return ViewerContractOut(
        mappings={
            "viewer3d": ["step", "stp", "iges", "igs", "brep", "brp", "stl", "obj", "ply", "off", "3mf", "amf", "dae", "glb", "gltf"],
            "viewer2d": ["dxf", "dwg", "svg"],
            "docviewer": ["pdf", "doc", "docx", "xlsx", "pptx", "odt", "ods", "odp", "rtf", "txt", "md", "csv", "html", "htm", "png", "jpg", "jpeg", "zip", "rar", "7z"],
        }
    )


@router.get("/projects", response_model=list[ProjectOut])
def list_projects(
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    rows = _scoped_uploads(db, principal)
    project_rows = _project_rows_for_owner(db, principal)
    buckets: dict[str, list[UploadFileModel]] = {}
    for row in rows:
        buckets.setdefault(_project_id_from_meta(row), []).append(row)

    project_ids = set(buckets.keys()) | set(project_rows.keys()) | {"default"}
    items: list[ProjectOut] = []
    for project_id in sorted(project_ids):
        files = buckets.get(project_id, [])
        project_row = project_rows.get(project_id)
        updated_at = files[0].created_at if files else (project_row.created_at if project_row else None)
        items.append(
            ProjectOut(
                id=project_id,
                name=_project_name_from_row(project_row, project_id),
                file_count=len(files),
                updated_at=updated_at,
                files=[_serialize_project_file(row) for row in files],
            )
        )
    items.sort(key=lambda item: item.updated_at or datetime(1970, 1, 1, tzinfo=timezone.utc), reverse=True)
    return items


@router.post("/projects", response_model=ProjectOut, status_code=201)
def create_project(
    data: ProjectCreateIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    row = Project(name=data.name.strip(), owner_id=_owner_key(principal), privacy=Privacy.PRIVATE)
    db.add(row)
    db.commit()
    db.refresh(row)
    return ProjectOut(id=str(row.id), name=row.name, file_count=0, updated_at=row.created_at, files=[])


@router.get("/projects/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    rows = _scoped_uploads(db, principal)
    files = [row for row in rows if _project_id_from_meta(row) == project_id]
    project_rows = _project_rows_for_owner(db, principal)
    project_row = project_rows.get(project_id)
    if project_id != "default" and project_row is None and not files:
        raise HTTPException(status_code=404, detail="Project not found")
    updated_at = files[0].created_at if files else (project_row.created_at if project_row else None)
    return ProjectOut(
        id=project_id,
        name=_project_name_from_row(project_row, project_id),
        file_count=len(files),
        updated_at=updated_at,
        files=[_serialize_project_file(row) for row in files],
    )


@router.get("/files/{file_id}/meta")
def file_meta_alias(
    file_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    return get_file_detail(file_id=file_id, db=db, principal=principal)


@router.get("/files/{file_id}/download")
def file_download_alias(
    file_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    return download_content(file_id=file_id, db=db, principal=principal)


@router.post("/share/create")
def share_create_alias(
    data: ShareCreateAliasIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    return create_share(
        file_id=data.file_id,
        data=ShareCreateIn(permission=data.permission, expires_in_seconds=data.expires_in_seconds),
        db=db,
        principal=principal,
    )


@router.post("/jobs/convert", response_model=JobEnqueueOut)
def job_convert(
    data: JobFileIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    rows = _scoped_uploads(db, principal)
    if not any(row.file_id == data.file_id for row in rows):
        raise HTTPException(status_code=404, detail="File not found")
    return JobEnqueueOut(job_id=enqueue_convert_file(data.file_id))


@router.post("/jobs/mesh2d3d", response_model=JobEnqueueOut)
def job_mesh2d3d(
    data: JobFileIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    rows = _scoped_uploads(db, principal)
    if not any(row.file_id == data.file_id for row in rows):
        raise HTTPException(status_code=404, detail="File not found")
    return JobEnqueueOut(job_id=enqueue_mesh2d3d_export(data.file_id))


@router.post("/jobs/moldcodes_export", response_model=JobEnqueueOut)
def job_moldcodes_export(
    data: MoldcodesExportIn,
    principal: Principal = Depends(get_current_principal),
):
    return JobEnqueueOut(
        job_id=enqueue_moldcodes_export(
            owner_sub=_owner_key(principal),
            owner_user_id=str(principal.user_id) if principal.user_id else None,
            owner_anon_sub=principal.owner_sub,
            is_anonymous=principal.typ == "guest",
            project_id=data.project_id,
            category=data.category,
            family=data.family,
            params=data.params,
        )
    )
