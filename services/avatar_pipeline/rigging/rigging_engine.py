"""Generate rig controls and skeleton data for avatars."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from services.avatar_pipeline.models.pipeline import MeshResult, RiggingResult


class RiggingEngine:
    """Fake rigging engine that emits skeleton and control rig metadata."""

    def rig_mesh(
        self,
        mesh: MeshResult,
        texture_path: Optional[Path],
        working_dir: Optional[Path],
    ) -> RiggingResult:
        if working_dir is None:
            raise ValueError("working_dir must be provided for rigging output.")
        rig_dir = working_dir / "rig"
        rig_dir.mkdir(parents=True, exist_ok=True)

        skeleton_path = rig_dir / "skeleton.json"
        blendshape_path = rig_dir / "blendshapes.json"

        controls = {"jaw_open": 0.0, "eye_blink_left": 0.0, "eye_blink_right": 0.0}
        skeleton_payload = {
            "mesh": str(mesh.mesh_path),
            "neutral_mesh": str(mesh.neutral_mesh_path) if mesh.neutral_mesh_path else None,
            "texture": str(texture_path) if texture_path else None,
        }
        skeleton_path.write_text(json.dumps(skeleton_payload))
        blendshape_path.write_text(json.dumps(mesh.expression_coefficients))
        return RiggingResult(
            skeleton_path=skeleton_path,
            blendshape_path=blendshape_path,
            controls=controls,
        )
