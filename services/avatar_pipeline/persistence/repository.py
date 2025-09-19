"""Repository abstraction for persisting avatar generation jobs."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Dict, Iterable, List, Optional

from sqlalchemy.orm import Session, sessionmaker

from services.avatar_pipeline.persistence.models import (
    AvatarGenerationJob,
    GeneratedAsset,
    JobStatus,
)


class AvatarJobRepository:
    """Encapsulates data access for avatar generation jobs."""

    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    @contextmanager
    def session_scope(self) -> Iterable[Session]:
        session: Session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def create_job(self, user_id: str, payload: Dict) -> AvatarGenerationJob:
        with self.session_scope() as session:
            job = AvatarGenerationJob(user_id=user_id, input_payload=payload)
            session.add(job)
            session.flush()
            session.refresh(job)
            return job

    def get_job(self, job_id: str) -> Optional[AvatarGenerationJob]:
        with self.session_scope() as session:
            return session.get(AvatarGenerationJob, job_id)

    def get_job_for_update(self, session: Session, job_id: str) -> Optional[AvatarGenerationJob]:
        return session.get(AvatarGenerationJob, job_id)

    def update_job_status(
        self,
        session: Session,
        job: AvatarGenerationJob,
        status: JobStatus,
        progress: Optional[float] = None,
        error_message: Optional[str] = None,
        output_payload: Optional[Dict] = None,
    ) -> None:
        job.status = status
        if progress is not None:
            job.progress = progress
        if error_message is not None:
            job.error_message = error_message
        if output_payload is not None:
            job.output_payload = output_payload
        session.add(job)

    def add_asset(
        self,
        session: Session,
        job: AvatarGenerationJob,
        asset_type: str,
        uri: str,
        metadata: Optional[Dict] = None,
    ) -> GeneratedAsset:
        asset = GeneratedAsset(job_id=job.id, asset_type=asset_type, uri=uri, metadata_json=metadata)
        session.add(asset)
        session.flush()
        session.refresh(asset)
        return asset

    def list_assets(self, job_id: str) -> List[GeneratedAsset]:
        with self.session_scope() as session:
            job = session.get(AvatarGenerationJob, job_id)
            if not job:
                return []
            return [asset for asset in job.assets]

    def mark_failure(self, session: Session, job: AvatarGenerationJob, message: str) -> None:
        self.update_job_status(session, job, JobStatus.FAILED, error_message=message)

    def mark_success(
        self,
        session: Session,
        job: AvatarGenerationJob,
        output_payload: Optional[Dict] = None,
    ) -> None:
        self.update_job_status(session, job, JobStatus.SUCCESS, progress=1.0, output_payload=output_payload)
