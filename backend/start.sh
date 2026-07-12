#!/bin/bash
# Start API
uvicorn app.main:app --host 0.0.0.0 --port $PORT &

# Start Celery worker
celery -A app.core.celery_app worker -l info &

# Start Celery beat
celery -A app.core.celery_app beat -l info &

# Wait for all background processes
wait
