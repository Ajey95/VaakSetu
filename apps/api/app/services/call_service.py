from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from uuid import uuid4

from app.agents.graph import IntelligenceGraph
from app.agents.summary_agent import SummaryAgent
from app.conversation.reducer import apply_final_utterance
from app.conversation.triggers import detect_triggers
from app.llm.synthetic import SyntheticLLMProvider
from app.memory.relational import InMemoryCallRepository
from app.memory.service import MemoryService
from app.memory.temporal_graph import InMemoryTemporalGraphStore
from app.models.contracts import AppEvent, CallStatus, EventType, Speaker, Utterance
from app.sessions.store import InMemorySessionStore
from app.tools.synthetic import SyntheticExternalTool


class CallService:
    def __init__(self) -> None:
        self.store = InMemorySessionStore()
        self.repository = InMemoryCallRepository()
        self.graph_store = InMemoryTemporalGraphStore()
        self.memory = MemoryService(self.repository, self.graph_store)
        self._call_sessions: dict[str, str] = {}
        self._subscribers: dict[str, set[asyncio.Queue]] = {}
        self._tasks: set[asyncio.Task] = set()
        self.feedback: list[dict] = []

    async def create_synthetic_call(self, phone_number: str, customer_id: str | None) -> dict:
        from app.models.contracts import normalize_phone_number
        number = normalize_phone_number(phone_number)
        call_id = f"call_{uuid4().hex[:12]}"
        session = await self.store.create(call_id, customer_id)
        await self.store.set_status(session.session_id, CallStatus.CONNECTED)
        session.health.update({"call": "live", "media": "live", "stt": "live", "coach": "live", "data": "live"})
        self._call_sessions[call_id] = session.session_id
        self._subscribers[call_id] = set()
        snapshot = await self.store.snapshot(session.session_id)
        result = snapshot.model_dump(mode="json")
        result["call"].update({"phone_number": number, "synthetic": True})
        return result

    async def snapshot(self, call_id: str):
        return await self.store.snapshot(self._session_id(call_id))

    async def process_utterance(self, call_id: str, speaker: Speaker, text: str, is_final: bool) -> Utterance:
        session_id = self._session_id(call_id)
        snapshot = await self.store.snapshot(session_id)
        sequence = max((item.sequence for item in snapshot.transcript), default=0) + 1
        utterance = Utterance(id=f"utt_{uuid4().hex[:12]}" if is_final else f"partial_{speaker.value}",
            call_id=call_id, speaker=speaker, text=text, sequence=sequence, is_final=is_final,
            source_track="inbound_track" if speaker is Speaker.CUSTOMER else "outbound_track")
        await self.store.add_utterance(session_id, utterance)
        await self.publish(call_id, EventType.STT_FINAL if is_final else EventType.STT_PARTIAL,
                           utterance.model_dump(mode="json"))
        if not is_final:
            return utterance
        update = apply_final_utterance(snapshot.conversation_state, utterance)
        await self.store.update_conversation(session_id, update.state)
        triggers = detect_triggers(update.state, utterance)
        if triggers:
            task = asyncio.create_task(self._run_intelligence(call_id, update.state, text, triggers[0].type.value))
            self._tasks.add(task)
            task.add_done_callback(self._tasks.discard)
        return utterance

    async def _run_intelligence(self, call_id, state, text, trigger) -> None:
        recommendations = []
        graph = IntelligenceGraph(SyntheticLLMProvider(), SyntheticExternalTool(delay_seconds=.01), recommendations.append)
        result = await graph.run(state, text, trigger)
        session = await self.store.get(self._session_id(call_id))
        session.recommendations.append(result.fast_recommendation)
        session.conversation.current_recommendation = result.fast_recommendation.model_dump(mode="json")
        await self.publish(call_id, EventType.COACH_FAST_READY, result.fast_recommendation.model_dump(mode="json"))
        session.evidence.extend(result.evidence)
        if result.evidence:
            await self.publish(call_id, EventType.EVIDENCE_VERIFIED, result.evidence[0].model_dump(mode="json"))
        if result.deep_recommendation:
            session.recommendations.append(result.deep_recommendation)
            session.conversation.current_recommendation = result.deep_recommendation.model_dump(mode="json")
            await self.publish(call_id, EventType.COACH_DEEP_READY, result.deep_recommendation.model_dump(mode="json"))

    async def end_call(self, call_id: str):
        if self._tasks:
            await asyncio.gather(*list(self._tasks), return_exceptions=True)
        session_id = self._session_id(call_id)
        session = await self.store.get(session_id)
        summary = SummaryAgent().summarize(session.conversation, session.evidence, [])
        session.summary = summary
        await self.store.set_status(session_id, CallStatus.ENDED)
        if session.customer_id:
            await self.memory.persist_call(call_id, session.customer_id, session.conversation, summary)
        await self.publish(call_id, EventType.SUMMARY_READY, summary.model_dump(mode="json"))
        return await self.store.snapshot(session_id)

    async def pre_call_brief(self, customer_id: str) -> dict:
        return await self.memory.pre_call_brief(customer_id)

    async def history(self, customer_id: str) -> list[dict]:
        return [{"call_id": item.call_id, "ended_at": item.ended_at.isoformat(),
                 "summary": item.summary.model_dump(mode="json")} for item in self.repository.calls if item.customer_id == customer_id]

    def subscribe(self, call_id: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._subscribers.setdefault(call_id, set()).add(queue)
        return queue

    def unsubscribe(self, call_id: str, queue: asyncio.Queue) -> None:
        self._subscribers.get(call_id, set()).discard(queue)

    async def publish(self, call_id: str, event_type: EventType, payload: dict) -> None:
        event = AppEvent(type=event_type, event_id=f"evt_{uuid4().hex[:12]}", trace_id=f"trace_{call_id}",
            call_id=call_id, session_id=self._session_id(call_id), payload=payload)
        for queue in list(self._subscribers.get(call_id, set())):
            try:
                queue.put_nowait(event.model_dump(mode="json"))
            except asyncio.QueueFull:
                pass

    async def inject_fault(self, call_id: str, fault: str) -> dict:
        known = {"stt_disconnect": "transcription", "stt_reconnect": "transcription", "buffer_replay": "transcription",
            "duplicate_replay": "transcription", "llm_timeout": "coach", "llm_malformed": "coach",
            "external_timeout": "external_data", "external_rate_limit": "external_data",
            "evidence_conflict": "external_data", "evidence_unverified": "external_data",
            "database_failure": "persistence", "graph_failure": "graph", "frontend_disconnect": "frontend_delivery"}
        if fault not in known:
            raise KeyError(fault)
        session = await self.store.get(self._session_id(call_id))
        if session.status is not CallStatus.CONNECTED:
            raise RuntimeError("Fault injection requires a connected call")
        session.health["stt" if known[fault] == "transcription" else "coach" if known[fault] == "coach" else "data"] = "degraded"
        return {"fault": fault, "call_status": session.status.value, "degraded_capability": known[fault]}

    def _session_id(self, call_id: str) -> str:
        if call_id not in self._call_sessions:
            raise KeyError(call_id)
        return self._call_sessions[call_id]

