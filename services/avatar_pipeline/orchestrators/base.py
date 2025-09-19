"""Common utilities shared by orchestrators."""

from __future__ import annotations

from abc import ABC, abstractmethod
from services.avatar_pipeline.models.pipeline import PipelineContext


class PipelineStage(ABC):
    """Abstract base class describing a pipeline stage."""

    name: str

    @abstractmethod
    def run(self, context: PipelineContext) -> PipelineContext:
        """Execute the stage and mutate/return the pipeline context."""


class CompositeOrchestrator:
    """Utility that runs a sequence of stages in order."""

    def __init__(self, *stages: PipelineStage) -> None:
        self._stages = list(stages)

    def add_stage(self, stage: PipelineStage) -> None:
        self._stages.append(stage)

    def run(self, context: PipelineContext) -> PipelineContext:
        for stage in self._stages:
            context = stage.run(context)
        return context
