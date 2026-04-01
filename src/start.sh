#!/bin/sh
set -e

alembic upgrade head
python -m main

#!/bin/bash
set -e

echo "Running database migrations..."
cd /app
alembic upgrade head

echo "Starting Task Service..."
python -m main



