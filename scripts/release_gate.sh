#!/usr/bin/env bash
set -euo pipefail

echo "[1/6] Running deterministic unit test gate..."
./scripts/test.sh

echo "[2/6] Verifying Python source compiles..."
python -m compileall -q src tests

echo "[3/6] Validating packaging metadata files..."
test -f requirements.txt
test -f requirements-dev.txt
test -f pytest.ini

echo "[4/6] Running dependency health check..."
python -m pip check > /dev/null

echo "[5/6] Enforcing implementation matrix release-critical rules..."
python scripts/check_implementation_matrix.py

echo "[6/6] Release gate complete ✅"
