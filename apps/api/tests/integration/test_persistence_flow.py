import pytest
from app.agents.memory_agent import MemoryAgent
from app.memory.relational import InMemoryCallRepository
from app.memory.service import MemoryService
from app.memory.temporal_graph import InMemoryTemporalGraphStore
from app.models.contracts import CallSummary, ConversationState


@pytest.mark.asyncio
async def test_ended_call_persists_summary_then_supports_follow_up_without_graph_hot_path():
    repo, graph = InMemoryCallRepository(), InMemoryTemporalGraphStore()
    service = MemoryService(repo, graph)
    agent = MemoryAgent(service)
    state = ConversationState(call_id="call-1", customer={"budget": {"value": 450000, "utterance_id": "utt-1"}},
        commitments=[{"type": "viewing", "detail": "Saturday", "utterance_id": "utt-2"}])
    summary = CallSummary(customer_facts=["Budget: £450,000"], commitments=["Viewing: Saturday"])
    await agent.persist("call-1", "customer-1", state, summary)
    brief = await service.pre_call_brief("customer-1")
    assert brief["known"] == ["Budget: £450,000"]
    assert brief["last_commitment"] == ["Viewing: Saturday"]
    assert graph.read_count == 0
    await agent.drain()
    assert len(await graph.history("customer-1", "budget")) == 1
