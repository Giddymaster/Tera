#!/bin/sh
# Apply database migrations, then start the API.
set -e

echo "Applying database migrations..."
alembic upgrade head

echo "Starting API (workers=${WEB_CONCURRENCY:-1})..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers "${WEB_CONCURRENCY:-1}"
