from __future__ import annotations

import os

from celery import Celery

broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
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
celery_app.autodiscover_tasks(["app.tasks"])  # looks for @shared_task

# at the bottom of celery_app.py
try:
    import app.tasks.beat_schedule  # noqa: F401
except Exception:
    # beat can still run without a schedule (e.g., env disables it)
    pass
