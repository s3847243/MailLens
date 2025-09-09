import datetime
import json
import logging
from uuid import uuid4

import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openai import BaseModel
from sqlalchemy.orm import Session

from . import models
from .config import settings
from .db import get_db
from .routes import auth
from .routes import chat as chats_route
from .routes import email as email_route
from .routes import gmail as gmail_route
from .routes import health
from .routes import jobs as jobs_route
from .routes import me as me_route
from .routes import search as search_route
from .routes import sync as sync_route
from .utils.jwt import get_user_id_from_cookie
from .utils.security import decrypt, encrypt

# from pinecone import Pinecone

# logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
# logging.getLogger("httpx").setLevel(logging.WARNING)
# logging.getLogger("urllib3").setLevel(logging.WARNING)
# logging.getLogger("openai").setLevel(logging.WARNING)
# logging.getLogger("pinecone").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


app = FastAPI(title="MailLens API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.ALLOW_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api = APIRouter(prefix="/api")
api.include_router(health.router)
api.include_router(auth.router)
api.include_router(me_route.router)
api.include_router(gmail_route.router)
api.include_router(sync_route.router)
api.include_router(search_route.router)
api.include_router(chats_route.router)
api.include_router(jobs_route.router)
api.include_router(email_route.router)
app.include_router(api)


@api.get("/")
def root():

    return {"service": "maillens", "ok": True}


@api.get("/auth/debug/scopes")
async def debug_scopes(request: Request, db: Session = Depends(get_db)):
    from .utils.jwt import get_user_id_from_cookie
    uid = get_user_id_from_cookie(request)
    if not uid:
        raise HTTPException(status_code=401)
    acct = db.query(models.GmailAccount).filter(
        models.GmailAccount.user_id == uid).first()
    access = decrypt(acct.access_token)
    async with httpx.AsyncClient() as client:
        r = await client.get("https://www.googleapis.com/oauth2/v3/tokeninfo", params={"access_token": access})
        return r.json()


@api.get("/auth/debug/whoami")
def whoami(request: Request):
    uid = get_user_id_from_cookie(request)
    if not uid:
        raise HTTPException(
            status_code=401, detail="No/invalid session cookie")
    return {"user_id": uid}
