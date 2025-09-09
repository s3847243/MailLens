# app/services/indexing.py
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from app.services.chunking import _plain_text, chunk_text_by_tokens
from app.utils.embeddings import embed_text

logger = logging.getLogger(__name__)


async def build_email_vectors_async(
    *,
    embed_text,
    message_id: str,
    gmail_account_id: str,
    subject: Optional[str],
    body_text: Optional[str],
    thread_id: Optional[str],
    date: Optional[datetime],
    label_ids: Optional[list[str]],
    doc_hash: Optional[str],
    max_tokens_per_chunk: int = 600,
    overlap: int = 80,
) -> List[Dict]:
    text = _plain_text(subject, body_text)
    if not text.strip():
        return []
    chunks = chunk_text_by_tokens(
        text, max_tokens=max_tokens_per_chunk, overlap=overlap)

    vectors: List[Dict] = []
    for idx, (chunk_text, start_tok, end_tok) in enumerate(chunks):
        logger.info("Chunk text %s :", chunk_text)
        vec = await embed_text(chunk_text)
        if vec is None:
            continue
        vectors.append({
            "id": f"{message_id}#{idx}",
            "values": vec,
            "metadata": {
                "type": "email_chunk",
                "message_id": message_id,
                "gmail_account_id": str(gmail_account_id),
                "thread_id": thread_id,
                "subject": subject or "",
                "date": (date.isoformat() if date else None),
                "label_ids": label_ids or [],
                "doc_hash": doc_hash or "",
                "chunk_index": idx,
                "start_tok": start_tok,
                "end_tok": end_tok,
            },
        })
    return vectors
