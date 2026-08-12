from pathlib import Path

import pytest

from app.agents.knowledge_agent import KnowledgeAgent
from app.memory.vector import InMemoryVectorStore
from app.models.contracts import Speaker
from app.services.call_service import CallService


@pytest.mark.asyncio
async def test_objection_routes_live_knowledge_context_into_session_and_trajectory():
    root = Path(__file__).parents[4] / "knowledge"
    service = CallService(knowledge_agent=KnowledgeAgent(root, InMemoryVectorStore()))
    call_id = (await service.create_synthetic_call("07700 900123", "customer-1"))["call"]["id"]

    await service.process_utterance(
        call_id, Speaker.CUSTOMER, "Your commission fee is too high", True)
    await service.close()

    snapshot = await service.snapshot(call_id)
    assert snapshot.external_context
    context = snapshot.external_context[0]
    assert context["category"] == "internal_knowledge"
    assert context["source"].endswith("playbook.md")
    assert "diagnostic question" in context["content"]
    assert service.trajectories[call_id][0]["router"]["knowledge_rag"] is True
    assert snapshot.recommendations[-1].type == "deep"
    assert snapshot.recommendations[-1].lifecycle == "refined"
    assert "internal playbook" in snapshot.recommendations[-1].reason.lower()


@pytest.mark.asyncio
async def test_knowledge_agent_indexes_and_retrieves_vector_chunks_without_external_credentials():
    root = Path(__file__).parents[4] / "knowledge"
    store = InMemoryVectorStore()
    agent = KnowledgeAgent(root, store)
    results = await agent.retrieve("fee objection diagnostic question")
    assert results
    assert len(store.chunks) == len(list(root.rglob("*.md")))
    assert results[0]["source"].endswith("playbook.md")
    assert results[0]["retrieval"] == "vector"
