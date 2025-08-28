from .routes import jobs as jobs_route
import datetime
import json
import logging
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openai import BaseModel

from .config import settings
from .routes import auth
from .routes import chat as chats_route
from .routes import gmail as gmail_route
from .routes import health
from .routes import me as me_route
from .routes import search as search_route
from .routes import sync as sync_route

# from pinecone import Pinecone


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
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


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(me_route.router)
app.include_router(gmail_route.router)
app.include_router(sync_route.router)
app.include_router(search_route.router)
app.include_router(chats_route.router)


@app.get("/")
def root():

    return {"service": "maillens", "ok": True}


# ...
app.include_router(jobs_route.router)
