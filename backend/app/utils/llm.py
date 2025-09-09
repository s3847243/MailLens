from __future__ import annotations

import os
from typing import Any, AsyncGenerator, Dict, List

from openai import AsyncOpenAI

from ..config import settings

_client: AsyncOpenAI | None = None


def client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


DEFAULT_MODEL = settings.OPENAI_CHAT_MODEL if hasattr(
    settings, 'OPENAI_CHAT_MODEL') else 'gpt-4o-mini'


async def stream_chat(messages: List[Dict[str, str]], model: str | None = None) -> AsyncGenerator[str, None]:
    """Yield token deltas as strings."""
    model = model or DEFAULT_MODEL
    resp = await client().chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.2,
        stream=True,
    )
    async for chunk in resp:
        for choice in chunk.choices:
            delta = choice.delta.content
            if delta:
                yield delta
