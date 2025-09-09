from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class HealthOut(BaseModel):
    status: str


class ChatMessageOut(BaseModel):
    id: str
    role: str
    content: str
    tokens: int | None = None
    citations: Any | None = None
    created_at: datetime


class EmailDetail(BaseModel):
    id: str
    gmail_account_id: str
    message_id: str
    thread_id: Optional[str] = None
    subject: Optional[str] = None
    from_addr: Optional[str] = None
    to_addr: Optional[str] = None
    cc: Optional[str] = None
    bcc: Optional[str] = None
    date: Optional[str] = None
    snippet: Optional[str] = None
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    headers_json: Optional[Dict[str, str]] = None
    label_ids: Optional[List[str]] = None
    gmail_web_url: Optional[str] = None

    class Config:
        from_attributes = True
