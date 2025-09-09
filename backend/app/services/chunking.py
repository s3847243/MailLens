# app/services/chunking.py
from typing import Dict, List, Optional, Tuple


def _safe(s: Optional[str]) -> str:
    return s or ""


def _plain_text(subject: Optional[str], body_text: Optional[str]) -> str:
    subj = _safe(subject).strip()
    body = _safe(body_text).strip()
    if subj:
        return f"Subject: {subj}\n\n{body}"
    return body


def chunk_text_by_tokens(
    text: str,
    *,
    max_tokens: int = 600,
    overlap: int = 80,
    encoder_name: str = "cl100k_base",
) -> List[Tuple[str, int, int]]:
    """
    Returns list of (chunk_text, start_token_idx, end_token_idx)
    """
    try:
        import tiktoken
        enc = tiktoken.get_encoding(encoder_name)
        toks = enc.encode(text)
        chunks: List[Tuple[str, int, int]] = []
        i = 0
        while i < len(toks):
            j = min(i + max_tokens, len(toks))
            sub = toks[i:j]
            chunk = enc.decode(sub)
            chunks.append((chunk, i, j))
            if j == len(toks):
                break
            i = max(0, j - overlap)
        return chunks
    except Exception:
        max_chars = max_tokens * 4
        ov_chars = overlap * 4
        chunks: List[Tuple[str, int, int]] = []
        i = 0
        n = len(text)
        while i < n:
            j = min(i + max_chars, n)
            chunk = text[i:j]
            chunks.append((chunk, i, j))
            if j == n:
                break
            i = max(0, j - ov_chars)
        return chunks
