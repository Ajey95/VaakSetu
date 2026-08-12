import json
from app.observability.logging import SafeJsonFormatter, safe_metadata


def test_operational_logging_redacts_contact_transcript_prompt_and_sensitive_values():
    result = safe_metadata({"call_id": "call-1", "phone_number": "+447700900123",
        "transcript": "My budget is £450,000", "prompt": "Full private prompt",
        "budget": 450000, "latency_ms": 290, "provider": "deepgram"})
    assert result == {"call_id": "call-1", "phone_number": "[REDACTED]", "transcript": "[REDACTED]",
        "prompt": "[REDACTED]", "budget": "[REDACTED]", "latency_ms": 290, "provider": "deepgram"}


def test_json_formatter_preserves_correlation_and_error_category():
    import logging
    record = logging.LogRecord("coach", logging.ERROR, __file__, 1, "stt disconnected", (), None)
    record.event = "stt_disconnected"; record.trace_id = "trace-1"; record.call_id = "call-1"
    record.session_id = "session-1"; record.component = "stt"; record.retryable = True
    payload = json.loads(SafeJsonFormatter().format(record))
    assert payload["trace_id"] == "trace-1"
    assert payload["call_id"] == "call-1"
    assert payload["session_id"] == "session-1"
    assert payload["component"] == "stt"
    assert payload["retryable"] is True

