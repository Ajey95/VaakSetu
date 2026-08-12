import pytest
from datetime import UTC, datetime, timedelta
from app.memory.temporal_graph import InMemoryTemporalGraphStore, TemporalFact


@pytest.mark.asyncio
async def test_changing_fact_closes_prior_edge_and_preserves_history():
    graph = InMemoryTemporalGraphStore()
    first = datetime(2026, 8, 1, tzinfo=UTC)
    second = first + timedelta(days=7)
    await graph.upsert_fact(TemporalFact(entity_id="customer-1", predicate="budget", value=400000,
                                         valid_from=first, source_event_id="evt-1"))
    await graph.upsert_fact(TemporalFact(entity_id="customer-1", predicate="budget", value=425000,
                                         valid_from=second, source_event_id="evt-2"))
    history = await graph.history("customer-1", "budget")
    assert [item.value for item in history] == [400000, 425000]
    assert history[0].valid_to == second and history[0].current is False
    assert history[1].valid_to is None and history[1].current is True
