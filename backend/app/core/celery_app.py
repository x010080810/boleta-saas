import ssl
from celery import Celery
from app.core.config import settings

_ssl_config = {"ssl_cert_reqs": ssl.CERT_NONE} if settings.REDIS_URL.startswith("rediss://") else {}

celery_app = Celery(
    "boleta_saas",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    broker_use_ssl=_ssl_config,
    redis_backend_use_ssl=_ssl_config,
    include=[
        "app.services.email_sender",
        "app.services.pdf_generator",
        "app.tasks.scheduled",
        "app.tasks.payroll",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Lima",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

celery_app.conf.beat_schedule = {
    "check-expiring-licenses-daily": {
        "task": "app.tasks.scheduled.check_expiring_licenses",
        "schedule": 86400.0,
    },
    "update-license-states-daily": {
        "task": "app.tasks.scheduled.update_license_states",
        "schedule": 86400.0,
    },
    "backup-database-daily": {
        "task": "app.tasks.scheduled.backup_database",
        "schedule": 86400.0,
    },
}
