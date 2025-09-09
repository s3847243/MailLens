from __future__ import annotations

import os
from typing import List, Optional

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential_jitter

from ..config import settings

_client: AsyncOpenAI | None = None


def _client_lazy() -> AsyncOpenAI:

    global _client
    if _client is None:
        if not settings.OPENAI_API_KEY:
            raise RuntimeError(
                "OPENAI_API_KEY not loaded from settings. Check .env")
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


MODEL = settings.EMBEDDING_MODEL or "text-embedding-3-large"


@retry(stop=stop_after_attempt(3), wait=wait_exponential_jitter(initial=1, max=6))
async def embed_text(text: str) -> Optional[List[float]]:
    """Embed a single text. Returns vector or None if input is empty."""
    text = (text or "").strip()
    if not text:
        return None
    client = _client_lazy()
    resp = await client.embeddings.create(model=MODEL, input=[text])
    vec = resp.data[0].embedding
    return vec


@retry(stop=stop_after_attempt(3), wait=wait_exponential_jitter(initial=1, max=6))
async def embed_batch(texts: List[str]) -> List[Optional[List[float]]]:
    """Embed a batch of texts; keeps order; returns list where items can be None for empty inputs."""
    if not texts:
        return []
    client = _client_lazy()
    inputs = [(t or "").strip() for t in texts]
    resp = await client.embeddings.create(model=MODEL, input=inputs)
    return [d.embedding if inputs[i] else None for i, d in enumerate(resp.data)]


def build_embedding_text(subject: str | None, body_text: str | None) -> str:
    s = (subject or "").strip()
    b = (body_text or "").strip()
    return f"{s}\n\n{b}".strip()
