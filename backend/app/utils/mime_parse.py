from __future__ import annotations

import base64
import re
from typing import Any, Dict, Tuple


def _b64url_decode(s: str) -> bytes:

    s = s or ""
    pad = (-len(s)) % 4
    if pad:
        s += "=" * pad
    return base64.urlsafe_b64decode(s)


_tag_re = re.compile(r"<[^>]+>")
_ws_re = re.compile(r"\s+")


def _strip_html(html: str) -> str:

    text = _tag_re.sub(" ", html)
    text = _ws_re.sub(" ", text)
    return text.strip()


def parse_message(gmsg: Dict[str, Any]) -> Tuple[Dict[str, str], str, str]:

    payload = gmsg.get("payload", {})
    headers_list = payload.get("headers", [])
    headers = {h.get("name", "").lower(): h.get("value", "")
               for h in headers_list}

    def walk(parts):
        if not parts:
            return None
        for p in parts:
            mime = (p.get("mimeType") or "").lower()
            body = p.get("body", {})
            data = body.get("data")
            if mime.startswith("text/plain") and data:
                raw = _b64url_decode(data)
                return (raw.decode(errors="ignore"), None)
            if mime.startswith("text/html") and data:
                raw = _b64url_decode(data)
                return (None, raw.decode(errors="ignore"))
            # nested multipart
            res = walk(p.get("parts"))
            if res:
                return res
        return None
    body_text = body_html = None

    if payload.get("body", {}).get("data"):
        mime = (payload.get("mimeType") or "").lower()
        raw = _b64url_decode(payload["body"]["data"]).decode(errors="ignore")
        if mime.startswith("text/plain"):
            body_text = raw
        elif mime.startswith("text/html"):
            body_html = raw
    else:
        res = walk(payload.get("parts"))
        if res:
            body_text, body_html = res

    if body_text is None and body_html:
        body_text = _strip_html(body_html)
    return headers, (body_text or ""), (body_html or "")
