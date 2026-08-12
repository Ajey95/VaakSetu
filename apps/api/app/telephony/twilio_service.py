from __future__ import annotations

from urllib.parse import urlparse

from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VoiceGrant
from twilio.twiml.voice_response import VoiceResponse

from app.config import AppMode, Settings
from app.models.contracts import normalize_phone_number


class TwilioService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def access_token(self, identity: str) -> dict[str, str | None]:
        if self.settings.app_mode is AppMode.SYNTHETIC:
            return {"mode": "synthetic", "token": None, "identity": identity}
        token = AccessToken(self.settings.twilio_account_sid, self.settings.twilio_api_key,
                            self.settings.twilio_api_secret, identity=identity)
        token.add_grant(VoiceGrant(outgoing_application_sid=self.settings.twilio_twiml_app_sid,
                                   incoming_allow=False))
        encoded = token.to_jwt()
        if isinstance(encoded, bytes):
            encoded = encoded.decode("utf-8")
        return {"mode": "real", "token": encoded, "identity": identity}

    def outbound_twiml(self, destination: str, call_id: str) -> str:
        number = normalize_phone_number(destination)
        parsed = urlparse(self.settings.public_base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("PUBLIC_BASE_URL must be an absolute HTTP(S) URL")
        websocket_scheme = "wss" if parsed.scheme == "https" else "ws"
        stream_url = f"{websocket_scheme}://{parsed.netloc}/ws/media/{call_id}"
        response = VoiceResponse()
        response.start().stream(url=stream_url, track="both_tracks",
                                status_callback=f"{self.settings.public_base_url.rstrip('/')}/twilio/stream-status")
        dial = response.dial(caller_id=self.settings.twilio_caller_id,
                             action=f"{self.settings.public_base_url.rstrip('/')}/twilio/status",
                             method="POST")
        dial.number(number, status_callback=f"{self.settings.public_base_url.rstrip('/')}/twilio/status",
                    status_callback_event="initiated ringing answered completed")
        return str(response)

