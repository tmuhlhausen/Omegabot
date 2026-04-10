#!/usr/bin/env bash
set -euo pipefail

echo "[1/4] Running deterministic unit test gate..."
./scripts/test.sh

echo "[2/4] Verifying Python source compiles..."
python -m compileall -q src tests

echo "[3/4] Validating packaging metadata files..."
test -f requirements.txt
test -f requirements-dev.txt
test -f pytest.ini

echo "[4/4] Release gate complete ✅"
