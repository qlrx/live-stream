"""Avatar pipeline service package."""

from __future__ import annotations

from typing import Optional

from services.avatar_pipeline.config.settings import Settings, get_settings
from services.avatar_pipeline.orchestrators.ingestion_orchestrator import IngestionOrchestrator
from services.avatar_pipeline.orchestrators.packaging_orchestrator import PackagingOrchestrator
from services.avatar_pipeline.orchestrators.preprocessing_orchestrator import PreprocessingOrchestrator
from services.avatar_pipeline.orchestrators.reconstruction_orchestrator import ReconstructionOrchestrator
from services.avatar_pipeline.orchestrators.rigging_orchestrator import RiggingOrchestrator
from services.avatar_pipeline.persistence.database import create_session_factory
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


__all__ = ["build_default_service", "AvatarPipelineService"]


def build_default_service(settings: Optional[Settings] = None) -> AvatarPipelineService:
    """Instantiate the pipeline service with production defaults."""

    settings = settings or get_settings()
    session_factory = create_session_factory(settings)
    repository = AvatarJobRepository(session_factory)
    ingestion = IngestionOrchestrator(PhotoValidator())
    preprocessing = PreprocessingOrchestrator(FaceAlignmentPreprocessor())
    reconstruction = ReconstructionOrchestrator(
        DecaRunner(settings.deca_model_path, settings.gpu_enabled),
        TextureGenerator(),
    )
    rigging = RiggingOrchestrator(RiggingEngine(), BlendshapeExporter())
    packaging = PackagingOrchestrator([FBXWriter(), GLBWriter()], settings.asset_base_url)
    stages = [ingestion, preprocessing, reconstruction, rigging, packaging]
    return AvatarPipelineService(repository, stages, settings)
