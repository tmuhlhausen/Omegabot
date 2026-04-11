from __future__ import annotations

import asyncio
from dataclasses import dataclass


@dataclass
class RestartPolicy:
    max_restarts: int
    backoff_seconds: float
    failure_budget: int


class TaskSupervisor:
    """Supervises loop tasks with restart policies and failure budgets."""

    def __init__(self, telemetry):
        self.telemetry = telemetry
        self._tasks: list[asyncio.Task] = []

    def supervise(self, name: str, coro_factory, policy: RestartPolicy) -> asyncio.Task:
        task = asyncio.create_task(self._runner(name, coro_factory, policy), name=f"supervisor:{name}")
        self._tasks.append(task)
        return task

    async def _runner(self, name: str, coro_factory, policy: RestartPolicy) -> None:
        restarts = 0
        failures = 0
        while True:
            try:
                await coro_factory()
                return
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                failures += 1
                self.telemetry.record(name, exc)
                if failures > policy.failure_budget or restarts >= policy.max_restarts:
                    raise
                restarts += 1
                await asyncio.sleep(policy.backoff_seconds)

    async def wait(self) -> None:
        await asyncio.gather(*self._tasks, return_exceptions=True)
