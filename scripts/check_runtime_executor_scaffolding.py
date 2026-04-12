#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "src/core/engine_components/runtime.py",
    "src/strategies/executor_calldata.py",
    "tests/test_engine_runtime.py",
    "tests/test_executor_calldata.py",
    "contracts/test/executor.fork.js",
    "docs/ROADMAP_RUNTIME_EXECUTOR_HARDENING.md",
    "scripts/apply_runtime_patch.py",
    "scripts/apply_executor_patch.py",
]


def assert_exists(rel_path: str) -> None:
    path = ROOT / rel_path
    if not path.exists():
        raise SystemExit(f"missing required file: {rel_path}")


def assert_contains(rel_path: str, needle: str) -> None:
    body = (ROOT / rel_path).read_text(encoding="utf-8")
    if needle not in body:
        raise SystemExit(f"missing expected content in {rel_path}: {needle}")


def main() -> None:
    for rel_path in REQUIRED_FILES:
        assert_exists(rel_path)

    assert_contains("src/strategies/executor_calldata.py", "def encode_arb_calldata")
    assert_contains("src/strategies/executor_calldata.py", "def encode_liquidation_calldata")
    assert_contains("tests/test_executor_calldata.py", "test_encode_arb_calldata_round_trips_expected_fields")
    assert_contains("tests/test_engine_runtime.py", "test_runtime_enable_disable_strategy_starts_and_stops_named_task")
    assert_contains("contracts/test/executor.fork.js", "AaveBotExecutor fork integration")
    assert_contains("docs/ROADMAP_RUNTIME_EXECUTOR_HARDENING.md", "Phase 6")

    print("runtime/executor scaffolding checks passed")


if __name__ == "__main__":
    main()
