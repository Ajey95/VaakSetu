import pytest
from app.agents.graph import IntelligenceGraph
from app.llm.synthetic import SyntheticLLMProvider
from app.models.contracts import ConversationState
from app.tools.synthetic import SyntheticExternalTool


@pytest.mark.asyncio
async def test_fast_recommendation_is_emitted_before_slow_research_refinement():
    emitted = []
    graph = IntelligenceGraph(SyntheticLLMProvider(), SyntheticExternalTool(delay_seconds=.02), emitted.append)
    state = ConversationState(call_id="call-1", stage="objection_handling", objections=[{"type": "price"}])
    await graph.run(state, "Prices around Manchester fell 10%", "price_objection")
    assert emitted[0].type == "fast"
    assert emitted[-1].type == "deep"
    assert emitted[-1].lifecycle == "refined"
    assert emitted[-1].evidence_ids


@pytest.mark.asyncio
async def test_research_failure_keeps_fast_recommendation_and_records_unverified():
    emitted = []
    graph = IntelligenceGraph(SyntheticLLMProvider(), SyntheticExternalTool(fail=True), emitted.append)
    state = ConversationState(call_id="call-1", objections=[{"type": "price"}])
    result = await graph.run(state, "Prices fell 10%", "price_objection")
    assert [item.type for item in emitted] == ["fast"]
    assert result.evidence[0].support_status == "unverified"
    assert result.fast_recommendation.lifecycle == "visible"


@pytest.mark.asyncio
async def test_malformed_llm_output_degrades_without_erasing_fast_recommendation():
    emitted = []
    graph = IntelligenceGraph(SyntheticLLMProvider(malformed=True), SyntheticExternalTool(), emitted.append)
    state = ConversationState(call_id="call-1", objections=[{"type": "price"}])
    result = await graph.run(state, "Prices fell 10%", "price_objection")
    assert result.fast_recommendation.next_move
    assert result.deep_recommendation is None

