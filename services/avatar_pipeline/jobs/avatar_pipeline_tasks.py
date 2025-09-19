"""Asynchronous task definitions for the avatar pipeline."""

from __future__ import annotations

import logging
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from services.avatar_pipeline import build_default_service
from services.avatar_pipeline.config.settings import Settings, get_settings
from services.avatar_pipeline.service import AvatarPipelineService

logger = logging.getLogger(__name__)


@dataclass
class TaskHandle:
    """Represents a scheduled task and exposes helper utilities."""

    job_id: Optional[str]
    future: Future

    def result(self, timeout: Optional[float] = None) -> Any:
        return self.future.result(timeout)

    def successful(self) -> bool:
        return self.future.done() and self.future.exception() is None

    def ready(self) -> bool:
        return self.future.done()


class TaskQueue:
    """A minimal asynchronous execution queue used in place of Celery."""

    def __init__(self, max_workers: int = 4) -> None:
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._tasks: Dict[str, Callable[..., Any]] = {}
        self._inflight: Dict[str, Future] = {}
        self._lock = threading.Lock()

    def task(self, name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self._tasks[name] = func

            def apply_async(*args: Any, **kwargs: Any) -> TaskHandle:
                job_id = kwargs.get("job_id") or (args[0] if args else None)
                future = self._executor.submit(self._execute, func, job_id, args, kwargs)
                if job_id:
                    with self._lock:
                        self._inflight[job_id] = future
                return TaskHandle(job_id=job_id, future=future)

            func.delay = apply_async  # type: ignore[attr-defined]
            func.apply_async = apply_async  # type: ignore[attr-defined]
            return func

        return decorator

    def _execute(
        self,
        func: Callable[..., Any],
        job_id: Optional[str],
        args: Any,
        kwargs: Dict[str, Any],
    ) -> Any:
        try:
            return func(*args, **kwargs)
        finally:
            if job_id:
                with self._lock:
                    self._inflight.pop(job_id, None)

    def status(self, job_id: str) -> str:
        with self._lock:
            future = self._inflight.get(job_id)
        if future is None:
            return "IDLE"
        if future.running():
            return "RUNNING"
        if future.done():
            return "SUCCESS" if future.exception() is None else "FAILURE"
        return "PENDING"


task_queue = TaskQueue()


def build_pipeline_service(settings: Optional[Settings] = None) -> AvatarPipelineService:
    settings = settings or get_settings()
    return build_default_service(settings=settings)


@task_queue.task("avatar_pipeline.run")
def run_avatar_pipeline(job_id: str, settings: Optional[Settings] = None) -> Dict[str, Any]:
    """Execute the full avatar pipeline for the provided job."""

    settings = settings or get_settings()
    service = build_pipeline_service(settings=settings)
    try:
        context = service.run(job_id)
        return context.assets
    except Exception:
        logger.exception("Avatar pipeline failed for job %s", job_id)
        raise


def submit_avatar_job(job_id: str, settings: Optional[Settings] = None) -> TaskHandle:
    """Queue a new avatar generation job for asynchronous processing."""

    return run_avatar_pipeline.delay(job_id=job_id, settings=settings)
