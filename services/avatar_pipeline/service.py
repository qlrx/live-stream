"""High level orchestration of the avatar generation pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from services.avatar_pipeline.config.settings import Settings
from services.avatar_pipeline.models.pipeline import PipelineContext
from services.avatar_pipeline.orchestrators.base import PipelineStage
from services.avatar_pipeline.persistence.models import JobStatus
from services.avatar_pipeline.persistence.repository import AvatarJobRepository


@dataclass
class PipelineProgress:
    stage: str
    progress: float


class AvatarPipelineService:
    """Coordinates the full avatar pipeline and persists intermediate progress."""

    def __init__(
        self,
        repository: AvatarJobRepository,
        stages: Iterable[PipelineStage],
        settings: Settings,
    ) -> None:
        self.repository = repository
        self.stages: List[PipelineStage] = list(stages)
        self.settings = settings

    def run(self, job_id: str) -> PipelineContext:
        self.settings.ensure_directories()
        failure: Exception | None = None
        with self.repository.session_scope() as session:
            job = self.repository.get_job_for_update(session, job_id)
            if job is None:
                raise ValueError(f"Job {job_id} not found")

            input_payload = job.input_payload or {}
            context = PipelineContext(
                job_id=job.id,
                user_id=job.user_id,
                photos=input_payload.get("photos", []),
            )
            context.temp_dir = Path(self.settings.temp_storage_path) / job.id
            context.output_dir = Path(self.settings.output_path) / job.id
            context.temp_dir.mkdir(parents=True, exist_ok=True)
            context.output_dir.mkdir(parents=True, exist_ok=True)

            self.repository.update_job_status(session, job, JobStatus.RUNNING, progress=0.01)

            total_stages = len(self.stages)
            for index, stage in enumerate(self.stages, start=1):
                try:
                    context = stage.run(context)
                except Exception as exc:  # store failure and exit loop gracefully
                    self.repository.mark_failure(session, job, str(exc))
                    failure = exc
                    break
                progress = round(index / total_stages, 4)
                self.repository.update_job_status(session, job, JobStatus.RUNNING, progress=progress)

            if failure is None:
                for asset_type, asset_payload in context.assets.items():
                    metadata = dict(asset_payload.get("metadata", {}))
                    if "file_path" in asset_payload:
                        metadata.setdefault("file_path", asset_payload["file_path"])
                    self.repository.add_asset(
                        session,
                        job,
                        asset_type=asset_type,
                        uri=asset_payload.get("uri", ""),
                        metadata=metadata,
                    )

                self.repository.mark_success(session, job, output_payload={"assets": context.assets})

        if failure is not None:
            raise failure

        return context
