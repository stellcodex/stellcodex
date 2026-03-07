from __future__ import annotations

from typing import Optional

from app.core.ids import generate_scx_id
from sqlalchemy import String, Text, DateTime, JSON, BigInteger, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class UploadFile(Base):
    __tablename__ = "uploaded_files"

    file_id: Mapped[str] = mapped_column(
        String(40),
        primary_key=True,
        default=generate_scx_id,
    )

    owner_sub: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    owner_user_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=True), nullable=True)
    owner_anon_sub: Mapped[Optional[str]] = mapped_column(Text, nullable=True, index=True)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    privacy: Mapped[str] = mapped_column(String(16), default="private")

    bucket: Mapped[str] = mapped_column(Text, nullable=False)
    object_key: Mapped[str] = mapped_column(Text, nullable=False, unique=True)

    original_filename: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256: Mapped[Optional[str]] = mapped_column(String(64))

    gltf_key: Mapped[Optional[str]] = mapped_column(Text)
    thumbnail_key: Mapped[Optional[str]] = mapped_column(Text)
    folder_key: Mapped[Optional[str]] = mapped_column(Text, index=True)

    meta: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    decision_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    visibility: Mapped[str] = mapped_column(String(16), default="private")
    archived_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
