from __future__ import annotations

import asyncio
import hashlib
from time import perf_counter
from datetime import UTC, datetime
from uuid import uuid4

from app.agents.graph import IntelligenceGraph
from app.agents.summary_agent import SummaryAgent
from app.conversation.reducer import apply_final_utterance
from app.conversation.triggers import detect_triggers
from app.llm.synthetic import SyntheticLLMProvider
from app.llm.structured import OpenAICompatibleLLMProvider
from app.config import AppMode, Settings
from app.memory.relational import InMemoryCallRepository, PostgreSQLCallRepository
from app.memory.service import MemoryService
from app.memory.temporal_graph import InMemoryTemporalGraphStore, Neo4jTemporalGraphStore
from app.models.contracts import AppEvent, CallStatus, EventType, Speaker, Utterance
from app.sessions.store import InMemorySessionStore
from app.tools.synthetic import SyntheticExternalTool
from app.tools.official_uk import OfficialUKTool
from app.stt.deepgram import DeepgramSTTProvider
from app.stt.manager import STTManager
from app.stt.synthetic import SyntheticSTTProvider
from app.evals.service import AsyncEvaluationService
from app.observability.metrics import Metrics
from app.observability.trajectory import TrajectoryRecorder


class CallService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.store = InMemorySessionStore()
        self.database_engine = None
        if self.settings.database_url:
            from app.db.base import create_database
            self.database_engine, session_factory = create_database(self.settings.database_url)
            self.repository = PostgreSQLCallRepository(session_factory)
        else:
            self.repository = InMemoryCallRepository()
        if self.settings.neo4j_uri and self.settings.neo4j_username and self.settings.neo4j_password:
            self.graph_store = Neo4jTemporalGraphStore(
                self.settings.neo4j_uri, self.settings.neo4j_username, self.settings.neo4j_password)
        else:
            self.graph_store = InMemoryTemporalGraphStore()
        self.memory = MemoryService(self.repository, self.graph_store)
        self._call_sessions: dict[str, str] = {}
        self._subscribers: dict[str, set[asyncio.Queue]] = {}
        self._tasks: set[asyncio.Task] = set()
        self.feedback: list[dict] = []
        self._stt_managers: dict[str, STTManager] = {}
        self.metrics = Metrics()
        self.trajectory_recorder = TrajectoryRecorder()
        self.trajectories: dict[str, list[dict]] = {}
        self.evaluations = AsyncEvaluationService()

    async def create_synthetic_call(self, phone_number: str, customer_id: str | None) -> dict:
        from app.models.contracts import normalize_phone_number
        number = normalize_phone_number(phone_number)
        call_id = f"call_{uuid4().hex[:12]}"
        session = await self.store.create(call_id, customer_id, synthetic=True, phone_number=number)
        await self.store.set_status(session.session_id, CallStatus.CONNECTED)
        session.health.update({"call": "live", "media": "live", "stt": "live", "coach": "live", "data": "live"})
        self._call_sessions[call_id] = session.session_id
        self._subscribers[call_id] = set()
        self.trajectories[call_id] = []
        self.metrics.values["call_setup_total"].inc()
        snapshot = await self.store.snapshot(session.session_id)
        return snapshot.model_dump(mode="json")

    async def register_real_call(self, call_id: str, phone_number: str) -> None:
        if call_id in self._call_sessions:
            return
        from app.models.contracts import normalize_phone_number
        number = normalize_phone_number(phone_number)
        customer_id = f"phone_{hashlib.sha256(number.encode('utf-8')).hexdigest()[:24]}"
        session = await self.store.create(call_id, customer_id, synthetic=False, phone_number=number)
        await self.store.set_status(session.session_id, CallStatus.DIALING)
        session.health.update({"call": "connecting", "media": "connecting", "stt": "connecting",
                               "coach": "connecting", "data": "connecting"})
        self._call_sessions[call_id] = session.session_id
        self._subscribers[call_id] = set()
        self.trajectories[call_id] = []
        self.metrics.values["call_setup_total"].inc()

    async def update_real_call_status(self, call_id: str, provider_status: str) -> None:
        mapping = {"queued": CallStatus.DIALING, "initiated": CallStatus.DIALING,
                   "ringing": CallStatus.RINGING, "in-progress": CallStatus.CONNECTED,
                   "completed": CallStatus.ENDED, "busy": CallStatus.ENDED,
                   "no-answer": CallStatus.ENDED, "failed": CallStatus.ERROR, "canceled": CallStatus.ENDED}
        if call_id not in self._call_sessions:
            return
        status = mapping.get(provider_status, CallStatus.ERROR)
        await self.store.set_status(self._session_id(call_id), status)
        session = await self.store.get(self._session_id(call_id))
        session.health["call"] = "live" if status is CallStatus.CONNECTED else "connecting" if status in {CallStatus.DIALING, CallStatus.RINGING} else "unavailable"

    def provider_modes(self) -> dict[str, str]:
        if self.settings.app_mode is AppMode.SYNTHETIC:
            return {"stt": "synthetic", "llm": "synthetic", "external_data": "synthetic"}
        return {"stt": self.settings.stt_provider,
                "llm": self.settings.llm_provider or "unconfigured",
                "external_data": "official_uk" if self.settings.external_data_mode == "real" else "synthetic"}

    async def start_stt(self, call_id: str) -> STTManager:
        if call_id in self._stt_managers:
            return self._stt_managers[call_id]
        def publish(utterance: Utterance) -> None:
            task = asyncio.create_task(self.process_utterance(call_id, utterance.speaker, utterance.text, utterance.is_final))
            self._tasks.add(task); task.add_done_callback(self._tasks.discard)
        if self.settings.app_mode is AppMode.REAL:
            factory = lambda speaker: DeepgramSTTProvider(speaker, self.settings.deepgram_api_key)
        else:
            factory = lambda speaker: SyntheticSTTProvider(speaker)
        manager = STTManager(factory, publish, call_id=call_id)
        await manager.start()
        self._stt_managers[call_id] = manager
        session = await self.store.get(self._session_id(call_id))
        session.health.update({"media": "live", "stt": "live"})
        return manager

    async def stop_stt(self, call_id: str) -> None:
        manager = self._stt_managers.pop(call_id, None)
        if manager:
            await manager.close()

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
        started = perf_counter()
        recommendations = []
        if self.settings.app_mode is AppMode.REAL:
            llm = OpenAICompatibleLLMProvider(self.settings.llm_api_key, self.settings.llm_model)
            tool = OfficialUKTool() if self.settings.external_data_mode == "real" else SyntheticExternalTool(delay_seconds=.01)
        else:
            llm, tool = SyntheticLLMProvider(), SyntheticExternalTool(delay_seconds=.01)
        graph = IntelligenceGraph(llm, tool, recommendations.append)
        result = await graph.run(state, text, trigger)
        latency_ms = max(0, round((perf_counter() - started) * 1000))
        self.metrics.values["coach_latency_seconds"].observe(latency_ms / 1000)
        event_id = f"evt_{uuid4().hex[:12]}"
        latest = next((item for item in reversed(state.objections + state.commitments + state.external_claims)
                       if item.get("utterance_id")), {})
        trajectory = self.trajectory_recorder.record(
            event_id=event_id, call_id=call_id, utterance_id=latest.get("utterance_id", "unknown"),
            speaker="customer", intent=trigger, stage=state.stage, confidence=.8,
            knowledge_rag=True, external_research=bool(state.external_claims),
            fast_recommendation_id=result.fast_recommendation.id,
            latencies_ms={"coach": latency_ms, "end_to_end": latency_ms})
        if result.deep_recommendation:
            trajectory["deep_coach_recommendation_id"] = result.deep_recommendation.id
        self.trajectories.setdefault(call_id, []).append(trajectory)
        self.evaluations.queue(trajectory)
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
        calls = await self.repository.history_for_customer(customer_id)
        return [{"call_id": item.call_id, "ended_at": item.ended_at.isoformat(),
                 "summary": item.summary.model_dump(mode="json")} for item in calls]

    async def close(self) -> None:
        await asyncio.gather(*list(self._tasks), return_exceptions=True)
        await asyncio.gather(*list(self.memory.graph_tasks), return_exceptions=True)
        await self.evaluations.drain()
        if isinstance(self.graph_store, Neo4jTemporalGraphStore):
            await self.graph_store.close()
        if self.database_engine:
            await self.database_engine.dispose()

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
