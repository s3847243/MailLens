from __future__ import annotations

from app.celery_app import celery_app
from app.tasks.sync_tasks import (incremental_sync_account,
                                  schedule_incremental_for_all)
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .. import models
from ..db import get_db
from ..utils.jwt import get_user_id_from_cookie

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/incremental")
async def kickoff_incremental(request: Request, db: Session = Depends(get_db)):
    uid = get_user_id_from_cookie(request)
    if not uid:
        raise HTTPException(status_code=401, detail="Not authenticated")
    acct = db.query(models.GmailAccount).filter(
        models.GmailAccount.user_id == uid).first()
    if not acct:
        raise HTTPException(status_code=400, detail="No linked Gmail account")
    # incremental_sync_account.delay(str(acct.id))
    celery_app.send_task(
        'app.tasks.sync_tasks.incremental_sync_account', args=[str(acct.id)])

    return {"ok": True}


@router.post("/incremental/all")
async def kickoff_all():
    # schedule_incremental_for_all.delay()
    celery_app.send_task('app.tasks.sync_tasks.schedule_incremental_for_all')
    return {"ok": True}
