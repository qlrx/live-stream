"""Base utilities for asset writers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from services.avatar_pipeline.models.pipeline import MeshResult, RiggingResult


@dataclass
class AssetWriteResult:
    """Represents a file emitted by an asset writer."""

    asset_type: str
    file_path: Path
    metadata: Dict[str, str]


class AssetWriter(ABC):
    """Abstract writer that serializes pipeline output to a specific format."""

    asset_type: str

    def __init__(self, unity_version: str = "2022.3", scale: float = 1.0) -> None:
        self.unity_version = unity_version
        self.scale = scale

    @abstractmethod
    def write(
        self,
        job_id: str,
        mesh: MeshResult,
        texture_path: Path,
        rigging: RiggingResult,
        output_dir: Path,
    ) -> AssetWriteResult:
        """Persist pipeline results to disk and return metadata about the asset."""

    def _unity_metadata(self, rigging: RiggingResult) -> Dict[str, str]:
        return {
            "unity_version": self.unity_version,
            "scale": self.scale,
            "default_controls": {key: str(value) for key, value in rigging.controls.items()},
        }
