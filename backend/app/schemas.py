from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class JobOut(BaseModel):
    id: UUID
    type: str
    status: str
    queue: str
    error: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    finished_at: Optional[datetime]


class ArtifactOut(BaseModel):
    id: UUID
    type: str
    storage_key: str
    ready: bool
    content_type: Optional[str]
    size: Optional[str]
    created_at: datetime
    url: Optional[str] = None
    glb_url: Optional[str] = None


class UploadResponse(BaseModel):
    project_id: UUID
    revision_id: UUID
    file_id: str
    job_id: UUID


class StatusResponse(BaseModel):
    revision_id: UUID
    file_id: str
    jobs: List[JobOut]
    artifacts: List[ArtifactOut]
