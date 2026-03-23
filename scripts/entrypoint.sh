#!/usr/bin/env sh
set -e

export DATABASE_URL="${DATABASE_URL:-postgresql+psycopg://app:app@db:5432/app}"

alembic upgrade head
python -m scripts.seed

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
