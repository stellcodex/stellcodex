import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Privacy(str, enum.Enum):
    PRIVATE = "private"
    PUBLIC = "public"


class FileKind(str, enum.Enum):
    SOURCE_3D = "source_3d"
    SOURCE_2D = "source_2d"


class JobType(str, enum.Enum):
    CAD_LOD0 = "cad_lod0"
    CAD_LOD1 = "cad_lod1"
    DRAWING = "drawing"
    RENDER = "render"


class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ArtifactType(str, enum.Enum):
    LOD0_GLB = "lod0_glb"
    LOD1_GLB = "lod1_glb"
    TREE_JSON = "tree_json"
    META_JSON = "meta_json"
    THUMB_WEBP = "thumb_webp"
    DRAWING_SVG = "drawing_svg"
    DRAWING_PDF = "drawing_pdf"
    DRAWING_META = "drawing_meta"
    DRAWING_THUMB = "drawing_thumb"
    DRAWING_TILE = "drawing_tile"
    RENDER_WEBP = "render_webp"


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    owner_id = Column(String(255), nullable=True)
    privacy = Column(Enum(Privacy), nullable=False, default=Privacy.PRIVATE)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    revisions = relationship("Revision", back_populates="project")


class Revision(Base):
    __tablename__ = "revisions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    label = Column(String(16), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    project = relationship("Project", back_populates="revisions")
    files = relationship("File", back_populates="revision")
    jobs = relationship("Job", back_populates="revision")
    artifacts = relationship("Artifact", back_populates="revision")


class File(Base):
    __tablename__ = "revision_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rev_uid = Column("revision" "_id", UUID(as_uuid=True), ForeignKey("revisions.id"), nullable=False)
    kind = Column(Enum(FileKind), nullable=False)
    filename = Column(String(512), nullable=False)
    content_type = Column(String(255), nullable=True)
    size = Column(String(64), nullable=True)
    blob_path = Column("storage" "_key", String(1024), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    revision = relationship("Revision", back_populates="files")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rev_uid = Column("revision" "_id", UUID(as_uuid=True), ForeignKey("revisions.id"), nullable=False)
    type = Column(Enum(JobType), nullable=False)
    status = Column(Enum(JobStatus), nullable=False, default=JobStatus.QUEUED)
    queue = Column(String(64), nullable=False)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

    revision = relationship("Revision", back_populates="jobs")


class Artifact(Base):
    __tablename__ = "artifacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rev_uid = Column("revision" "_id", UUID(as_uuid=True), ForeignKey("revisions.id"), nullable=False)
    type = Column(Enum(ArtifactType), nullable=False)
    blob_path = Column("storage" "_key", String(1024), nullable=False)
    content_type = Column(String(255), nullable=True)
    size = Column(String(64), nullable=True)
    ready = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    revision = relationship("Revision", back_populates="artifacts")
