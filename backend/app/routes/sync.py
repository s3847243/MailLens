from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .. import models
from ..db import SessionLocal, get_db
from ..services.sync_service import SyncService
from ..utils.jwt import get_user_id_from_cookie

router = APIRouter(prefix="/sync", tags=["sync"])


async def _run_initial(acct_id: str):
    db = SessionLocal()
    try:
        acct = db.query(models.GmailAccount).filter(
            models.GmailAccount.id == acct_id).one_or_none()
        if not acct:
            return
        svc = SyncService(db, acct)
        await svc.initial_sync()
    finally:
        db.close()


@router.post("/initial")
async def start_initial_sync(background: BackgroundTasks, request: Request, db: Session = Depends(get_db)):
    uid = get_user_id_from_cookie(request)
    if not uid:
        raise HTTPException(status_code=401, detail="Not authenticated")
    acct = db.query(models.GmailAccount).filter(
        models.GmailAccount.user_id == uid).first()
    if not acct:
        raise HTTPException(status_code=400, detail="No linked Gmail account")

    background.add_task(_run_initial, str(acct.id))
    return {"ok": True}


@router.get("/status")
async def sync_status(request: Request, db: Session = Depends(get_db)):
    uid = get_user_id_from_cookie(request)
    if not uid:
        raise HTTPException(status_code=401, detail="Not authenticated")
    acct = db.query(models.GmailAccount).filter(
        models.GmailAccount.user_id == uid).first()
    if not acct:
        raise HTTPException(status_code=400, detail="No linked Gmail account")

    from ..services.sync_service import SyncService
    prog = SyncService.get_progress(str(acct.id))
    count = db.query(models.EmailMessage).filter(
        models.EmailMessage.gmail_account_id == acct.id).count()
    prog["db_emails"] = count
    prog["history_id"] = acct.history_id
    return prog


@router.post("/incremental")
async def run_incremental(background: BackgroundTasks, request: Request, db: Session = Depends(get_db)):
    uid = get_user_id_from_cookie(request)
    if not uid:
        raise HTTPException(status_code=401, detail="Not authenticated")
    acct = db.query(models.GmailAccount).filter(
        models.GmailAccount.user_id == uid).first()
    if not acct:
        raise HTTPException(
            status_code=400, detail="No linked Gmail account")

    async def _task(acct_id: str):
        from .. import models as M
        from ..db import SessionLocal
        local = SessionLocal()
        try:
            a = local.query(M.GmailAccount).filter(
                M.GmailAccount.id == acct_id).one_or_none()
            if not a:
                return
            svc = SyncService(local, a)
            await svc.incremental_sync()
        finally:
            local.close()

        background.add_task(_task, str(acct.id))
        return {"ok": True}
