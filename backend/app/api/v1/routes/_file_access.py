from __future__ import annotations

"""Shared file/session ownership guards for public-facing route surfaces.

This module centralises the file-access and session-ownership helpers that are
used identically in *both* the orchestrator and approvals route surfaces.
Keeping them in one place prevents the two surfaces from drifting apart on
access-control logic over time.

IMPORTANT: These helpers are intended for PUBLIC route surfaces that receive
authenticated user tokens (Principal). They MUST NOT be used in the
internal_runtime surface, which operates under a different trust model
(shared internal-service token, no user identity).
"""

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.ids import format_scx_file_id, normalize_scx_file_id, normalize_scx_id
from app.models.file import UploadFile as UploadFileModel
from app.models.orchestrator import OrchestratorSession
from app.security.deps import Principal


def normalize_file_uuid(value: str) -> UUID:
    """Parse a raw file_id string into a UUID, raising HTTP 400 on failure."""
    try:
        return normalize_scx_file_id(value)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file id")


def public_file_id(value: str) -> str:
    """Return the canonical public file_id string, falling back to the raw value."""
    try:
        return normalize_scx_id(value)
    except ValueError:
        return value


def get_file_by_identifier(db: Session, value: str) -> UploadFileModel | None:
    """Look up a file by its public or canonical file_id."""
    uid = normalize_file_uuid(value)
    canonical = format_scx_file_id(uid)
    legacy = str(uid)
    return db.query(UploadFileModel).filter(UploadFileModel.file_id.in_((canonical, legacy))).first()


def assert_file_access(file_row: UploadFileModel, principal: Principal) -> None:
    """Raise HTTP 403 if the authenticated principal does not own the file.

    Ownership is determined by matching owner_user_id against principal.user_id.
    Both must be non-empty for access to be granted; a null owner_user_id means
    the file is anonymous and cannot be accessed through this guard.
    """
    file_owner = str(file_row.owner_user_id or "").strip()
    requester = str(principal.user_id or "").strip()
    if not file_owner or not requester or file_owner != requester:
        raise HTTPException(status_code=403, detail="Forbidden")


def get_session_by_id(db: Session, session_id: str) -> OrchestratorSession:
    """Look up an OrchestratorSession by UUID string, raising HTTP 400/404 as needed."""
    try:
        session_uuid = UUID(str(session_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session id")
    session = db.query(OrchestratorSession).filter(OrchestratorSession.id == session_uuid).first()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


def file_for_session(db: Session, session_id: str, principal: Principal) -> UploadFileModel:
    """Return the file associated with a session, asserting the principal owns it."""
    session = get_session_by_id(db, session_id)
    file_row = get_file_by_identifier(db, session.file_id)
    if file_row is None:
        raise HTTPException(status_code=404, detail="File not found")
    assert_file_access(file_row, principal)
    return file_row
