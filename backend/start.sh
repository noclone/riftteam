#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

docker compose up -d --wait

cd backend
uv run alembic upgrade head
exec uv run uvicorn app.main:app --reload
