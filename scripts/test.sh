#!/usr/bin/env bash
set -euo pipefail

# Web3 ships an optional pytest plugin that can break collection depending on
# dependency resolution. Keep tests deterministic by disabling auto-loaded
# third-party plugins and loading only pytest-asyncio explicitly.
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q -p pytest_asyncio.plugin "$@"
