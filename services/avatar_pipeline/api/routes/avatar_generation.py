"""API routes for avatar generation lifecycle management."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_serializer
from sqlalchemy.orm import Session

from services.avatar_pipeline.config.settings import Settings, get_settings
from services.avatar_pipeline.jobs.avatar_pipeline_tasks import submit_avatar_job, task_queue
from services.avatar_pipeline.persistence.database import Database
from services.avatar_pipeline.persistence.models import Base, JobStatus
from services.avatar_pipeline.persistence.repository import AvatarJobRepository
from services.avatar_pipeline.validators.photo_validator import PhotoValidator

router = APIRouter(prefix="/avatar", tags=["avatar-generation"])


settings = get_settings()
database = Database(settings)
database.create_schema(Base.metadata)
photo_validator = PhotoValidator()


def get_db_session() -> Session:
    with database.session_scope() as session:
        yield session


def get_repository() -> AvatarJobRepository:
    return AvatarJobRepository(database.SessionLocal)


def get_settings_dependency() -> Settings:
    return settings


class PhotoPayload(BaseModel):
    url: str
    width: int
    height: int
    metadata: Dict[str, str] = Field(default_factory=dict)


class CreateAvatarJobRequest(BaseModel):
    user_id: str
    photos: List[PhotoPayload]
    options: Dict[str, Any] = Field(default_factory=dict)


class JobResponse(BaseModel):
    id: str
    status: JobStatus
    progress: float
    error_message: Optional[str]
    queue_state: str

    @field_serializer("status")
    def serialize_status(self, value: JobStatus) -> str:
        return value.value


class AssetResponse(BaseModel):
    id: str
    asset_type: str
    uri: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


@router.post("/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_avatar_job(
    request: CreateAvatarJobRequest,
    repository: AvatarJobRepository = Depends(get_repository),
    settings: Settings = Depends(get_settings_dependency),
) -> JobResponse:
    try:
        photo_validator.validate([photo.model_dump() for photo in request.photos])
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    payload = {
        "photos": [photo.model_dump() for photo in request.photos],
        "options": request.options,
    }
    job = repository.create_job(request.user_id, payload)
    submit_avatar_job(job.id, settings=settings)
    return JobResponse(
        id=job.id,
        status=job.status,
        progress=job.progress,
        error_message=job.error_message,
        queue_state=task_queue.status(job.id),
    )


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job_status(
    job_id: str,
    repository: AvatarJobRepository = Depends(get_repository),
) -> JobResponse:
    job = repository.get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return JobResponse(
        id=job.id,
        status=job.status,
        progress=job.progress,
        error_message=job.error_message,
        queue_state=task_queue.status(job.id),
    )


@router.get("/jobs/{job_id}/assets", response_model=List[AssetResponse])
def list_job_assets(
    job_id: str,
    repository: AvatarJobRepository = Depends(get_repository),
) -> List[AssetResponse]:
    job = repository.get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    assets = repository.list_assets(job_id)
    return [
        AssetResponse(
            id=asset.id,
            asset_type=asset.asset_type,
            uri=asset.uri,
            metadata=asset.metadata_json or {},
        )
        for asset in assets
    ]
