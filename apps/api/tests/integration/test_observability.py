import asyncio
import logging
import pytest
from app.evals.service import AsyncEvaluationService
from app.observability.metrics import Metrics
from fastapi.testclient import TestClient
from app.main import create_app
from app.models.contracts import Speaker
from app.services.call_service import CallService
from app.tools.synthetic import SyntheticExternalTool


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


def test_live_recommendation_records_trajectory_queues_eval_and_exports_prometheus_metrics():
    with TestClient(create_app()) as client:
        call_id = client.post("/demo/calls", json={"phone_number":"07700 900123"}).json()["call"]["id"]
        client.post(f"/demo/calls/{call_id}/utterances", json={
            "speaker":"customer", "text":"The asking price feels too high", "is_final":True})
        import time
        time.sleep(.05)
        trajectories = client.get(f"/calls/{call_id}/trajectories").json()
        assert trajectories[0]["call_id"] == call_id
        assert trajectories[0]["fast_coach_recommendation_id"].startswith("rec_")
        assert client.app.state.calls.evaluations.records[0]["queued"] is True
        metrics = client.get("/metrics")
        assert metrics.headers["content-type"].startswith("text/plain")
        assert "coach_latency_seconds_count" in metrics.text


@pytest.mark.asyncio
async def test_live_pipeline_logs_correlated_components_without_transcript_or_phone(caplog):
    caplog.set_level(logging.INFO)
    service = CallService(external_tool=SyntheticExternalTool(delay_seconds=.01))
    call_id = (await service.create_synthetic_call("07700 900123", "customer-1"))["call"]["id"]
    await service.process_utterance(call_id, Speaker.CUSTOMER,
        "Manchester house prices fell 10% and the asking price feels too high", True)
    await service.close()

    events = {getattr(record, "event", ""): record for record in caplog.records}
    assert {"call_connected", "stt_final_received", "conversation_state_updated",
            "coach_fast_ready", "context_lookup_started", "context_lookup_completed",
            "coach_deep_ready"} <= set(events)
    assert all(getattr(record, "trace_id", "") == f"trace_{call_id}" for record in events.values())
    rendered = " ".join(record.getMessage() for record in caplog.records)
    assert "07700" not in rendered
    assert "house prices fell" not in rendered.lower()


@pytest.mark.asyncio
async def test_external_lookup_and_feedback_increment_runtime_metrics():
    service = CallService(external_tool=SyntheticExternalTool(delay_seconds=.01))
    before_tool = service.metrics.values["external_tool_latency_seconds"]._sum.get()
    before_feedback = service.metrics.values["recommendation_feedback_total"]._value.get()
    call_id = (await service.create_synthetic_call("07700 900123", "customer-1"))["call"]["id"]
    await service.process_utterance(call_id, Speaker.CUSTOMER, "Manchester house prices fell 10%", True)
    await service.close()
    service.record_feedback("rec-1", True, None)
    assert service.metrics.values["external_tool_latency_seconds"]._sum.get() > before_tool
    assert service.metrics.values["recommendation_feedback_total"]._value.get() == before_feedback + 1


@pytest.mark.asyncio
async def test_stream_stt_and_frontend_recovery_metrics_increment_on_real_recovery_actions():
    service = CallService()
    before_gap = service.metrics.values["media_packet_gaps_total"]._value.get()
    before_stt = service.metrics.values["stt_reconnects_total"]._value.get()
    before_ui = service.metrics.values["ui_reconnects_total"]._value.get()
    call_id = (await service.create_synthetic_call("07700 900123", "customer-1"))["call"]["id"]
    service.record_media_gap(call_id)
    service.record_stt_reconnect(call_id)
    service.record_ui_reconnect(call_id)
    assert service.metrics.values["media_packet_gaps_total"]._value.get() == before_gap + 1
    assert service.metrics.values["stt_reconnects_total"]._value.get() == before_stt + 1
    assert service.metrics.values["ui_reconnects_total"]._value.get() == before_ui + 1


@pytest.mark.asyncio
async def test_knowledge_failure_is_logged_and_fast_coaching_remains_live(caplog):
    class UnavailableKnowledge:
        async def retrieve(self, query: str):
            raise ConnectionError("vector store unavailable")

    caplog.set_level(logging.INFO)
    service = CallService(knowledge_agent=UnavailableKnowledge())
    call_id = (await service.create_synthetic_call("07700 900123", "customer-1"))["call"]["id"]
    await service.process_utterance(call_id, Speaker.CUSTOMER,
        "Your fee is too high", True)
    await service.close()

    snapshot = await service.snapshot(call_id)
    failure = next(record for record in caplog.records
                   if getattr(record, "event", "") == "knowledge_retrieval_failed")
    assert snapshot.call["status"] == "connected"
    assert snapshot.recommendations[0].type == "fast"
    assert failure.retryable is True
    assert failure.degraded_capability == "knowledge_rag"
