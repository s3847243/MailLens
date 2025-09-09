from fastapi import (APIRouter, Depends, HTTPException, Request, Response,
                     status)
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from .. import models
from ..config import settings
from ..db import get_db
from ..utils import google_oauth
from ..utils.jwt import (clear_session_cookie, get_user_id_from_cookie,
                         issue_session_cookie)
from ..utils.security import encrypt, new_state

router = APIRouter(prefix="/auth", tags=["auth"])


STATE_STORE: dict[str, bool] = {}


@router.get("/google/login")
async def google_login():
    state = new_state()
    STATE_STORE[state] = True
    url = google_oauth.build_auth_url(state)
    return {"auth_url": url}


@router.get("/google/callback")
async def google_callback(code: str | None = None, state: str | None = None, request: Request = None, response: Response = None, db: Session = Depends(get_db)):
    if not code or not state or state not in STATE_STORE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid state or code")
        STATE_STORE.pop(state, None)

    access_token, refresh_token, expiry, raw = await google_oauth.exchange_code_for_tokens(code)
    userinfo = await google_oauth.fetch_userinfo(access_token)

    google_user_id = userinfo.get("sub")
    email = userinfo.get("email")
    name = userinfo.get("name")
    picture = userinfo.get("picture")

    # upsert User
    user = db.query(models.User).filter(
        models.User.email == email).one_or_none()
    if not user:
        user = models.User(email=email, name=name, picture_url=picture)
        db.add(user)
        db.flush()
    else:
        user.name = name or user.name
        user.picture_url = picture or user.picture_url

    # upsert GmailAccount
    acct = (
        db.query(models.GmailAccount)
        .filter(models.GmailAccount.user_id == user.id, models.GmailAccount.google_user_id == google_user_id)
        .one_or_none()
    )

    enc_access = encrypt(access_token)
    enc_refresh = encrypt(refresh_token) if refresh_token else None

    if not acct:
        acct = models.GmailAccount(
            user_id=user.id,
            google_user_id=google_user_id,
            email=email,
            access_token=enc_access,
            refresh_token=enc_refresh,
            expiry=expiry,
            token_scope=settings.GOOGLE_OAUTH_SCOPES,
        )
        db.add(acct)
    else:
        acct.email = email
        acct.access_token = enc_access
        if enc_refresh:
            acct.refresh_token = enc_refresh
            acct.expiry = expiry
            acct.token_scope = settings.GOOGLE_OAUTH_SCOPES

    db.commit()

    redirect = RedirectResponse(
        url=f"{settings.APP_BASE_URL}/auth/callback?ok=1",
        status_code=302
    )
    issue_session_cookie(redirect, str(user.id))
    return redirect


@router.post("/logout")
async def logout(response: Response):
    clear_session_cookie(response)
    return {"ok": True}


@router.delete("/delete")
async def delete_account(request: Request, response: Response, db: Session = Depends(get_db)):
    uid = get_user_id_from_cookie(request)
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    user = db.query(models.User).filter(models.User.id == uid).one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()

    clear_session_cookie(response)
    return {"ok": True, "message": "Account deleted"}
