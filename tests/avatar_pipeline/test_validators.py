import pytest

from services.avatar_pipeline.exceptions import ValidationError
from services.avatar_pipeline.validators.photo_validator import PhotoValidator


def test_photo_validator_accepts_valid_payload():
    validator = PhotoValidator()
    photos = [
        {
            "url": "https://example.com/photo.jpg",
            "width": 512,
            "height": 512,
        }
    ]
    validated = validator.validate(photos)
    assert len(validated) == 1
    assert validated[0].url == photos[0]["url"]


def test_photo_validator_rejects_missing_url():
    validator = PhotoValidator()
    with pytest.raises(ValidationError):
        validator.validate([{"width": 512, "height": 512}])


def test_photo_validator_rejects_low_resolution():
    validator = PhotoValidator()
    with pytest.raises(ValidationError):
        validator.validate(
            [
                {
                    "url": "https://example.com/photo.jpg",
                    "width": 64,
                    "height": 64,
                }
            ]
        )
