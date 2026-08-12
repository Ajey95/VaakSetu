from prometheus_client import Counter, Histogram, REGISTRY


class Metrics:
    METRICS = {
        "call_setup_total": (Counter, "Call setup attempts"),
        "call_impacting_ai_failures_total": (Counter, "AI failures that affected the phone call"),
        "media_packet_gaps_total": (Counter, "Media sequence gaps"),
        "stt_reconnects_total": (Counter, "STT reconnect attempts"),
        "coach_latency_seconds": (Histogram, "Meaningful event to coaching latency"),
        "external_tool_latency_seconds": (Histogram, "External tool latency"),
        "ui_reconnects_total": (Counter, "UI reconnect attempts"),
        "recommendation_feedback_total": (Counter, "Recommendation feedback events"),
    }
    def __init__(self) -> None:
        existing = {name: collector for collector in REGISTRY._collector_to_names for name in REGISTRY._collector_to_names[collector]}
        self.values = {}
        for name, (kind, description) in self.METRICS.items():
            self.values[name] = existing.get(name) or kind(name, description)
    def names(self) -> set[str]: return set(self.values)

