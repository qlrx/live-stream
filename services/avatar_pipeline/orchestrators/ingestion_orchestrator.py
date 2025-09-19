"""Ingestion orchestrator validating source photos."""

from __future__ import annotations

from services.avatar_pipeline.exceptions import StageExecutionError, ValidationError
from services.avatar_pipeline.models.pipeline import PipelineContext
from services.avatar_pipeline.orchestrators.base import PipelineStage
from services.avatar_pipeline.validators.photo_validator import PhotoValidator


class IngestionOrchestrator(PipelineStage):
    name = "ingestion"

    def __init__(self, validator: PhotoValidator) -> None:
        self._validator = validator

    def run(self, context: PipelineContext) -> PipelineContext:
        try:
            context.photos = self._validator.validate(context.photos)
            return context
        except ValidationError as exc:  # re-wrap to provide stage information
            raise StageExecutionError(str(exc)) from exc
