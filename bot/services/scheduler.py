"""Async background scheduler utilities."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable


LOGGER = logging.getLogger(__name__)


class AsyncScheduler:
    """Run an async callable at fixed intervals without blocking."""

    def __init__(self, interval_seconds: int, task_callable: Callable[[], Awaitable[None]]) -> None:
        """Initialize scheduler with interval and async task callable."""
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be greater than 0")

        self.interval_seconds = interval_seconds
        self.task_callable = task_callable
        self._stop_event = asyncio.Event()
        self._runner_task: asyncio.Task[None] | None = None

    async def _run_loop(self) -> None:
        """Internal scheduler loop using monotonic time to minimize drift."""
        next_run = time.monotonic()

        while not self._stop_event.is_set():
            try:
                await self.task_callable()
            except Exception as exc:  # noqa: BLE001
                LOGGER.exception("Scheduled task failed: %s", exc)

            next_run += self.interval_seconds
            sleep_for = max(0.0, next_run - time.monotonic())

            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=sleep_for)
            except asyncio.TimeoutError:
                continue

    async def start(self) -> None:
        """Start the scheduler loop if it is not already running."""
        if self._runner_task is not None and not self._runner_task.done():
            LOGGER.info("Scheduler already running")
            return

        self._stop_event.clear()
        self._runner_task = asyncio.create_task(self._run_loop())
        LOGGER.info("Scheduler started with interval=%s seconds", self.interval_seconds)

    async def stop(self) -> None:
        """Signal the scheduler to stop and await background task shutdown."""
        self._stop_event.set()

        if self._runner_task is None:
            return

        try:
            await self._runner_task
        finally:
            self._runner_task = None

        LOGGER.info("Scheduler stopped")
