from datetime import UTC, datetime


class TrajectoryRecorder:
    def record(self, *, event_id: str, call_id: str, utterance_id: str, speaker: str, intent: str,
               stage: str, confidence: float, knowledge_rag: bool, external_research: bool,
               fast_recommendation_id: str, latencies_ms: dict[str, int]) -> dict:
        return {"event_id": event_id, "call_id": call_id, "timestamp": datetime.now(UTC).isoformat(),
            "trigger": {"speaker": speaker, "utterance_id": utterance_id},
            "conversation_agent": {"intent": intent, "stage": stage, "confidence": confidence},
            "router": {"knowledge_rag": knowledge_rag, "external_research": external_research},
            "fast_coach_recommendation_id": fast_recommendation_id, "deep_coach_recommendation_id": None,
            "latencies_ms": dict(latencies_ms)}

