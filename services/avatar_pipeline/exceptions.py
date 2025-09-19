"""Custom exceptions for the avatar pipeline service."""

from dataclasses import dataclass
from typing import Optional


class AvatarPipelineError(Exception):
    """Base class for exceptions raised by the avatar pipeline."""


class ValidationError(AvatarPipelineError):
    """Raised when user supplied input fails validation."""


class StageExecutionError(AvatarPipelineError):
    """Raised when a specific pipeline stage fails."""


@dataclass
class ErrorDetail:
    """Structured error information returned to clients."""

    message: str
    stage: Optional[str] = None
    retryable: bool = False
