import pytest
from app.agents.memory_agent import MemoryAgent
from app.memory.relational import InMemoryCallRepository
from app.memory.service import MemoryService
from app.memory.temporal_graph import InMemoryTemporalGraphStore
from app.models.contracts import CallSummary, ConversationState
from app.models.contracts import Recommendation
from fastapi.testclient import TestClient
from app.main import create_app


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


def test_second_call_for_same_customer_includes_attributable_pre_call_brief():
    with TestClient(create_app()) as client:
        first = client.post("/demo/calls", json={
            "phone_number":"07700 900123", "customer_id":"customer-1"}).json()
        first_id = first["call"]["id"]
        client.post(f"/demo/calls/{first_id}/utterances", json={"speaker":"customer",
            "text":"My budget is 450000 and a Saturday viewing works for me", "is_final":True})
        client.post(f"/calls/{first_id}/end")

        second = client.post("/demo/calls", json={
            "phone_number":"07700 900123", "customer_id":"customer-1"}).json()
        assert second["pre_call_brief"]["source_call_id"] == first_id
        assert "Budget" in second["pre_call_brief"]["known"][0]
        assert second["pre_call_brief"]["last_commitment"]
        reconnected = client.get(f"/calls/{second['call']['id']}").json()
        assert reconnected["pre_call_brief"]["source_call_id"] == first_id


@pytest.mark.asyncio
async def test_feedback_updates_recommendation_lifecycle_authoritatively():
    from app.services.call_service import CallService
    service = CallService()
    snapshot = await service.create_synthetic_call("07700 900123", "customer-1")
    session = await service.store.get(snapshot["call"]["session_id"])
    recommendation = Recommendation(id="rec-1", type="fast", next_move="Ask about timing",
        reason="Timeline is unknown", confidence="medium")
    session.recommendations.append(recommendation)
    session.conversation.current_recommendation = recommendation.model_dump(mode="json")

    service.record_feedback("rec-1", True, None)

    updated = await service.snapshot(snapshot["call"]["id"])
    assert updated.recommendations[0].lifecycle == "accepted"
    assert updated.conversation_state.current_recommendation["lifecycle"] == "accepted"
