import pytest
from pydantic import ValidationError

from app.models.contracts import AppEvent, EventType, normalize_phone_number


def test_normalizes_uk_phone_number_to_e164():
    assert normalize_phone_number("07700 900123", region="GB") == "+447700900123"


def test_rejects_non_phone_input():
    with pytest.raises(ValueError, match="valid phone number"):
        normalize_phone_number("call Ajay")


def test_event_envelope_requires_every_correlation_identifier():
    with pytest.raises(ValidationError):
        AppEvent(
            type=EventType.CALL_CONNECTED,
            event_id="evt_1",
            call_id="call_1",
            session_id="session_1",
            payload={},
        )


def test_event_envelope_accepts_complete_correlated_event():
    event = AppEvent(
        type=EventType.CALL_CONNECTED,
        event_id="evt_1",
        trace_id="trace_1",
        call_id="call_1",
        session_id="session_1",
        payload={"provider": "synthetic"},
    )

    assert event.type is EventType.CALL_CONNECTED
    assert event.payload == {"provider": "synthetic"}
