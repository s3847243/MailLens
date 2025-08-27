import uuid
from datetime import datetime

from sqlalchemy import (Column, DateTime, Enum, ForeignKey, Index, Integer,
                        String, Text, UniqueConstraint)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class User(Base):

    __tablename__ = "user"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(
        String(320), unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(200))
    picture_url: Mapped[str | None] = mapped_column(String(1024))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow)

    gmail_accounts = relationship("GmailAccount", back_populates="user")
    chat_sessions = relationship("ChatSession", back_populates="user")


class GmailAccount(Base):
    __tablename__ = "gmail_account"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)

    google_user_id: Mapped[str] = mapped_column(String(128), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)

    access_token: Mapped[str | None] = mapped_column(Text)
    refresh_token: Mapped[str | None] = mapped_column(Text)
    expiry: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    history_id: Mapped[str | None] = mapped_column(String(64))
    token_scope: Mapped[str | None] = mapped_column(Text)
    token_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True))

    user = relationship("User", back_populates="gmail_accounts")
    emails = relationship("EmailMessage", back_populates="gmail_account")

    __table_args__ = (
        UniqueConstraint("user_id", "google_user_id",
                         name="uq_user_google_user"),
    )


class EmailMessage(Base):
    __tablename__ = "email_message"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gmail_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("gmail_account.id"), nullable=False)

    message_id: Mapped[str] = mapped_column(
        String(128), nullable=False, unique=True)
    thread_id: Mapped[str | None] = mapped_column(String(128))

    subject: Mapped[str | None] = mapped_column(String(998))
    from_addr: Mapped[str | None] = mapped_column("from", String(998))
    to_addr: Mapped[str | None] = mapped_column("to", Text)
    cc: Mapped[str | None] = mapped_column(Text)
    bcc: Mapped[str | None] = mapped_column(Text)

    date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    snippet: Mapped[str | None] = mapped_column(Text)
    headers_json: Mapped[dict | None] = mapped_column(JSONB)

    body_text: Mapped[str | None] = mapped_column(Text)
    body_html: Mapped[str | None] = mapped_column(Text)

    size_estimate: Mapped[int | None] = mapped_column(Integer)
    label_ids: Mapped[list[str] | None] = mapped_column(ARRAY(String))

    hash_dedup: Mapped[str | None] = mapped_column(String(64))
    indexed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow)

    gmail_account = relationship("GmailAccount", back_populates="emails")

    __table_args__ = (
        Index("ix_email_gmail_date", "gmail_account_id", "date"),
        Index("ix_email_labels", "label_ids", postgresql_using="gin"),
        Index("ix_email_hash", "hash_dedup"),
    )


class ChatSession(Base):
    __tablename__ = "chat_session"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    title: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow)

    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="chat_session")


class ChatMessage(Base):
    __tablename__ = "chat_message"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chat_session.id"), nullable=False)

    role: Mapped[str] = mapped_column(
        Enum("system", "user", "assistant", name="chat_role"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tokens: Mapped[int | None] = mapped_column(Integer)

    citations: Mapped[dict | list | None] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow)

    chat_session = relationship("ChatSession", back_populates="messages")


# Helpful composite indexes
Index("ix_chat_messages_session_created",
      ChatMessage.chat_session_id, ChatMessage.created_at)
