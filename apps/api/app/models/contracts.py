from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

import phonenumbers
from pydantic import BaseModel, Field


class CallStatus(StrEnum):
    IDLE = "idle"
    DIALING = "dialing"
    RINGING = "ringing"
    CONNECTED = "connected"
    ENDED = "ended"
    ERROR = "error"


class Speaker(StrEnum):
    AGENT = "agent"
    CUSTOMER = "customer"


class HealthState(StrEnum):
    LIVE = "live"
    CONNECTING = "connecting"
    RECONNECTING = "reconnecting"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class EventType(StrEnum):
    CALL_CREATED = "call.created"
    CALL_DIALING = "call.dialing"
    CALL_RINGING = "call.ringing"
    CALL_CONNECTED = "call.connected"
    CALL_ENDED = "call.ended"
    CALL_FAILED = "call.failed"
    STT_PARTIAL = "stt.partial"
    STT_FINAL = "stt.final"
    CONVERSATION_STAGE_CHANGED = "conversation.stage_changed"
    CONTEXT_LOOKUP_STARTED = "context.lookup.started"
    CONTEXT_LOOKUP_COMPLETED = "context.lookup.completed"
    EVIDENCE_VERIFIED = "evidence.verified"
    COACH_FAST_READY = "coach.fast.ready"
    COACH_DEEP_READY = "coach.deep.ready"
    SUMMARY_READY = "summary.ready"
    SYSTEM_DEGRADED = "system.degraded"
    SYSTEM_RECOVERED = "system.recovered"


class Utterance(BaseModel):
    id: str
    call_id: str
    speaker: Speaker
    text: str = Field(min_length=1)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    sequence: int = Field(ge=0)
    is_final: bool = True
    confidence: float | None = Field(default=None, ge=0, le=1)
    source_track: str


class ConversationState(BaseModel):
    call_id: str
    customer_id: str | None = None
    call_type: str = "unknown"
    stage: str = "opening"
    temperature: str = "unknown"
    sentiment: str = "unknown"
    customer: dict[str, Any] = Field(default_factory=dict)
    signals: list[dict[str, Any]] = Field(default_factory=list)
    objections: list[dict[str, Any]] = Field(default_factory=list)
    commitments: list[dict[str, Any]] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    sensitive_items: list[dict[str, Any]] = Field(default_factory=list)
    external_claims: list[dict[str, Any]] = Field(default_factory=list)
    external_context: list[dict[str, Any]] = Field(default_factory=list)
    current_recommendation: dict[str, Any] | None = None
    previous_recommendations: list[dict[str, Any]] = Field(default_factory=list)


class Recommendation(BaseModel):
    id: str
    type: str
    next_move: str
    reason: str
    confidence: str
    lifecycle: str = "visible"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    evidence_ids: list[str] = Field(default_factory=list)


class Evidence(BaseModel):
    id: str
    claim: str
    source_id: str | None = None
    source_title: str | None = None
    source_url: str | None = None
    source_tier: int | None = Field(default=None, ge=1, le=5)
    retrieved_at: datetime
    published_at: datetime | None = None
    support_status: str
    confidence: float = Field(ge=0, le=1)
    freshness: str
    safe_to_surface_as_fact: bool


class CallSummary(BaseModel):
    customer_facts: list[str] = Field(default_factory=list)
    sales_signals: list[str] = Field(default_factory=list)
    objections: list[str] = Field(default_factory=list)
    commitments: list[str] = Field(default_factory=list)
    external_verified_context: list[dict[str, Any]] = Field(default_factory=list)
    unverified_claims: list[str] = Field(default_factory=list)
    ai_inferences: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    follow_up_memory: list[str] = Field(default_factory=list)


class SessionSnapshot(BaseModel):
    call: dict[str, Any]
    health: dict[str, Any]
    transcript: list[Utterance]
    conversation_state: ConversationState
    recommendations: list[Recommendation] = Field(default_factory=list)
    external_context: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    summary: CallSummary | None = None


class AppEvent(BaseModel):
    type: EventType
    event_id: str = Field(min_length=1)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    trace_id: str = Field(min_length=1)
    call_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    payload: dict[str, Any]


def normalize_phone_number(value: str, region: str = "GB") -> str:
    try:
        parsed = phonenumbers.parse(value, region)
    except phonenumbers.NumberParseException as exc:
        raise ValueError("Enter a valid phone number") from exc
    if not phonenumbers.is_possible_number(parsed):
        raise ValueError("Enter a valid phone number")
    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
