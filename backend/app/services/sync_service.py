from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict

from sqlalchemy.orm import Session

from .. import models
from ..utils.embeddings import build_embedding_text, embed_batch, embed_text
from ..utils.gmail_client import GmailClient
from ..utils.mime_parse import parse_message
from ..utils.vectorstore import delete_ids, upsert_vectors

# In-memory sync progress keyed by GmailAccount ID (string)
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
        # 2) iterate and persist
        batch_vectors = []
        batch_ids: list[str] = []
        batch_payloads: list[dict] = []
        batch_texts: list[str] = []

        for i, mid in enumerate(ids, start=1):
            try:
                # skip if already stored
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
                # parse Date header best-effort
                date = None
                if date_hdr:
                    try:
                        from email.utils import parsedate_to_datetime
                        date = parsedate_to_datetime(date_hdr)
                    except Exception:
                        pass
                # dedup hash
                h = hashlib.sha256()
                h.update(((subject or "") + "|" + (from_addr or "") + "|" +
                         (body_text or "")).encode("utf-8", errors="ignore"))
                doc_hash = h.hexdigest()[:64]
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
                    body_text=body_text,
                    body_html=body_html,
                    size_estimate=size_estimate,
                    label_ids=label_ids,
                    hash_dedup=doc_hash,
                    indexed_at=None,
                    created_at=datetime.now(timezone.utc),
                )
                self.db.add(row)
                self.db.commit()
                # ---- M3 placeholders ----
                text = build_embedding_text(subject, body_text)
                batch_ids.append(mid)
                batch_texts.append(text)
                batch_payloads.append({
                    "thread_id": thread_id,
                    "gmail_account_id": str(self.acct.id),
                    "subject": subject or "",
                    "from": from_addr or "",
                    "to": to_addr or "",
                    "date": (date.isoformat() if date else None),
                    "label_ids": label_ids,
                    "doc_hash": doc_hash,
                })
                # Flush in chunks to control rate/latency
                if len(batch_ids) >= 64:
                    vecs = await embed_batch(batch_texts)
                    upserts = []
                    for j, v in enumerate(vecs):
                        if v is None:
                            continue
                    upserts.append({
                        "id": batch_ids[j],
                        "values": v,
                        "metadata": {"message_id": batch_ids[j], **batch_payloads[j]},
                    })
                    if upserts:
                        await upsert_vectors(upserts, namespace=str(self.acct.id))
                        # mark indexed_at for those successfully embedded
                        from datetime import datetime, timezone
                        now = datetime.now(timezone.utc)
                        for j, v in enumerate(vecs):
                            if v is None:
                                continue
                            row2 = (
                                self.db.query(models.EmailMessage)
                                .filter(models.EmailMessage.message_id == batch_ids[j])
                                .one_or_none()
                            )
                            if row2:
                                row2.indexed_at = now
                                self.db.add(row2)
                        self.db.commit()
                    batch_ids.clear()
                    batch_texts.clear()
                    batch_payloads.clear()
                # progress update
                prev = SYNC_PROGRESS[str(self.acct.id)]["processed"] if str(
                    self.acct.id) in SYNC_PROGRESS else 0
                self._update_progress(processed=i)
            except Exception:
                prev_err = SYNC_PROGRESS[str(self.acct.id)]["errors"] if str(
                    self.acct.id) in SYNC_PROGRESS else 0
                self._update_progress(processed=i, errors=prev_err + 1)
        # final upsert flush
        if batch_ids:
            vecs = await embed_batch(batch_texts)
            upserts = []
            for j, v in enumerate(vecs):
                if v is None:
                    continue
                upserts.append({
                    "id": batch_ids[j],
                    "values": v,
                    "metadata": {"message_id": batch_ids[j], **batch_payloads[j]},
                })
            if upserts:
                await upsert_vectors(upserts, namespace=str(self.acct.id))
                from datetime import datetime, timezone
                now = datetime.now(timezone.utc)
                for j, v in enumerate(vecs):
                    if v is None:
                        continue
                    row2 = (
                        self.db.query(models.EmailMessage)
                        .filter(models.EmailMessage.message_id == batch_ids[j])
                        .one_or_none()
                    )
                    if row2:
                        row2.indexed_at = now
                        self.db.add(row2)
                self.db.commit()
        # if batch_vectors:
        #     await upsert_vectors(batch_vectors)
        # 3) store latest historyId for incremental syncs later
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
        start_id = self.acct.history_id
        if not start_id:
            # No baseline — fall back to initial sync (or simply return)
            return await self.initial_sync()

        self._update_progress(state="incremental", total=0)

        latest_seen = int(start_id)
        page_token = None
        processed = 0
        errors = 0
        while True:
            try:
                data = await self.client.get_history(start_id, page_token)
            except Exception:
                errors += 1
                break

            histories = data.get("history", [])
            if not histories:
                break
            for h in histories:
                hid = int(h.get("id", latest_seen))
                latest_seen = max(latest_seen, hid)

                # 1) messageAdded: fetch & upsert
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
                        # dedup hash
                        import hashlib
                        hsh = hashlib.sha256()
                        hsh.update(((subject or "") + "|" + (from_addr or "") +
                                   "|" + (body_text or "")).encode("utf-8", errors="ignore"))
                        doc_hash = hsh.hexdigest()[:64]
                        row = (
                            self.db.query(models.EmailMessage)
                            .filter(models.EmailMessage.message_id == mid)
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
                        if not row.created_at:
                            from datetime import datetime, timezone
                            row.created_at = datetime.now(timezone.utc)
                        text = build_embedding_text(subject, body_text)
                        vec = await embed_text(text)
                        if vec is not None:
                            await upsert_vectors([{
                                "id": mid,
                                "values": vec,
                                "metadata": {
                                    "message_id": mid,
                                    "thread_id": thread_id,
                                    "gmail_account_id": str(self.acct.id),
                                    "subject": subject or "",
                                    "from": from_addr or "",
                                    "to": to_addr or "",
                                    "date": (date.isoformat() if date else None),
                                    "label_ids": label_ids,
                                    "doc_hash": doc_hash,
                                },
                            }], namespace=str(self.acct.id))
                            from datetime import datetime, timezone
                            row.indexed_at = datetime.now(timezone.utc)
                            self.db.add(row)
                            self.db.commit()

                        # (M3) embedding/upsert integration point
                        # text = build_embedding_text(subject, body_text)
                        # vec = await embed_text(text)
                        # if vec is not None: ... upsert_vectors([...]) and set row.indexed_at
                        processed += 1
                        self._update_progress(
                            processed=processed, errors=errors)
                    except Exception:
                        errors += 1
                        self._update_progress(
                            processed=processed, errors=errors)
                # 2) messageDeleted: remove from DB (soft delete alternative optional)
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
                        await delete_ids([mid], namespace=str(self.acct.id))
                        processed += 1
                        self._update_progress(
                            processed=processed, errors=errors)
                    except Exception:
                        errors += 1
                        self._update_progress(
                            processed=processed, errors=errors)
                # 3) labelsAdded/labelsRemoved: update label_ids if row exists

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
                        # Gmail sends labels in wrapper; if absent, fall back to fetching the message
                        labels = (msg.get("labelIds") or row.label_ids or [])
                        if add:
                            # union
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
        # update account history_id to the latest seen
        self.acct.history_id = str(latest_seen)
        self.db.add(self.acct)
        self.db.commit()
        self._update_progress(state="idle")
