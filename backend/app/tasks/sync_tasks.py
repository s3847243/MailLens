from __future__ import annotations

import asyncio
import os

from celery import shared_task
from sqlalchemy.orm import Session

from .. import models
from ..db import SessionLocal
from ..services.sync_service import SyncService


@shared_task(name="incremental_sync_account")
def incremental_sync_account(acct_id: str):
    """Run incremental sync for a single Gmail account."""
    db: Session = SessionLocal()
    try:
        acct = db.query(models.GmailAccount).filter(
            models.GmailAccount.id == acct_id).one_or_none()
        if not acct:
            return {"ok": False, "error": "account_not_found"}
        svc = SyncService(db, acct)
        asyncio.run(svc.incremental_sync())
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        db.close()


@shared_task(name="schedule_incremental_for_all")
def schedule_incremental_for_all():
    """Enqueue per-account incremental syncs.
    This is idempotent and safe to run periodically.
    """

    db: Session = SessionLocal()
    try:
        acct_ids = [str(r.id) for r in db.query(models.GmailAccount.id).all()]
    finally:
        db.close()

    for aid in acct_ids:
        incremental_sync_account.delay(aid)
    return {"queued": len(acct_ids)}
