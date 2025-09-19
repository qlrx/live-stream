"""Texture generation utilities for the avatar pipeline."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Optional

from services.avatar_pipeline.models.pipeline import AlignedImage, MeshResult


class TextureGenerator:
    """Produce texture maps compatible with downstream asset packaging."""

    def generate(
        self,
        images: Iterable[AlignedImage],
        mesh: MeshResult,
        working_dir: Optional[Path],
    ) -> Path:
        if working_dir is None:
            raise ValueError("working_dir must be provided for texture generation output.")
        texture_dir = working_dir / "textures"
        texture_dir.mkdir(parents=True, exist_ok=True)

        texture_path = texture_dir / "albedo.png"
        manifest_path = texture_dir / "albedo.json"

        image_paths = [str(image.aligned_path) for image in images]
        texture_path.write_text("texture placeholder")
        manifest_path.write_text(
            json.dumps(
                {
                    "mesh": str(mesh.mesh_path),
                    "aligned_images": image_paths,
                }
            )
        )
        return texture_path
