#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def write(rel_path: str, content: str) -> None:
    path = ROOT / rel_path
    path.write_text(content, encoding="utf-8")
    print(f"wrote {rel_path}")


def replace_once(rel_path: str, old: str, new: str) -> None:
    path = ROOT / rel_path
    body = path.read_text(encoding="utf-8")
    if old not in body:
        raise RuntimeError(f"pattern not found in {rel_path}: {old[:60]!r}")
    path.write_text(body.replace(old, new, 1), encoding="utf-8")
    print(f"patched {rel_path}")


def main() -> None:
    write(
        "src/core/engine_components/health/supervisor.py",
        '''from __future__ import annotations

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
        self._tasks: dict[str, asyncio.Task] = {}

    def supervise(self, name: str, coro_factory, policy: RestartPolicy) -> asyncio.Task:
        existing = self._tasks.get(name)
        if existing and not existing.done():
            return existing
        task = asyncio.create_task(self._runner(name, coro_factory, policy), name=f"supervisor:{name}")
        self._tasks[name] = task
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
            finally:
                task = self._tasks.get(name)
                if task and task.done():
                    self._tasks.pop(name, None)

    def stop(self, name: str) -> bool:
        task = self._tasks.get(name)
        if not task or task.done():
            self._tasks.pop(name, None)
            return False
        task.cancel()
        return True

    def is_running(self, name: str) -> bool:
        task = self._tasks.get(name)
        return bool(task and not task.done())

    async def wait(self) -> None:
        await asyncio.gather(*self._tasks.values(), return_exceptions=True)
''',
    )

    write(
        "src/core/engine_components/__init__.py",
        '''from .bootstrap import BootstrapComponent
from .market_loop import MarketLoopComponent
from .strategy_loop import StrategyLoopComponent
from .execution_loop import ExecutionLoopComponent
from .reporting_loop import ReportingLoopComponent
from .runtime import RuntimeComponent
from .telemetry import ErrorTelemetry

__all__ = [
    "BootstrapComponent",
    "MarketLoopComponent",
    "StrategyLoopComponent",
    "ExecutionLoopComponent",
    "ReportingLoopComponent",
    "RuntimeComponent",
    "ErrorTelemetry",
]
''',
    )

    write(
        "Dockerfile",
        '''FROM python:3.11-slim

RUN useradd --create-home appuser

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libssl-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt constraints-shared.txt ./
RUN pip install --no-cache-dir --break-system-packages -c constraints-shared.txt -r requirements.txt

COPY src/ src/
COPY backend/ backend/
COPY strategies/ strategies/
COPY migrations/ migrations/
COPY alembic.ini ./
COPY VERSION ./
COPY LICENSE ./

USER appuser

ENV PORT=8080
CMD exec python -m src.core.engine
''',
    )

    write(
        "contracts/hardhat.config.js",
        '''require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

const forking = process.env.ARBITRUM_RPC_URL
  ? {
      url: process.env.ARBITRUM_RPC_URL,
      enabled: true,
    }
  : undefined;

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: {
    version: "0.8.20",
    settings: {
      optimizer: { enabled: true, runs: 200 },
      viaIR: true,
    },
  },
  networks: {
    hardhat: {
      forking,
      chainId: 42161,
    },
    arbitrum: {
      url: process.env.ARBITRUM_RPC_URL || "https://arb1.arbitrum.io/rpc",
      accounts: process.env.DEPLOYER_PRIVATE_KEY ? [process.env.DEPLOYER_PRIVATE_KEY] : [],
      chainId: 42161,
    },
    arbitrum_sepolia: {
      url: "https://sepolia-rollup.arbitrum.io/rpc",
      accounts: process.env.DEPLOYER_PRIVATE_KEY ? [process.env.DEPLOYER_PRIVATE_KEY] : [],
      chainId: 421614,
    },
  },
  etherscan: {
    apiKey: { arbitrumOne: process.env.ARBISCAN_API_KEY || "" },
  },
};
''',
    )

    write(
        "contracts/package.json",
        '''{
  "name": "neuralbot-omega-contracts",
  "version": "1.0.0",
  "scripts": {
    "compile": "hardhat compile",
    "test": "hardhat test",
    "test:fork": "hardhat test test/executor.fork.js",
    "deploy:testnet": "hardhat run scripts/deploy.js --network arbitrum_sepolia",
    "deploy:mainnet": "hardhat run scripts/deploy.js --network arbitrum",
    "verify": "hardhat verify --network arbitrum"
  },
  "devDependencies": {
    "@nomicfoundation/hardhat-toolbox": "^4.0.0",
    "hardhat": "^2.19.4",
    "dotenv": "^16.4.1"
  },
  "dependencies": {
    "@aave/v3-core": "^1.19.3",
    "@openzeppelin/contracts": "^4.9.6",
    "@uniswap/v3-periphery": "^1.4.4"
  }
}
''',
    )

    replace_once(
        "src/core/engine.py",
        "from ..core.engine_components import (\n    BootstrapComponent,\n    MarketLoopComponent,\n    StrategyLoopComponent,\n    ExecutionLoopComponent,\n    ReportingLoopComponent,\n    ErrorTelemetry,\n)\n",
        "from ..core.engine_components import (\n    BootstrapComponent,\n    MarketLoopComponent,\n    StrategyLoopComponent,\n    ExecutionLoopComponent,\n    ReportingLoopComponent,\n    RuntimeComponent,\n    ErrorTelemetry,\n)\n",
    )

    replace_once(
        "src/core/engine.py",
        "        self.reporting_loop = ReportingLoopComponent(self)\n        self.supervisor = TaskSupervisor(self.error_telemetry)\n",
        "        self.reporting_loop = ReportingLoopComponent(self)\n        self.supervisor = TaskSupervisor(self.error_telemetry)\n        self.runtime = RuntimeComponent(self, self.supervisor)\n",
    )

    replace_once(
        "src/core/engine.py",
        "        log.info(\"engine.tasks.started\", count=len(tasks))\n        await asyncio.gather(*tasks, return_exceptions=True)\n",
        "        self.runtime.start()\n        log.info(\"engine.tasks.started\")\n        await self.runtime.wait()\n",
    )

    replace_once(
        "src/core/engine.py",
        "    async def _cmd_enable_strategy(self, data):\n        strategy = data.get(\"strategy\", \"\")\n        enabled = data.get(\"enabled\", True)\n        if enabled:\n            self._enabled.add(strategy)\n        else:\n            self._enabled.discard(strategy)\n        return f\"{strategy}={'enabled' if enabled else 'disabled'}\"\n",
        "    async def _cmd_enable_strategy(self, data):\n        strategy = data.get(\"strategy\", \"\")\n        enabled = data.get(\"enabled\", True)\n        if enabled:\n            await self.runtime.enable_strategy(strategy)\n        else:\n            self.runtime.disable_strategy(strategy)\n        return f\"{strategy}={'enabled' if enabled else 'disabled'}\"\n",
    )

    print(\"runtime/container patch applied\")


if __name__ == \"__main__\":
    main()
