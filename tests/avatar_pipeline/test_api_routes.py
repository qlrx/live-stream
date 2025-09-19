from typing import Optional

from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.avatar_pipeline import build_default_service
from services.avatar_pipeline.api.routes import avatar_generation
from services.avatar_pipeline.config.settings import Settings
from services.avatar_pipeline.persistence.database import Database
from services.avatar_pipeline.persistence.models import Base, JobStatus


def configure_test_environment(tmp_path):
    settings = Settings(
        database_url=f"sqlite:///{tmp_path}/avatar.db",
        temp_storage_path=tmp_path / "tmp",
        output_path=tmp_path / "output",
        asset_base_url="http://assets.test",
    )
    avatar_generation.settings = settings
    avatar_generation.database = Database(settings)
    avatar_generation.database.create_schema(Base.metadata)
    avatar_generation.photo_validator = avatar_generation.PhotoValidator()

    class ImmediateQueue:
        def __init__(self) -> None:
            self._statuses = {}

        def run(self, job_id: str) -> None:
            self._statuses[job_id] = "RUNNING"
            service = build_default_service(settings=settings)
            service.run(job_id)
            self._statuses[job_id] = "SUCCESS"

        def status(self, job_id: str) -> str:
            return self._statuses.get(job_id, "IDLE")

    queue = ImmediateQueue()

    def immediate_submit(job_id: str, settings: Optional[Settings] = None):
        queue.run(job_id)

    avatar_generation.task_queue = queue
    avatar_generation.submit_avatar_job = immediate_submit

    return settings


def test_create_and_query_avatar_job(tmp_path):
    configure_test_environment(tmp_path)
    app = FastAPI()
    app.include_router(avatar_generation.router)
    client = TestClient(app)

    payload = {
        "user_id": "user-123",
        "photos": [
            {"url": "https://example.com/photo.jpg", "width": 512, "height": 512}
        ],
        "options": {},
    }

    response = client.post("/avatar/jobs", json=payload)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == JobStatus.PENDING.value
    job_id = body["id"]

    status_response = client.get(f"/avatar/jobs/{job_id}")
    assert status_response.status_code == 200
    status_body = status_response.json()
    assert status_body["status"] == JobStatus.SUCCESS.value
    assert status_body["queue_state"] == "SUCCESS"

    assets_response = client.get(f"/avatar/jobs/{job_id}/assets")
    assert assets_response.status_code == 200
    assets = assets_response.json()
    assert len(assets) == 2
    assert {asset["asset_type"] for asset in assets} == {"FBX", "GLB"}


def test_create_job_validation_error(tmp_path):
    configure_test_environment(tmp_path)
    app = FastAPI()
    app.include_router(avatar_generation.router)
    client = TestClient(app)

    payload = {
        "user_id": "user-123",
        "photos": [
            {"url": "", "width": 100, "height": 100}
        ],
    }

    response = client.post("/avatar/jobs", json=payload)
    assert response.status_code == 400
