"""Packaging orchestrator turning intermediate results into distributable assets."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from services.avatar_pipeline.exceptions import StageExecutionError
from services.avatar_pipeline.models.pipeline import PipelineContext
from services.avatar_pipeline.orchestrators.base import PipelineStage
from services.avatar_pipeline.writers.base_writer import AssetWriteResult, AssetWriter


class PackagingOrchestrator(PipelineStage):
    name = "packaging"

    def __init__(self, writers: Iterable[AssetWriter], asset_base_url: str) -> None:
        self._writers = list(writers)
        self._asset_base_url = asset_base_url.rstrip("/")

    def run(self, context: PipelineContext) -> PipelineContext:
        if context.mesh_result is None or context.rigging_result is None or context.texture_path is None:
            raise StageExecutionError("Packaging requires mesh, rig, and texture data.")
        try:
            output_dir = context.output_dir or context.temp_dir or Path("./output")
            output_dir.mkdir(parents=True, exist_ok=True)
            for writer in self._writers:
                result: AssetWriteResult = writer.write(
                    context.job_id,
                    context.mesh_result,
                    context.texture_path,
                    context.rigging_result,
                    output_dir,
                )
                uri = f"{self._asset_base_url}/{result.file_path.name}"
                context.assets[result.asset_type] = {
                    "uri": uri,
                    "file_path": str(result.file_path),
                    "metadata": result.metadata,
                }
            return context
        except Exception as exc:
            raise StageExecutionError(f"Packaging failed: {exc}") from exc
