from __future__ import annotations

import datetime
import hashlib
import logging
import traceback
from typing import Any, Dict

from googleapiclient.errors import HttpError
from httpx import HTTPStatusError
from sqlalchemy.orm import Session

from .. import models
from ..services.indexing import build_email_vectors_async
from ..utils.embeddings import embed_text
from ..utils.gmail_client import GmailClient
from ..utils.mime_parse import parse_message
from ..utils.vectorstore import delete_by_filter, delete_ids, upsert_vectors

logger = logging.getLogger(__name__)


SYNC_PROGRESS: dict[str, Dict[str, Any]] = {}


class SyncService:
    def __init__(self, db: Session, acct: models.GmailAccount):
        self.db = db
        self.acct = acct
        self.client = GmailClient(db, acct)

    def _update_progress(self, **kwargs):
        pid = str(self.acct.id)
        curr = SYNC_PROGRESS.get(
            pid, {"state": "idle", "total": 0, "processed": 0, "indexed": 0, "errors": 0})
        curr.update(kwargs)
        SYNC_PROGRESS[pid] = curr

    async def initial_sync(self, q: str | None = None):
        # 1) gather all message IDs (for a progress total)
        self._update_progress(state="listing", total=0,
                              processed=0, indexed=0, errors=0)

        ids: list[str] = []
        async for mid in self.client.list_message_ids(q=q):
            ids.append(mid)
        total = len(ids)
        self._update_progress(state="syncing", total=total)

        for i, mid in enumerate(ids, start=1):
            try:

                exist = (
                    self.db.query(models.EmailMessage)
                    .filter(models.EmailMessage.message_id == mid)
                    .one_or_none()
                )
                if exist:
                    self._update_progress(processed=i)
                    continue

                gmsg = await self.client.get_message_full(mid)
                headers_map, body_text, body_html = parse_message(gmsg)
                subject = headers_map.get("subject")
                from_addr = headers_map.get("from")
                to_addr = headers_map.get("to")
                cc = headers_map.get("cc")
                bcc = headers_map.get("bcc")
                date_hdr = headers_map.get("date")
                snippet = gmsg.get("snippet")
                thread_id = gmsg.get("threadId")
                label_ids = gmsg.get("labelIds", [])
                size_estimate = gmsg.get("sizeEstimate")
                date = None
                if date_hdr:
                    try:
                        from email.utils import parsedate_to_datetime

                        date = parsedate_to_datetime(date_hdr)
                    except Exception:
                        pass

                h = hashlib.sha256()
                h.update(((subject or "") + "|" + (from_addr or "") + "|" +
                         (body_text or "")).encode("utf-8", errors="ignore"))
                doc_hash = h.hexdigest()[:64]

                import datetime
                row = models.EmailMessage(
                    gmail_account_id=self.acct.id,
                    message_id=mid,
                    thread_id=thread_id,
                    subject=subject,
                    from_addr=from_addr,
                    to_addr=to_addr,
                    cc=cc,
                    bcc=bcc,
                    date=date,
                    snippet=snippet,
                    headers_json=headers_map,
                    body_text=body_text or "",
                    body_html=body_html or "",
                    size_estimate=int(
                        size_estimate) if size_estimate is not None else None,
                    label_ids=list(label_ids) if label_ids else [],
                    hash_dedup=doc_hash,
                    indexed_at=None,
                    created_at=datetime.datetime.now(
                        datetime.timezone.utc),
                )
                self.db.add(row)
                self.db.commit()
                self.db.flush()
                vectors = await build_email_vectors_async(
                    embed_text=embed_text,
                    message_id=mid,
                    gmail_account_id=str(self.acct.id),
                    subject=subject,
                    body_text=body_text,
                    thread_id=thread_id,
                    date=date,
                    label_ids=label_ids,
                    doc_hash=doc_hash,
                    # max_tokens_per_chunk=600,
                    # overlap=80,
                )

                if vectors:
                    await upsert_vectors(vectors, namespace=str(self.acct.id))
                    import datetime
                    row.indexed_at = datetime.datetime.now(
                        datetime.timezone.utc)
                    self.db.add(row)
                    self.db.commit()
                self._update_progress(processed=i)
            except Exception as e:
                print("EXCEPTION constructing/inserting EmailMessage:", repr(e))
                print("TRACEBACK:\n", traceback.format_exc())
                print(
                    "TYPES:",
                    "mid", type(mid),
                    "thread_id", type(thread_id),
                    "subject", type(subject),
                    "from_addr", type(from_addr),
                    "to_addr", type(to_addr),
                    "cc", type(cc),
                    "bcc", type(bcc),
                    "date", type(date),
                    "snippet", type(snippet),
                    "headers_map", type(
                        headers_map) if 'headers_map' in locals() else 'MISSING',
                    "body_text", type(body_text),
                    "body_html", type(body_html),
                    "size_estimate", type(
                        size_estimate) if 'size_estimate' in locals() else 'MISSING',
                    "label_ids", type(
                        label_ids) if 'label_ids' in locals() else 'MISSING',
                    "doc_hash", type(doc_hash),
                )
                prev_err = 0
                try:
                    prev_err = self.SYNC_PROGRESS[str(self.acct.id)]["errors"]
                except Exception:
                    pass
                self._update_progress(processed=i, errors=prev_err + 1)
        try:
            prof = await self.client.get_profile()
            hid = prof.get("historyId")
            if hid:
                self.acct.history_id = str(hid)
                self.db.add(self.acct)
                self.db.commit()
        except Exception:
            pass

        self._update_progress(state="done")

    @staticmethod
    def get_progress(acct_id: str) -> Dict[str, Any]:
        return SYNC_PROGRESS.get(acct_id, {"state": "idle", "total": 0, "processed": 0, "indexed": 0, "errors": 0})

    async def incremental_sync(self):
        """Fetch changes since last stored history_id and apply them."""
        logger.info("Reached incremental_sync")
        start_id = self.acct.history_id
        if not start_id:
            logger.info("Reached start")

            await self.initial_sync()

            prof = await self.client.get_profile()
            self.acct.history_id = str(prof.get("historyId"))
            self.db.add(self.acct)
            self.db.commit()
            self._update_progress(state="idle")
            return
        logger.info("Reached update porgres")
        self._update_progress(state="incremental", total=0)

        def _now():
            return datetime.now(timezone.utc)

        latest_seen_int = int(start_id)
        page_token = None
        processed = 0
        errors = 0
        saw_any_history = False

        while True:

            logger.info("Reached while loop")
            try:
                logger.info("Reached histroy")
                data = await self.client.get_history(start_history_id=str(start_id), page_token=page_token)
                logger.info("get_history OK. has_history=%s nextPage=%s",
                            bool(data.get("history")), data.get("nextPageToken"))

            except HTTPStatusError as e:

                code = e.response.status_code
                reason = ""
                logger.info("Reached err histroy")
                try:

                    error_data = e.response.json()
                    if isinstance(error_data, dict):
                        if "error" in error_data:
                            error_info = error_data["error"]
                            reason = error_info.get("message", "")
                            if "details" in error_info:
                                details = error_info["details"]
                                if isinstance(details, list) and details:
                                    reason = details[0].get("reason", reason)
                except Exception:
                    try:
                        e.response.text
                    except Exception:
                        reason = ""
                logger.exception("get_history HttpError status=%s reason=%s content=%s",
                                 code, reason, getattr(e, "content", None))
                if str(code) in {"400", "404"} and ("history" in reason.lower() or "invalid" in reason.lower()):
                    logger.info(
                        "History baseline invalid → running initial_sync and resetting baseline")
                    await self.initial_sync()
                    prof = await self.client.get_profile()
                    self.acct.history_id = str(prof.get("historyId"))
                    self.db.add(self.acct)
                    self.db.commit()
                    self._update_progress(state="idle")
                    return

                raise
            except Exception as e:
                logger.exception("get_history unexpected error: %s", e)
                errors += 1
                break
            histories = data.get("history", [])
            if histories:
                saw_any_history = True

            for h in histories:
                hid = int(h.get("id", latest_seen_int))
                latest_seen_int = max(latest_seen_int, hid)

                for ma in h.get("messagesAdded", []) or []:
                    msg = ma.get("message") or {}
                    mid = msg.get("id")
                    if not mid:
                        continue
                    try:
                        gmsg = await self.client.get_message_full(mid)
                        headers_map, body_text, body_html = parse_message(gmsg)
                        subject = headers_map.get("subject")
                        from_addr = headers_map.get("from")
                        to_addr = headers_map.get("to")
                        cc = headers_map.get("cc")
                        bcc = headers_map.get("bcc")
                        date_hdr = headers_map.get("date")
                        snippet = gmsg.get("snippet")
                        thread_id = gmsg.get("threadId")
                        label_ids = gmsg.get("labelIds", [])
                        size_estimate = gmsg.get("sizeEstimate")
                        date = None
                        if date_hdr:
                            try:
                                from email.utils import parsedate_to_datetime
                                date = parsedate_to_datetime(date_hdr)
                            except Exception:
                                pass
                        import hashlib
                        hsh = hashlib.sha256()
                        hsh.update(((subject or "") + "|" + (from_addr or "") +
                                   "|" + (body_text or "")).encode("utf-8", errors="ignore"))
                        doc_hash = hsh.hexdigest()[:64]

                        row = (
                            self.db.query(models.EmailMessage)
                            .filter(
                                models.EmailMessage.message_id == mid,
                                models.EmailMessage.gmail_account_id == self.acct.id,
                            )
                            .one_or_none()
                        )
                        if not row:
                            row = models.EmailMessage(
                                gmail_account_id=self.acct.id,
                                message_id=mid,
                            )
                        row.thread_id = thread_id
                        row.subject = subject
                        row.from_addr = from_addr
                        row.to_addr = to_addr
                        row.cc = cc
                        row.bcc = bcc
                        row.date = date
                        row.snippet = snippet
                        row.headers_json = headers_map
                        row.body_text = body_text
                        row.body_html = body_html
                        row.size_estimate = size_estimate
                        row.label_ids = label_ids
                        row.hash_dedup = doc_hash
                        logger.info("Full Messge %s ", body_text)
                        if not row.created_at:
                            from datetime import datetime, timezone
                            row.created_at = datetime.now(timezone.utc)
                        self.db.add(row)
                        self.db.commit()
                        vectors = await build_email_vectors_async(
                            embed_text=embed_text,
                            message_id=mid,
                            gmail_account_id=str(self.acct.id),
                            subject=subject,
                            body_text=body_text,
                            thread_id=thread_id,
                            date=date,
                            label_ids=label_ids,
                            doc_hash=doc_hash,
                        )
                        if vectors:
                            await upsert_vectors(vectors, namespace=str(self.acct.id))
                            row.indexed_at = _now()
                            self.db.add(row)
                            self.db.commit()

                        processed += 1
                        self._update_progress(
                            processed=processed, errors=errors)
                    except Exception:
                        errors += 1
                        self._update_progress(
                            processed=processed, errors=errors)
                for md in h.get("messagesDeleted", []) or []:
                    msg = md.get("message") or {}
                    mid = msg.get("id")
                    if not mid:
                        continue
                    try:
                        row = (
                            self.db.query(models.EmailMessage)
                            .filter(models.EmailMessage.message_id == mid, models.EmailMessage.gmail_account_id == self.acct.id)
                            .one_or_none()
                        )
                        if row:
                            self.db.delete(row)
                            self.db.commit()
                        await delete_by_filter(
                            namespace=str(self.acct.id),
                            where={"message_id": {"$eq": mid}},
                        )
                        processed += 1
                        self._update_progress(
                            processed=processed, errors=errors)
                    except Exception:
                        errors += 1
                        self._update_progress(
                            processed=processed, errors=errors)

                def _apply_labels(msg_wrapper_key: str, add: bool):
                    for lr in h.get(msg_wrapper_key, []) or []:
                        msg = lr.get("message") or {}
                        mid = msg.get("id")
                        if not mid:
                            continue
                        row = (
                            self.db.query(models.EmailMessage)
                            .filter(models.EmailMessage.message_id == mid, models.EmailMessage.gmail_account_id == self.acct.id)
                            .one_or_none()
                        )
                        if not row:
                            continue
                        labels = (msg.get("labelIds") or row.label_ids or [])
                        if add:
                            row.label_ids = sorted(
                                list(set((row.label_ids or []) + labels)))
                        else:
                            row.label_ids = [l for l in (
                                row.label_ids or []) if l not in labels]
                        self.db.add(row)
                        self.db.commit()

                _apply_labels("labelsAdded", add=True)
                _apply_labels("labelsRemoved", add=False)

            page_token = data.get("nextPageToken")
            if not page_token:

                break
        if saw_any_history and latest_seen_int:
            self.acct.history_id = str(latest_seen_int)
        else:
            try:
                prof = await self.client.get_profile()
                self.acct.history_id = str(prof.get("historyId"))
            except Exception:
                self.acct.history_id = str(latest_seen_int)

        self.db.add(self.acct)
        self.db.commit()
        self._update_progress(state="idle")
