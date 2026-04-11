#!/usr/bin/env bash
set -euo pipefail

export ENV="${ENV:-dev}"
if [[ "${ENV}" != "dev" ]]; then
  echo "Refusing to run dev DB bootstrap when ENV=${ENV}." >&2
  exit 1
fi

if [[ -z "${DATABASE_URL:-}" ]]; then
  export DATABASE_URL="sqlite:///./neuralbot_omega.db"
fi

echo "[dev-db-init] Running migrations on ${DATABASE_URL}"
alembic upgrade 20260411_0001
alembic current
