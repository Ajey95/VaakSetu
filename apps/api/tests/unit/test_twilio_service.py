from xml.etree import ElementTree
import pytest

from app.config import AppMode, Settings
from app.telephony.twilio_service import TwilioService


def real_settings() -> Settings:
    return Settings(app_mode=AppMode.REAL, public_base_url="https://coach.example.com",
        twilio_account_sid="AC" + "1" * 32, twilio_auth_token="auth-secret",
        twilio_api_key="SK" + "2" * 32, twilio_api_secret="api-secret-that-is-at-least-thirty-two-bytes",
        twilio_twiml_app_sid="AP" + "3" * 32, twilio_caller_id="+442079460123")


def test_outbound_twiml_streams_both_tracks_then_dials_only_validated_destination():
    xml = TwilioService(real_settings()).outbound_twiml("07700 900123", call_id="call-1")
    root = ElementTree.fromstring(xml)
    stream = root.find("./Start/Stream")
    number = root.find("./Dial/Number")
    assert stream is not None and stream.attrib["track"] == "both_tracks"
    assert stream.attrib["url"] == "wss://coach.example.com/ws/media/call-1"
    assert number is not None and number.text == "+447700900123"
    assert root.find("./Dial").attrib["callerId"] == "+442079460123"
    assert "secret" not in xml


def test_invalid_destination_never_reaches_twiml():
    with pytest.raises(ValueError, match="valid phone number"):
        TwilioService(real_settings()).outbound_twiml("dial Ajay", call_id="call-1")


def test_synthetic_token_is_explicit_and_real_mode_generates_jwt():
    synthetic = TwilioService(Settings(app_mode=AppMode.SYNTHETIC)).access_token("agent-1")
    real = TwilioService(real_settings()).access_token("agent-1")
    assert synthetic == {"mode": "synthetic", "token": None, "identity": "agent-1"}
    assert real["mode"] == "real" and real["token"].count(".") == 2
    assert "api-secret" not in real["token"]
