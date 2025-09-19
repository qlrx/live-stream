"""Application settings and dependency configuration for the avatar pipeline."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict


def _bool(value: str) -> bool:
    return value.lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    """Container for configuration values loaded from the environment."""

    database_url: str = "sqlite:///./avatar_pipeline.db"
    celery_broker_url: str = "memory://"
    celery_backend_url: str = "memory://"
    model_base_path: Path = Path("./models")
    deca_model_path: Path = Path("./models/deca")
    gpu_enabled: bool = False
    temp_storage_path: Path = Path("./tmp/avatar_pipeline")
    output_path: Path = Path("./var/avatars")
    output_bucket_url: str = "file://./var/avatars"
    asset_base_url: str = "http://localhost:8000/assets"

    @classmethod
    def from_env(cls) -> "Settings":
        """Create settings by reading environment variables."""

        data: Dict[str, Any] = {}
        if database_url := os.getenv("AVATAR_PIPELINE_DATABASE_URL"):
            data["database_url"] = database_url
        if broker := os.getenv("AVATAR_PIPELINE_BROKER_URL"):
            data["celery_broker_url"] = broker
        if backend := os.getenv("AVATAR_PIPELINE_BACKEND_URL"):
            data["celery_backend_url"] = backend
        if model_base := os.getenv("AVATAR_PIPELINE_MODEL_PATH"):
            data["model_base_path"] = Path(model_base)
        if deca_path := os.getenv("AVATAR_PIPELINE_DECA_PATH"):
            data["deca_model_path"] = Path(deca_path)
        if gpu := os.getenv("AVATAR_PIPELINE_GPU_ENABLED"):
            data["gpu_enabled"] = _bool(gpu)
        if temp_storage := os.getenv("AVATAR_PIPELINE_TEMP_PATH"):
            data["temp_storage_path"] = Path(temp_storage)
        if output_path := os.getenv("AVATAR_PIPELINE_OUTPUT_PATH"):
            data["output_path"] = Path(output_path)
        if bucket := os.getenv("AVATAR_PIPELINE_OUTPUT_BUCKET"):
            data["output_bucket_url"] = bucket
        if asset_base := os.getenv("AVATAR_PIPELINE_ASSET_BASE_URL"):
            data["asset_base_url"] = asset_base
        return cls(**data)

    def ensure_directories(self) -> None:
        """Ensure directories referenced by the settings exist."""

        self.temp_storage_path.mkdir(parents=True, exist_ok=True)
        self.output_path.mkdir(parents=True, exist_ok=True)

    def to_dict(self) -> Dict[str, Any]:
        """Expose configuration as a dictionary for debugging and serialization."""

        return {
            "database_url": self.database_url,
            "celery_broker_url": self.celery_broker_url,
            "celery_backend_url": self.celery_backend_url,
            "model_base_path": str(self.model_base_path),
            "deca_model_path": str(self.deca_model_path),
            "gpu_enabled": self.gpu_enabled,
            "temp_storage_path": str(self.temp_storage_path),
            "output_path": str(self.output_path),
            "output_bucket_url": self.output_bucket_url,
            "asset_base_url": self.asset_base_url,
        }


def get_settings() -> Settings:
    """Access the default application settings."""

    return Settings.from_env()
