from app.observability.trajectory import TrajectoryRecorder


def test_trajectory_records_trigger_routing_recommendation_and_latency_without_transcript():
    record = TrajectoryRecorder().record(event_id="evt-1", call_id="call-1", utterance_id="utt-1",
        speaker="customer", intent="price_objection", stage="objection_handling", confidence=.94,
        knowledge_rag=True, external_research=False, fast_recommendation_id="rec-1",
        latencies_ms={"stt": 290, "classification": 84, "coach": 520, "end_to_end": 934})
    assert record["trigger"] == {"speaker": "customer", "utterance_id": "utt-1"}
    assert record["router"]["knowledge_rag"] is True
    assert "transcript" not in str(record).lower()

