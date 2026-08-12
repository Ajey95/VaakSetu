from fastapi.testclient import TestClient
from app.main import create_app


def test_intelligence_faults_do_not_end_connected_call():
    fault_cases = ["stt_disconnect", "stt_reconnect", "buffer_replay", "duplicate_replay", "llm_timeout",
        "llm_malformed", "external_timeout", "external_rate_limit", "evidence_conflict", "evidence_unverified",
        "database_failure", "graph_failure", "frontend_disconnect"]
    with TestClient(create_app()) as client:
        call_id = client.post("/demo/calls", json={"phone_number": "07700 900123"}).json()["call"]["id"]
        for fault in fault_cases:
            result = client.post(f"/demo/calls/{call_id}/faults/{fault}").json()
            assert result["call_status"] == "connected", fault
            assert result["degraded_capability"], fault
