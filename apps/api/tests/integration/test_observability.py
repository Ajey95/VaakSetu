import asyncio
import pytest
from app.evals.service import AsyncEvaluationService
from app.observability.metrics import Metrics


@pytest.mark.asyncio
async def test_online_eval_queue_returns_before_slow_evaluator_completes():
    service = AsyncEvaluationService(delay_seconds=.2)
    service.queue({"event_id":"evt-1"})
    assert service.records == []
    await service.drain()
    assert service.records == [{"event_id":"evt-1","queued":True}]


def test_metrics_cover_call_stream_stt_coaching_context_and_ui_domains():
    names = Metrics().names()
    assert {"call_setup_total","call_impacting_ai_failures_total","media_packet_gaps_total","stt_reconnects_total",
        "coach_latency_seconds","external_tool_latency_seconds","ui_reconnects_total","recommendation_feedback_total"} <= names
