"""FBX asset writer generating Unity compatible metadata."""

from __future__ import annotations

import json
from pathlib import Path

from services.avatar_pipeline.models.pipeline import MeshResult, RiggingResult
from services.avatar_pipeline.writers.base_writer import AssetWriteResult, AssetWriter


class FBXWriter(AssetWriter):
    asset_type = "FBX"

    def write(
        self,
        job_id: str,
        mesh: MeshResult,
        texture_path: Path,
        rigging: RiggingResult,
        output_dir: Path,
    ) -> AssetWriteResult:
        output_dir.mkdir(parents=True, exist_ok=True)
        asset_path = output_dir / f"{job_id}.fbx"
        asset_path.write_text(
            "FBX placeholder generated for job {job_id}\n".format(job_id=job_id)
        )
        metadata = {
            "asset_type": self.asset_type,
            "mesh": str(mesh.mesh_path),
            "texture": str(texture_path),
        }
        metadata.update(self._unity_metadata(rigging))
        metadata_path = asset_path.with_suffix(".fbx.metadata.json")
        metadata_path.write_text(json.dumps(metadata, indent=2))
        metadata["metadata_path"] = str(metadata_path)
        return AssetWriteResult(asset_type=self.asset_type, file_path=asset_path, metadata=metadata)
