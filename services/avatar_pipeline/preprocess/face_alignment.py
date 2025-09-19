"""Simple face alignment preprocessor used for tests and orchestration wiring."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Iterable, List, Optional

from services.avatar_pipeline.models.pipeline import AlignedImage, Photo


class FaceAlignmentPreprocessor:
    """Align faces and produce landmark files for downstream stages."""

    def align(self, photos: Iterable[Photo], working_dir: Optional[Path]) -> List[AlignedImage]:
        photos = list(photos)
        if working_dir is None:
            raise ValueError("working_dir must be provided for face alignment output.")
        alignment_dir = working_dir / "alignment"
        alignment_dir.mkdir(parents=True, exist_ok=True)

        aligned: List[AlignedImage] = []
        for index, photo in enumerate(photos):
            aligned_path = alignment_dir / f"aligned_{index}.png"
            aligned_path.write_text(f"aligned image placeholder for {photo.url}\n")
            landmarks_path = alignment_dir / f"aligned_{index}_landmarks.json"
            landmarks = {"photo_url": photo.url, "landmarks": [0, 0, 1, 1], "id": uuid.uuid4().hex}
            landmarks_path.write_text(json.dumps(landmarks))
            aligned.append(
                AlignedImage(
                    source_photo=photo,
                    aligned_path=aligned_path,
                    landmarks_path=landmarks_path,
                )
            )
        return aligned
