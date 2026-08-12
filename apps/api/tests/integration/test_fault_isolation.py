from fastapi.testclient import TestClient
import pytest

from app.main import create_app
from app.models.contracts import Speaker
from app.services.call_service import CallService


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


@pytest.mark.asyncio
@pytest.mark.parametrize("fault", ["stt_disconnect", "stt_reconnect", "buffer_replay", "duplicate_replay",
    "llm_timeout", "llm_malformed", "external_timeout", "external_rate_limit", "evidence_conflict",
    "evidence_unverified", "database_failure", "graph_failure", "frontend_disconnect"])
async def test_each_fault_executes_a_behavioral_recovery_scenario(fault):
    service = CallService()
    call_id = (await service.create_synthetic_call("07700 900123", "customer-1"))["call"]["id"]
    result = await service.run_fault_scenario(call_id, fault)
    snapshot = await service.snapshot(call_id)
    assert result["exercised"] is True
    assert result["observable"]
    assert snapshot.call["status"] == "connected"
    await service.close()
