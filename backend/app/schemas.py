from datetime import datetime
from typing import Any

from pydantic import BaseModel


class HealthOut(BaseModel):
    status: str


class ChatMessageOut(BaseModel):
    id: str
    role: str
    content: str
    tokens: int | None = None
    citations: Any | None = None
    created_at: datetime
