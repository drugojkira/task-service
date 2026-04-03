#!/bin/sh
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting Task Service..."
exec python -m main

