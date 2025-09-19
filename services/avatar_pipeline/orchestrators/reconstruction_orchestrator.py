"""Runs 3D reconstruction using DECA and texture generation."""

from __future__ import annotations

from services.avatar_pipeline.exceptions import StageExecutionError
from services.avatar_pipeline.models.pipeline import PipelineContext
from services.avatar_pipeline.orchestrators.base import PipelineStage
from services.avatar_pipeline.reconstruction.deca_runner import DecaRunner
from services.avatar_pipeline.textures.texture_generator import TextureGenerator


class ReconstructionOrchestrator(PipelineStage):
    name = "reconstruction"

    def __init__(self, runner: DecaRunner, texture_generator: TextureGenerator) -> None:
        self._runner = runner
        self._texture_generator = texture_generator

    def run(self, context: PipelineContext) -> PipelineContext:
        try:
            context.mesh_result = self._runner.reconstruct(context.aligned_images, context.temp_dir)
            context.texture_path = self._texture_generator.generate(
                context.aligned_images,
                context.mesh_result,
                context.temp_dir,
            )
            return context
        except Exception as exc:
            raise StageExecutionError(f"Reconstruction failed: {exc}") from exc
