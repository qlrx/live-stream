"""Preprocessing orchestrator aligning faces prior to reconstruction."""

from __future__ import annotations

from services.avatar_pipeline.exceptions import StageExecutionError
from services.avatar_pipeline.models.pipeline import PipelineContext
from services.avatar_pipeline.orchestrators.base import PipelineStage
from services.avatar_pipeline.preprocess.face_alignment import FaceAlignmentPreprocessor


class PreprocessingOrchestrator(PipelineStage):
    name = "preprocessing"

    def __init__(self, preprocessor: FaceAlignmentPreprocessor) -> None:
        self._preprocessor = preprocessor

    def run(self, context: PipelineContext) -> PipelineContext:
        try:
            context.aligned_images = self._preprocessor.align(context.photos, context.temp_dir)
            return context
        except Exception as exc:
            raise StageExecutionError(f"Face alignment failed: {exc}") from exc
