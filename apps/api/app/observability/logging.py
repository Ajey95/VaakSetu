from __future__ import annotations

import json
import logging
from datetime import UTC, datetime


SENSITIVE_KEYS = {"phone", "phone_number", "contact", "email", "transcript", "utterance", "prompt", "raw_audio",
                  "audio", "budget", "mortgage", "deposit", "sensitive_items", "api_key", "auth_token", "password"}


def safe_metadata(values: dict) -> dict:
    return {key: "[REDACTED]" if key.lower() in SENSITIVE_KEYS else value for key, value in values.items()}


class SafeJsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        fields = {"timestamp": datetime.now(UTC).isoformat(), "level": record.levelname,
            "service": record.name, "event": getattr(record, "event", record.getMessage()),
            "trace_id": getattr(record, "trace_id", None), "call_id": getattr(record, "call_id", None),
            "session_id": getattr(record, "session_id", None), "component": getattr(record, "component", None),
            "retryable": getattr(record, "retryable", None), "degraded_capability": getattr(record, "degraded_capability", None)}
        return json.dumps(safe_metadata({key: value for key, value in fields.items() if value is not None}), default=str)


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(SafeJsonFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(logging.INFO)

