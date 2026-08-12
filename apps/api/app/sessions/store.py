from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from uuid import uuid4

from app.models.contracts import CallStatus, CallSummary, ConversationState, Evidence, Recommendation, SessionSnapshot, Utterance


@dataclass
class Session:
    session_id: str
    call_id: str
    customer_id: str | None
    synthetic: bool = False
    phone_number: str | None = None
    status: CallStatus = CallStatus.IDLE
    health: dict = field(default_factory=lambda: {"call": "connecting", "media": "connecting", "stt": "connecting", "coach": "connecting", "data": "connecting"})
    transcript: list[Utterance] = field(default_factory=list)
    conversation: ConversationState | None = None
    recommendations: list[Recommendation] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    summary: CallSummary | None = None


class InMemorySessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    async def create(self, call_id: str, customer_id: str | None, *, synthetic: bool = False,
                     phone_number: str | None = None) -> Session:
        session = Session(session_id=f"session_{uuid4().hex[:12]}", call_id=call_id, customer_id=customer_id,
                          synthetic=synthetic, phone_number=phone_number,
                          conversation=ConversationState(call_id=call_id, customer_id=customer_id))
        self._sessions[session.session_id] = session
        self._locks[session.session_id] = asyncio.Lock()
        return session

    async def get(self, session_id: str) -> Session:
        return self._sessions[session_id]

    async def delete(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
        self._locks.pop(session_id, None)

    async def set_status(self, session_id: str, status: CallStatus) -> None:
        async with self._locks[session_id]:
            self._sessions[session_id].status = status

    async def add_utterance(self, session_id: str, utterance: Utterance) -> None:
        async with self._locks[session_id]:
            items = self._sessions[session_id].transcript
            if utterance.is_final:
                items[:] = [item for item in items if item.is_final or item.speaker is not utterance.speaker]
                if not any(item.id == utterance.id for item in items):
                    items.append(utterance)
            else:
                for index, item in enumerate(items):
                    if not item.is_final and item.speaker is utterance.speaker:
                        items[index] = utterance
                        break
                else:
                    items.append(utterance)

    async def update_conversation(self, session_id: str, conversation: ConversationState) -> None:
        async with self._locks[session_id]:
            self._sessions[session_id].conversation = conversation.model_copy(deep=True)

    async def snapshot(self, session_id: str) -> SessionSnapshot:
        async with self._locks[session_id]:
            session = self._sessions[session_id]
            return SessionSnapshot(
                call={"id": session.call_id, "session_id": session.session_id, "customer_id": session.customer_id,
                      "status": session.status, "synthetic": session.synthetic, "phone_number": session.phone_number},
                health=dict(session.health), transcript=list(session.transcript),
                conversation_state=session.conversation.model_copy(deep=True), recommendations=list(session.recommendations),
                external_context=list(session.conversation.external_context), evidence=list(session.evidence), summary=session.summary,
            )
