import asyncio
import pytest
from app.evals.service import AsyncEvaluationService
from app.observability.metrics import Metrics
from fastapi.testclient import TestClient
from app.main import create_app


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
