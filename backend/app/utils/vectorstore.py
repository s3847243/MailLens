from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from pinecone import Pinecone
from tenacity import retry, stop_after_attempt, wait_exponential_jitter

from ..config import settings

_pc: Pinecone | None = None
_index = None


def _index_lazy():

    global _pc, _index
    if _index is not None:
        return _index
    if _pc is None:
        _pc = Pinecone(api_key=settings.PINECONE_API_KEY)
    _index = _pc.Index(settings.PINECONE_INDEX)
    return _index


@retry(stop=stop_after_attempt(3), wait=wait_exponential_jitter(min=1, max=6))
async def upsert_vectors(items: List[Dict[str, Any]], namespace: str) -> Dict[str, Any]:
    """items: [{id, values, metadata}]"""
    if not items:
        return {"upserted": 0}
    index = _index_lazy()
    # Run sync client in a thread so we don't block the event loop
    await asyncio.to_thread(index.upsert, vectors=items, namespace=namespace)
    return {"upserted": len(items)}


@retry(stop=stop_after_attempt(3), wait=wait_exponential_jitter(min=1, max=6))
async def delete_ids(ids: List[str], namespace: str):
    if not ids:
        return {"deleted": 0}
    index = _index_lazy()
    await asyncio.to_thread(index.delete, ids=ids, namespace=namespace)
    return {"deleted": len(ids)}


@retry(stop=stop_after_attempt(3), wait=wait_exponential_jitter(min=1, max=6))
async def query_top_k(namespace: str, vector: List[float], top_k: int = 8, filter: Optional[dict] = None):
    index = _index_lazy()
    res = await asyncio.to_thread(
        index.query,
        vector=vector,
        top_k=top_k,
        include_values=False,
        include_metadata=True,
        namespace=namespace,
        filter=filter or {},
    )
    # Normalize to a list of matches
    return res.matches or []


async def upsert_vectors(_items: List[Dict[str, Any]]):
    """M3: Replace with Pinecone upsert. Keep signature the same."""
    return {"upserted": len(_items)}
