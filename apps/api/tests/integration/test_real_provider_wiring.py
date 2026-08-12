from fastapi.testclient import TestClient

from app.config import AppMode, Settings
from app.main import create_app
from app.memory.relational import PostgreSQLCallRepository
from app.memory.temporal_graph import Neo4jTemporalGraphStore
from twilio.request_validator import RequestValidator


def real_settings() -> Settings:
    return Settings(app_mode=AppMode.REAL, public_base_url="https://coach.example.com",
        twilio_account_sid="AC"+"1"*32, twilio_auth_token="a"*32, twilio_api_key="SK"+"2"*32,
        twilio_api_secret="s"*32, twilio_twiml_app_sid="AP"+"3"*32, twilio_caller_id="+442079460123",
        deepgram_api_key="dg-secret", llm_provider="openai", llm_api_key="llm-secret", llm_model="gpt-test",
        external_data_mode="real")


def twilio_post(client: TestClient, path: str, data: dict):
    settings = client.app.state.settings
    signature = RequestValidator(settings.twilio_auth_token).compute_signature(
        f"{settings.public_base_url}{path}", data)
    return client.post(path, data=data, headers={"X-Twilio-Signature":signature})


def test_twilio_voice_webhook_registers_real_call_session_before_media_connects():
    with TestClient(create_app(real_settings())) as client:
        response = twilio_post(client, "/twilio/voice", {"To":"07700 900123","CallSid":"CA123"})
        assert response.status_code == 200
        snapshot = client.get("/calls/CA123").json()
        assert snapshot["call"]["id"] == "CA123"
        assert snapshot["call"]["status"] == "dialing"
        assert snapshot["call"]["synthetic"] is False
        assert snapshot["call"]["customer_id"].startswith("phone_")
        assert "447700900123" not in snapshot["call"]["customer_id"]


def test_twilio_status_callback_updates_existing_call_without_intelligence_dependency():
    with TestClient(create_app(real_settings())) as client:
        twilio_post(client, "/twilio/voice", {"To":"07700 900123","CallSid":"CA123"})
        assert twilio_post(client, "/twilio/status", {"CallSid":"CA123","CallStatus":"in-progress"}).status_code == 204
        assert client.get("/calls/CA123").json()["call"]["status"] == "connected"
        assert twilio_post(client, "/twilio/status", {"CallSid":"CA123","CallStatus":"completed"}).status_code == 204
        assert client.get("/calls/CA123").json()["call"]["status"] == "ended"


def test_child_leg_status_is_correlated_to_registered_parent_call():
    with TestClient(create_app(real_settings())) as client:
        twilio_post(client, "/twilio/voice", {"To":"07700 900123","CallSid":"CA_PARENT"})
        response = twilio_post(client, "/twilio/status", {
            "CallSid":"CA_CHILD", "ParentCallSid":"CA_PARENT", "CallStatus":"in-progress"})
        assert response.status_code == 204
        assert client.get("/calls/CA_PARENT").json()["call"]["status"] == "connected"


def test_real_twilio_webhook_rejects_missing_signature():
    with TestClient(create_app(real_settings())) as client:
        response = client.post("/twilio/voice", data={"To":"07700 900123","CallSid":"CA123"})
        assert response.status_code == 403


def test_real_call_service_selects_real_stt_llm_and_external_adapters():
    with TestClient(create_app(real_settings())) as client:
        modes = client.app.state.calls.provider_modes()
        assert modes == {"stt":"deepgram","llm":"openai","external_data":"official_uk"}


def test_configured_persistence_credentials_select_durable_adapters():
    settings = real_settings().model_copy(update={
        "database_url": "postgresql+asyncpg://coach:coach@localhost:5432/coach",
        "neo4j_uri": "bolt://localhost:7687", "neo4j_username": "neo4j", "neo4j_password": "secret",
    })
    with TestClient(create_app(settings)) as client:
        assert isinstance(client.app.state.calls.repository, PostgreSQLCallRepository)
        assert isinstance(client.app.state.calls.graph_store, Neo4jTemporalGraphStore)
