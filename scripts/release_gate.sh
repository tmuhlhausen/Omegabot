#!/usr/bin/env bash
set -euo pipefail

echo "[1/7] Running deterministic unit test gate..."
./scripts/test.sh

echo "[2/7] Verifying Python source compiles..."
python -m compileall -q src tests

echo "[3/7] Validating packaging metadata files..."
test -f requirements.txt
test -f requirements-dev.txt
test -f pytest.ini

echo "[4/7] Running dependency health check..."
python -m pip check > /dev/null

echo "[5/7] Enforcing deprecated import policy..."
python scripts/check_deprecated_imports.py

echo "[6/7] Enforcing release-critical implementation matrix..."
python scripts/check_implementation_matrix.py

echo "[7/7] Release gate complete ✅"
