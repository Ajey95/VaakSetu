import asyncio
import pytest
from app.agents.memory_agent import MemoryAgent
from app.memory.relational import InMemoryCallRepository
from app.memory.service import MemoryService
from app.memory.temporal_graph import InMemoryTemporalGraphStore
from app.models.contracts import CallSummary, ConversationState


@pytest.mark.asyncio
async def test_memory_agent_queues_graph_work_without_waiting_for_it():
    gate = asyncio.Event()
    graph = InMemoryTemporalGraphStore(write_gate=gate)
    repo = InMemoryCallRepository()
    agent = MemoryAgent(MemoryService(repo, graph))
    summary = CallSummary(customer_facts=["Budget: £450,000"])
    state = ConversationState(call_id="call-1", customer={"budget": {"value": 450000, "utterance_id": "utt-1"}})
    await asyncio.wait_for(agent.persist("call-1", "customer-1", state, summary), .1)
    await asyncio.sleep(0)
    assert repo.summaries["call-1"] == summary
    assert graph.pending_writes == 1
    gate.set()
    await agent.drain()


@pytest.mark.asyncio
async def test_known_customer_pre_call_brief_is_attributable():
    repo = InMemoryCallRepository()
    graph = InMemoryTemporalGraphStore()
    service = MemoryService(repo, graph)
    summary = CallSummary(customer_facts=["Budget: £450,000"], objections=["price"],
        commitments=["Viewing: Saturday"], next_steps=["Confirm deposit flexibility"])
    await repo.save_call("call-1", "customer-1", summary)
    brief = await service.pre_call_brief("customer-1")
    assert brief["known"] == ["Budget: £450,000"]
    assert brief["last_concern"] == ["price"]
    assert brief["last_commitment"] == ["Viewing: Saturday"]
    assert brief["source_call_id"] == "call-1"


@pytest.mark.asyncio
async def test_database_or_graph_failure_does_not_mutate_live_state():
    state = ConversationState(call_id="call-1", stage="connected")
    service = MemoryService(InMemoryCallRepository(fail=True), InMemoryTemporalGraphStore(fail=True))
    result = await service.persist_call("call-1", "customer-1", state, CallSummary())
    assert result.relational_saved is False
    assert result.graph_queued is False
    assert state.stage == "connected"
