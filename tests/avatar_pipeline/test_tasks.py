import time
from pathlib import Path

import pytest

from services.avatar_pipeline.config.settings import Settings
from services.avatar_pipeline.jobs import avatar_pipeline_tasks as tasks
from services.avatar_pipeline.persistence.database import Database
from services.avatar_pipeline.persistence.models import Base, JobStatus
from services.avatar_pipeline.persistence.repository import AvatarJobRepository


def test_submit_avatar_job_runs_pipeline(tmp_path: Path) -> None:
    settings = Settings(
        database_url=f"sqlite:///{tmp_path}/avatar.db",
        temp_storage_path=tmp_path / "tmp",
        output_path=tmp_path / "output",
        asset_base_url="http://assets.test",
    )
    database = Database(settings)
    database.create_schema(Base.metadata)
    repository = AvatarJobRepository(database.SessionLocal)

    job = repository.create_job(
        user_id="user-123",
        payload={
            "photos": [
                {
                    "url": "https://example.com/photo.jpg",
                    "width": 512,
                    "height": 512,
                }
            ]
        },
    )

    handle = tasks.submit_avatar_job(job.id, settings=settings)
    result = handle.result(timeout=10)
    assert isinstance(result, dict) or result is None

    # Give the executor a moment to persist results
    time.sleep(0.1)

    stored_job = repository.get_job(job.id)
    assert stored_job is not None
    assert stored_job.status is JobStatus.SUCCESS
    assert stored_job.progress == pytest.approx(1.0, 0.01)
