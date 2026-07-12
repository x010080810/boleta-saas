#!/bin/bash
set -e

nohup celery -A app.core.celery_app worker -l info > /tmp/celery_worker.log 2>&1 &

exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
