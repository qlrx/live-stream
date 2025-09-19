"""Input validation for avatar source photos."""

from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Iterable, List, Mapping
from urllib.parse import urlparse

from services.avatar_pipeline.exceptions import ValidationError
from services.avatar_pipeline.models.pipeline import Photo


class PhotoValidator:
    """Ensures inbound photos satisfy minimum quality thresholds."""

    allowed_extensions = {".jpg", ".jpeg", ".png"}
    min_resolution = 256

    def validate(self, photos: Iterable[Mapping]) -> List[Photo]:
        photos = list(photos)
        if not photos:
            raise ValidationError("At least one photo is required to generate an avatar.")

        validated: List[Photo] = []
        for index, payload in enumerate(photos):
            url = str(payload.get("url", "")).strip()
            if not url:
                raise ValidationError(f"Photo #{index + 1} is missing a URL.")

            extension = Path(urlparse(url).path).suffix.lower()
            guessed_type = mimetypes.guess_type(url)[0]
            if extension not in self.allowed_extensions and (guessed_type or "").split("/")[0] != "image":
                raise ValidationError(f"Unsupported image format for {url}.")

            width = int(payload.get("width", 0))
            height = int(payload.get("height", 0))
            if width < self.min_resolution or height < self.min_resolution:
                raise ValidationError(
                    f"Photo {url} is below the minimum resolution of {self.min_resolution}px."
                )

            metadata = {
                key: str(value)
                for key, value in payload.get("metadata", {}).items()
            }
            validated.append(Photo(url=url, width=width, height=height, metadata=metadata))
        return validated
