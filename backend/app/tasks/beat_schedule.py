from __future__ import annotations

import os

from app.celery_app import celery_app
from celery.schedules import crontab

# use CELERY_SCHEDULE_MINUTES (default 15) to run every N minutes
N = int(os.getenv("CELERY_SCHEDULE_MINUTES", "15"))


celery_app.conf.beat_schedule = {
    "incremental-sync-every-n-min": {
        "task": "schedule_incremental_for_all",
        "schedule": crontab(minute=f"*/{N}"),
    },
}
