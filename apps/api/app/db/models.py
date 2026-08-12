from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase): pass


def id_column() -> Mapped[str]:
    return mapped_column(String(64), primary_key=True, default=lambda: uuid4().hex)


class Customer(Base):
    __tablename__ = "customers"
    id: Mapped[str] = id_column()
    display_name: Mapped[str | None] = mapped_column(String(255))
    phone_hash: Mapped[str | None] = mapped_column(String(128), index=True)


class Call(Base):
    __tablename__ = "calls"
    id: Mapped[str] = id_column()
    twilio_call_sid: Mapped[str | None] = mapped_column(String(64), unique=True)
    customer_id: Mapped[str | None] = mapped_column(ForeignKey("customers.id"), index=True)
    direction: Mapped[str] = mapped_column(String(16), default="outbound")
    call_type: Mapped[str] = mapped_column(String(16), default="unknown")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    connected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32))


class UtteranceRow(Base):
    __tablename__ = "utterances"
    id: Mapped[str] = id_column()
    call_id: Mapped[str] = mapped_column(ForeignKey("calls.id"), index=True)
    speaker: Mapped[str] = mapped_column(String(16))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    text: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float | None] = mapped_column(Float)
    sequence: Mapped[int] = mapped_column(Integer)
    source_track: Mapped[str] = mapped_column(String(32))
    is_final: Mapped[bool] = mapped_column(Boolean, default=True)


class GenericCallRecord(Base):
    __tablename__ = "conversation_events"
    id: Mapped[str] = id_column()
    call_id: Mapped[str] = mapped_column(String(64), index=True)
    kind: Mapped[str] = mapped_column(String(64), index=True)
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class RecommendationRow(Base):
    __tablename__ = "recommendations"
    id: Mapped[str] = id_column()
    call_id: Mapped[str] = mapped_column(String(64), index=True)
    event_id: Mapped[str | None] = mapped_column(String(64))
    type: Mapped[str] = mapped_column(String(16))
    next_move: Mapped[str] = mapped_column(Text)
    reason: Mapped[str] = mapped_column(Text)
    confidence: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    stale_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    evidence_ids: Mapped[list] = mapped_column(JSON, default=list)


class CallSummaryRow(Base):
    __tablename__ = "call_summaries"
    id: Mapped[str] = id_column()
    call_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    customer_id: Mapped[str | None] = mapped_column(String(64), index=True)
    content: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    id: Mapped[str] = id_column()
    document_id: Mapped[str] = mapped_column(String(64), index=True)
    content: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)


class RecommendationFeedback(Base):
    __tablename__ = "recommendation_feedback"
    id: Mapped[str] = id_column()
    recommendation_id: Mapped[str] = mapped_column(String(64), index=True)
    useful: Mapped[bool] = mapped_column(Boolean)
    reason: Mapped[str | None] = mapped_column(String(128))


class EvalRecord(Base):
    __tablename__ = "eval_runs"
    id: Mapped[str] = id_column()
    call_id: Mapped[str | None] = mapped_column(String(64), index=True)
    payload: Mapped[dict] = mapped_column(JSON)
    score: Mapped[float | None] = mapped_column(Float)

