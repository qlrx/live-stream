"""Stub implementation of a DECA-based mesh reconstruction runner."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Optional

from services.avatar_pipeline.models.pipeline import AlignedImage, MeshResult


class DecaRunner:
    """Wraps DECA (or a compatible) model execution."""

    def __init__(self, model_path: Path, gpu_enabled: bool = False) -> None:
        self.model_path = model_path
        self.gpu_enabled = gpu_enabled

    def reconstruct(self, images: Iterable[AlignedImage], working_dir: Optional[Path]) -> MeshResult:
        images = list(images)
        if not images:
            raise ValueError("Aligned images are required for reconstruction.")
        if working_dir is None:
            raise ValueError("working_dir must be provided for reconstruction output.")

        recon_dir = working_dir / "reconstruction"
        recon_dir.mkdir(parents=True, exist_ok=True)

        mesh_path = recon_dir / "avatar_mesh.obj"
        neutral_mesh_path = recon_dir / "avatar_mesh_neutral.obj"
        coefficients = {f"exp_{index}": round(index * 0.1, 3) for index, _ in enumerate(images)}

        mesh_content = {
            "model_path": str(self.model_path),
            "gpu_enabled": self.gpu_enabled,
            "images": [str(img.aligned_path) for img in images],
        }
        mesh_path.write_text(json.dumps(mesh_content))
        neutral_mesh_path.write_text("neutral mesh placeholder")
        return MeshResult(
            mesh_path=mesh_path,
            neutral_mesh_path=neutral_mesh_path,
            expression_coefficients=coefficients,
        )
