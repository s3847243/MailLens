from __future__ import annotations

import os

from celery import Celery

broker_url = os.getenv("CELERY_BROKER_URL"),
result_backend = os.getenv("CELERY_RESULT_BACKEND"),
timezone = os.getenv("CELERY_TIMEZONE", "Australia/Melbourne")
celery_app = Celery("maillens", broker=broker_url, backend=result_backend)
celery_app.conf.broker_transport_options = {
    "region": os.getenv("AWS_DEFAULT_REGION", "ap-southeast-2")
}
celery_app.conf.update(
    timezone=timezone,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    worker_hijack_root_logger=False,
)

# Autodiscover tasks in app.tasks package
celery_app.autodiscover_tasks(["app.tasks"])

try:
    import app.tasks.beat_schedule
    from app.tasks import sync_tasks
except Exception:
    pass
