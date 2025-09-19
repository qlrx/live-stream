"""GLB asset writer with metadata describing Unity import settings."""

from __future__ import annotations

import json
from pathlib import Path

from services.avatar_pipeline.models.pipeline import MeshResult, RiggingResult
from services.avatar_pipeline.writers.base_writer import AssetWriteResult, AssetWriter


class GLBWriter(AssetWriter):
    asset_type = "GLB"

    def write(
        self,
        job_id: str,
        mesh: MeshResult,
        texture_path: Path,
        rigging: RiggingResult,
        output_dir: Path,
    ) -> AssetWriteResult:
        output_dir.mkdir(parents=True, exist_ok=True)
        asset_path = output_dir / f"{job_id}.glb"
        asset_path.write_bytes(b"glTF-binary placeholder")
        metadata = {
            "asset_type": self.asset_type,
            "mesh": str(mesh.mesh_path),
            "texture": str(texture_path),
            "skeleton": str(rigging.skeleton_path),
        }
        metadata.update(self._unity_metadata(rigging))
        metadata_path = asset_path.with_suffix(".glb.metadata.json")
        metadata_path.write_text(json.dumps(metadata, indent=2))
        metadata["metadata_path"] = str(metadata_path)
        return AssetWriteResult(asset_type=self.asset_type, file_path=asset_path, metadata=metadata)
