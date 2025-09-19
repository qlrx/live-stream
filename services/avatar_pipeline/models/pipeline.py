"""Dataclasses describing pipeline artifacts used by orchestrators."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class Photo:
    """Canonical representation of a user supplied photo."""

    url: str
    width: int
    height: int
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class AlignedImage:
    """Represents a face-aligned image ready for reconstruction."""

    source_photo: Photo
    aligned_path: Path
    landmarks_path: Optional[Path] = None


@dataclass
class MeshResult:
    """Meshes produced by the reconstruction stage."""

    mesh_path: Path
    neutral_mesh_path: Optional[Path] = None
    expression_coefficients: Dict[str, float] = field(default_factory=dict)


@dataclass
class RiggingResult:
    """Output from the rigging pipeline."""

    skeleton_path: Path
    blendshape_path: Path
    controls: Dict[str, float] = field(default_factory=dict)


@dataclass
class PipelineContext:
    """Mutable context passed across pipeline stages."""

    job_id: str
    user_id: str
    photos: List[Photo] = field(default_factory=list)
    aligned_images: List[AlignedImage] = field(default_factory=list)
    mesh_result: Optional[MeshResult] = None
    texture_path: Optional[Path] = None
    rigging_result: Optional[RiggingResult] = None
    assets: Dict[str, Dict[str, str]] = field(default_factory=dict)
    temp_dir: Optional[Path] = None
    output_dir: Optional[Path] = None
