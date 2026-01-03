#!/bin/bash
set -e

echo "Running data migration from DigitalOcean (one-time)..."
if [ -n "$DO_DATABASE_URL" ]; then
    python manage.py migrate_from_do --connection-string "$DO_DATABASE_URL" || echo "Data migration skipped or already completed"
else
    echo "DO_DATABASE_URL not set, skipping data migration"
fi

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Creating initial superuser if needed..."
python manage.py create_initial_superuser

echo "Starting gunicorn on port $PORT..."
exec gunicorn alphalpgas.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
