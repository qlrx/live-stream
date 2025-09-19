"""Blendshape exporter producing metadata for animation systems."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from services.avatar_pipeline.models.pipeline import RiggingResult


class BlendshapeExporter:
    """Serialize blendshape data to disk for game engine consumption."""

    def export(self, result: RiggingResult, working_dir: Optional[Path]) -> Path:
        if working_dir is None:
            raise ValueError("working_dir must be provided for blendshape export.")
        manifest_dir = working_dir / "rig"
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = manifest_dir / "blendshape_manifest.json"
        payload = {
            "blendshape_path": str(result.blendshape_path),
            "controls": result.controls,
        }
        manifest_path.write_text(json.dumps(payload))
        return manifest_path
