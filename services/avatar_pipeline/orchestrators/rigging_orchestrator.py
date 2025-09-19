"""Rigging orchestrator generating skeletons and blendshapes."""

from __future__ import annotations

from services.avatar_pipeline.exceptions import StageExecutionError
from services.avatar_pipeline.models.pipeline import PipelineContext
from services.avatar_pipeline.orchestrators.base import PipelineStage
from services.avatar_pipeline.rigging.blendshape_exporter import BlendshapeExporter
from services.avatar_pipeline.rigging.rigging_engine import RiggingEngine


class RiggingOrchestrator(PipelineStage):
    name = "rigging"

    def __init__(self, engine: RiggingEngine, exporter: BlendshapeExporter) -> None:
        self._engine = engine
        self._exporter = exporter

    def run(self, context: PipelineContext) -> PipelineContext:
        try:
            context.rigging_result = self._engine.rig_mesh(
                context.mesh_result,
                context.texture_path,
                context.temp_dir,
            )
            self._exporter.export(context.rigging_result, context.temp_dir)
            return context
        except Exception as exc:
            raise StageExecutionError(f"Rigging failed: {exc}") from exc
