import asyncio

import pytest

from app.models.contracts import EventType, Speaker
from app.services.call_service import CallService
from app.tools.synthetic import SyntheticExternalTool


class CountingTool(SyntheticExternalTool):
    def __init__(self): super().__init__(); self.calls = 0
    async def search(self, query, topic): self.calls += 1; return await super().search(query, topic)


@pytest.mark.asyncio
async def test_fast_coach_is_delivered_before_slow_context_lookup_then_refined():
    service = CallService(external_tool=SyntheticExternalTool(delay_seconds=.2))
    created = await service.create_synthetic_call("07700 900123", "customer-1")
    call_id = created["call"]["id"]
    queue = service.subscribe(call_id)

    await service.process_utterance(
        call_id, Speaker.CUSTOMER, "Manchester house prices fell 10% and the asking price feels too high", True)

    assert (await queue.get())["type"] == EventType.STT_FINAL
    assert (await queue.get())["type"] == EventType.CONVERSATION_STATE_UPDATED
    first = await asyncio.wait_for(queue.get(), timeout=.05)
    assert first["type"] == EventType.COACH_FAST_READY
    assert first["payload"]["next_move"]

    remaining = [await asyncio.wait_for(queue.get(), timeout=.5) for _ in range(4)]
    assert [event["type"] for event in remaining] == [
        EventType.CONTEXT_LOOKUP_STARTED,
        EventType.EVIDENCE_VERIFIED,
        EventType.COACH_DEEP_READY,
        EventType.CONTEXT_LOOKUP_COMPLETED,
    ]
    await service.close()


@pytest.mark.asyncio
async def test_external_failure_is_visible_but_call_and_fast_coach_remain_live():
    service = CallService(external_tool=SyntheticExternalTool(fail=True))
    created = await service.create_synthetic_call("07700 900123", "customer-1")
    call_id = created["call"]["id"]
    await service.process_utterance(call_id, Speaker.CUSTOMER, "Manchester house prices fell 10%", True)
    await service.close()

    snapshot = await service.snapshot(call_id)
    assert snapshot.call["status"] == "connected"
    assert snapshot.recommendations[0].type == "fast"
    assert snapshot.evidence[0].support_status == "unverified"
    assert snapshot.health["data"] == "degraded"


@pytest.mark.asyncio
async def test_identical_trigger_inside_cooldown_does_not_spam_recommendation_cards():
    service = CallService()
    call_id = (await service.create_synthetic_call("07700 900123", "customer-1"))["call"]["id"]
    await service.process_utterance(call_id, Speaker.CUSTOMER, "The asking price feels too high", True)
    await service.close()
    first_count = len((await service.snapshot(call_id)).recommendations)
    await service.process_utterance(call_id, Speaker.CUSTOMER, "The price is still too high", True)
    await service.close()
    assert len((await service.snapshot(call_id)).recommendations) == first_count


@pytest.mark.asyncio
async def test_repeated_external_claim_uses_fresh_provenance_cache_without_second_tool_call():
    tool = CountingTool()
    service = CallService(external_tool=tool)
    first = (await service.create_synthetic_call("07700 900123", "customer-1"))["call"]["id"]
    await service.process_utterance(first, Speaker.CUSTOMER, "Manchester house prices fell 10%", True)
    await service.close()
    second = (await service.create_synthetic_call("07700 900123", "customer-2"))["call"]["id"]
    await service.process_utterance(second, Speaker.CUSTOMER, "Manchester house prices fell 10%", True)
    await service.close()
    snapshot = await service.snapshot(second)
    assert tool.calls == 1
    assert snapshot.evidence[0].source_id == "synthetic-uk-hpi"
    assert snapshot.external_context[0]["category"] == "external_cache"
