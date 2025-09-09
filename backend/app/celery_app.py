from __future__ import annotations

import os

from celery import Celery

broker_url = "redis://localhost:6379/1"
result_backend = "redis://localhost:6379/2"
timezone = os.getenv("CELERY_TIMEZONE", "Australia/Melbourne")
celery_app = Celery("maillens", broker=broker_url, backend=result_backend)
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
