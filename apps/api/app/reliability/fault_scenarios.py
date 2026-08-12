from __future__ import annotations

from datetime import UTC, datetime

from app.agents.evidence_agent import EvidenceAgent
from app.agents.graph import IntelligenceGraph
from app.llm.base import LLMProvider
from app.llm.synthetic import SyntheticLLMProvider
from app.memory.relational import InMemoryCallRepository
from app.memory.service import MemoryService
from app.memory.temporal_graph import InMemoryTemporalGraphStore
from app.models.contracts import CallSummary, ConversationState, Speaker
from app.stt.base import STTResult
from app.stt.manager import STTManager
from app.stt.synthetic import SyntheticSTTProvider
from app.tools.base import ExternalTool, SourceResult, ToolResult
from app.tools.synthetic import SyntheticExternalTool


class FailingLLM(LLMProvider):
    async def complete_structured(self, purpose: str, payload: dict, schema: dict[str, type]) -> dict:
        raise TimeoutError("Injected bounded LLM timeout")


class RateLimitedTool(ExternalTool):
    async def search(self, query: str, topic: str) -> ToolResult:
        raise RuntimeError("Injected HTTP 429")


async def run_behavioral_fault(service, call_id: str, fault: str) -> dict:
    observable: dict | list | str | bool
    if fault in {"stt_disconnect", "stt_reconnect", "buffer_replay"}:
        manager = STTManager(lambda speaker: SyntheticSTTProvider(speaker), lambda event: None, call_id)
        await manager.start()
        await manager.send_audio(Speaker.CUSTOMER, b"one", 1, 10)
        await manager.send_audio(Speaker.CUSTOMER, b"two", 2, 20)
        manager.provider(Speaker.CUSTOMER).connected = False
        await manager.reconnect(Speaker.CUSTOMER)
        provider = manager.provider(Speaker.CUSTOMER)
        observable = {"health": manager.health[Speaker.CUSTOMER].value,
                      "replayed_chunks": len(provider.received_audio)}
        service.record_stt_reconnect(call_id)
        await manager.close()
    elif fault == "duplicate_replay":
        events = []
        manager = STTManager(lambda speaker: SyntheticSTTProvider(speaker), events.append, call_id)
        await manager.start()
        result = STTResult(text="Saturday works", is_final=True, confidence=.9, sequence=7)
        await manager.inject_synthetic(Speaker.CUSTOMER, result)
        await manager.inject_synthetic(Speaker.CUSTOMER, result.model_copy(update={"sequence": 8}))
        observable = {"published_finals": len(events)}
        await manager.close()
    elif fault in {"llm_timeout", "llm_malformed"}:
        llm = FailingLLM() if fault == "llm_timeout" else SyntheticLLMProvider(malformed=True)
        graph = IntelligenceGraph(llm, SyntheticExternalTool(), lambda item: None)
        state = ConversationState(call_id=call_id, objections=[{"type": "price"}])
        result = await graph.run(state, "Prices fell 10%", "price_objection")
        observable = {"fast_retained": bool(result.fast_recommendation.next_move),
                      "deep_suppressed": result.deep_recommendation is None}
    elif fault in {"external_timeout", "external_rate_limit"}:
        tool = SyntheticExternalTool(fail=True) if fault == "external_timeout" else RateLimitedTool()
        graph = IntelligenceGraph(SyntheticLLMProvider(), tool, lambda item: None)
        result = await graph.run(ConversationState(call_id=call_id), "Prices fell 10%", "market_claim")
        observable = {"fast_retained": bool(result.fast_recommendation.next_move),
                      "evidence_status": result.evidence[0].support_status}
    elif fault in {"evidence_conflict", "evidence_unverified"}:
        sources = []
        if fault == "evidence_conflict":
            now = datetime.now(UTC)
            sources = [
                SourceResult(source_id="up", title="Official A", provider="official", source_tier=1,
                             retrieved_at=now, content="Prices rose 3%"),
                SourceResult(source_id="down", title="Official B", provider="official", source_tier=1,
                             retrieved_at=now, content="Prices fell 2%"),
            ]
        result = EvidenceAgent().evaluate("Prices fell 10%", sources)
        observable = {"status": result.status, "safe_to_surface": result.safe_to_surface_as_fact}
    elif fault == "database_failure":
        memory = MemoryService(InMemoryCallRepository(fail=True), InMemoryTemporalGraphStore())
        result = await memory.persist_call(call_id, "customer-1", ConversationState(call_id=call_id), CallSummary())
        observable = {"relational_saved": result.relational_saved, "graph_queued": result.graph_queued}
    elif fault == "graph_failure":
        graph = InMemoryTemporalGraphStore(fail=True)
        memory = MemoryService(InMemoryCallRepository(), graph)
        state = ConversationState(call_id=call_id, customer={"budget": {"value": 450000}})
        result = await memory.persist_call(call_id, "customer-1", state, CallSummary())
        if memory.graph_tasks:
            import asyncio
            await asyncio.gather(*list(memory.graph_tasks), return_exceptions=True)
        observable = {"relational_saved": result.relational_saved, "graph_facts": len(graph.facts)}
    elif fault == "frontend_disconnect":
        first = service.subscribe(call_id)
        service.unsubscribe(call_id, first)
        second = service.subscribe(call_id)
        snapshot = await service.snapshot(call_id)
        service.unsubscribe(call_id, second)
        service.record_ui_reconnect(call_id)
        observable = {"snapshot_call_id": snapshot.call["id"], "subscriber_restored": True}
    else:
        raise KeyError(fault)
    return {"fault": fault, "exercised": True, "observable": observable}
