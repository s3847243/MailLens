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


@retry(stop=stop_after_attempt(3), wait=wait_exponential_jitter(initial=1, max=6))
async def upsert_vectors(items: List[Dict[str, Any]], namespace: str) -> Dict[str, Any]:
    """items: [{id, values, metadata}]"""
    if not items:
        return {"upserted": 0}
    index = _index_lazy()
    await asyncio.to_thread(index.upsert, vectors=items, namespace=namespace)
    return {"upserted": len(items)}


@retry(stop=stop_after_attempt(3), wait=wait_exponential_jitter(initial=1, max=6))
async def delete_ids(ids: List[str], namespace: str):
    if not ids:
        return {"deleted": 0}
    index = _index_lazy()
    await asyncio.to_thread(index.delete, ids=ids, namespace=namespace)
    return {"deleted": len(ids)}


@retry(stop=stop_after_attempt(3), wait=wait_exponential_jitter(initial=1, max=6))
async def delete_by_filter(namespace: str, where: Optional[Dict[str, Any]] = None):
    """
    Delete vectors from Pinecone by filter.
    Example:
        await delete_by_filter(
            namespace="account-123",
            where={"message_id": {"$eq": "abc123"}}
        )
    """
    if not where:
        return {"deleted": 0}

    index = _index_lazy()
    await asyncio.to_thread(index.delete, namespace=namespace, filter=where)
    return {"deleted": "unknown"}  # Pinecone doesn’t return count here


@retry(stop=stop_after_attempt(3), wait=wait_exponential_jitter(initial=1, max=6))
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
    return res.matches or []


def _filter_matches(matches, min_abs: float | None = None, rel_drop: float = 0.05):
    """
    Keep only matches that are (a) above an absolute floor, and
    (b) close enough to the best score (within rel_drop).
    Works well for cosine scores in [0,1].
    """
    if not matches:
        return []

    matches = sorted(matches, key=lambda m: getattr(
        m, "score", 0.0), reverse=True)

    best = float(getattr(matches[0], "score", 0.0) or 0.0)

    # set sane defaults: absolute floor 0.25 unless caller overrides
    abs_floor = min_abs if min_abs is not None else 0.25
    rel_floor = best - rel_drop

    keep = []
    for m in matches:
        s = float(getattr(m, "score", 0.0) or 0.0)
        if s >= abs_floor and s >= rel_floor:
            keep.append(m)
    return keep


def _dedupe_by_thread(rows):
    seen = set()
    out = []
    for r in rows:
        tid = r.thread_id or r.message_id
        if tid in seen:
            continue
        seen.add(tid)
        out.append(r)
    return out
