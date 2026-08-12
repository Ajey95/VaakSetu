from fastapi.testclient import TestClient
from app.config import AppMode, Settings
from app.main import create_app


def test_health_discloses_synthetic_mode_and_provider_readiness():
    with TestClient(create_app(Settings(_env_file=None, app_mode=AppMode.SYNTHETIC))) as client:
        health = client.get("/health").json()
        providers = client.get("/health/providers").json()
        assert health == {"status": "ok", "mode": "synthetic"}
        assert providers["twilio"]["mode"] == "synthetic"
        assert providers["twilio"]["configured"] is False


def test_synthetic_call_contract_validates_number_and_returns_snapshot():
    with TestClient(create_app()) as client:
        bad = client.post("/demo/calls", json={"phone_number": "Ajay"})
        assert bad.status_code == 422
        created = client.post("/demo/calls", json={"phone_number": "07700 900123", "customer_id": "customer-1"})
        assert created.status_code == 201
        call = created.json()
        assert call["call"]["status"] == "connected"
        assert call["call"]["synthetic"] is True
        snapshot = client.get(f"/calls/{call['call']['id']}").json()
        assert snapshot["call"]["id"] == call["call"]["id"]


def test_twilio_token_is_explicitly_synthetic_until_credentials_exist():
    with TestClient(create_app()) as client:
        result = client.post("/twilio/token", json={"identity": "agent-1"}).json()
        assert result == {"mode": "synthetic", "token": None, "identity": "agent-1"}


def test_call_summary_feedback_evidence_and_history_routes():
    with TestClient(create_app()) as client:
        call = client.post("/demo/calls", json={"phone_number": "07700 900123", "customer_id": "customer-1"}).json()
        call_id = call["call"]["id"]
        client.post(f"/demo/calls/{call_id}/utterances", json={"speaker": "customer",
            "text": "My budget is £450,000 and prices in Manchester fell 10%", "is_final": True})
        ended = client.post(f"/demo/calls/{call_id}/end").json()
        assert ended["summary"]["customer_facts"] == ["Budget: £450,000"]
        assert client.get(f"/calls/{call_id}/summary").status_code == 200
        assert client.get("/customers/customer-1/precall-brief").json()["source_call_id"] == call_id
        assert client.get("/customers/customer-1/history").json()[0]["call_id"] == call_id
        assert client.post("/recommendations/rec-1/feedback", json={"useful": False, "reason": "too_late"}).status_code == 201
