#!/usr/bin/env bash
set -euo pipefail

echo "[1/5] Running deterministic unit test gate..."
./scripts/test.sh

echo "[2/5] Verifying Python source compiles..."
python -m compileall -q src tests

echo "[3/5] Validating packaging metadata files..."
test -f requirements.txt
test -f requirements-dev.txt
test -f pytest.ini

echo "[4/5] Running dependency health check..."
python -m pip check > /dev/null

echo "[5/6] Enforcing deprecated import policy..."
python scripts/check_deprecated_imports.py

echo "[6/6] Release gate complete ✅"
