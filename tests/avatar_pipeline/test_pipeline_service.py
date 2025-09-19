from pathlib import Path

import pytest

from services.avatar_pipeline.config.settings import Settings
from services.avatar_pipeline.orchestrators.ingestion_orchestrator import IngestionOrchestrator
from services.avatar_pipeline.orchestrators.packaging_orchestrator import PackagingOrchestrator
from services.avatar_pipeline.orchestrators.preprocessing_orchestrator import PreprocessingOrchestrator
from services.avatar_pipeline.orchestrators.reconstruction_orchestrator import ReconstructionOrchestrator
from services.avatar_pipeline.orchestrators.rigging_orchestrator import RiggingOrchestrator
from services.avatar_pipeline.persistence.database import Database
from services.avatar_pipeline.persistence.models import Base, JobStatus
from services.avatar_pipeline.persistence.repository import AvatarJobRepository
from services.avatar_pipeline.preprocess.face_alignment import FaceAlignmentPreprocessor
from services.avatar_pipeline.reconstruction.deca_runner import DecaRunner
from services.avatar_pipeline.rigging.blendshape_exporter import BlendshapeExporter
from services.avatar_pipeline.rigging.rigging_engine import RiggingEngine
from services.avatar_pipeline.service import AvatarPipelineService
from services.avatar_pipeline.textures.texture_generator import TextureGenerator
from services.avatar_pipeline.validators.photo_validator import PhotoValidator
from services.avatar_pipeline.writers.fbx_writer import FBXWriter
from services.avatar_pipeline.writers.glb_writer import GLBWriter


@pytest.fixture
def temp_settings(tmp_path: Path) -> Settings:
    settings = Settings(
        database_url=f"sqlite:///{tmp_path}/avatar.db",
        temp_storage_path=tmp_path / "tmp",
        output_path=tmp_path / "output",
        asset_base_url="http://assets.test",
    )
    return settings


def _build_service(settings: Settings) -> AvatarPipelineService:
    database = Database(settings)
    database.create_schema(Base.metadata)
    repository = AvatarJobRepository(database.SessionLocal)
    ingestion = IngestionOrchestrator(PhotoValidator())
    preprocessing = PreprocessingOrchestrator(FaceAlignmentPreprocessor())
    reconstruction = ReconstructionOrchestrator(
        DecaRunner(settings.deca_model_path, settings.gpu_enabled),
        TextureGenerator(),
    )
    rigging = RiggingOrchestrator(RiggingEngine(), BlendshapeExporter())
    packaging = PackagingOrchestrator([FBXWriter(), GLBWriter()], settings.asset_base_url)
    return AvatarPipelineService(
        repository,
        [ingestion, preprocessing, reconstruction, rigging, packaging],
        settings,
    )


def test_pipeline_service_success(temp_settings: Settings) -> None:
    service = _build_service(temp_settings)
    repository = service.repository
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

    context = service.run(job.id)
    assert set(context.assets) == {"FBX", "GLB"}

    stored_job = repository.get_job(job.id)
    assert stored_job is not None
    assert stored_job.status is JobStatus.SUCCESS
    assert pytest.approx(stored_job.progress, 0.01) == 1.0

    assets = repository.list_assets(job.id)
    assert len(assets) == 2
    assert all(asset.uri.startswith(temp_settings.asset_base_url) for asset in assets)

    for asset_data in context.assets.values():
        assert Path(asset_data["file_path"]).exists()


def test_pipeline_service_failure_marks_job(temp_settings: Settings) -> None:
    service = _build_service(temp_settings)
    repository = service.repository

    class FailingStage:
        name = "failing"

        def run(self, _context):
            raise RuntimeError("boom")

    service.stages.append(FailingStage())

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

    with pytest.raises(RuntimeError):
        service.run(job.id)

    stored_job = repository.get_job(job.id)
    assert stored_job is not None
    assert stored_job.status is JobStatus.FAILED
    assert stored_job.progress < 1.0
