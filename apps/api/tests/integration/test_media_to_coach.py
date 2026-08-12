import time
from fastapi.testclient import TestClient
from app.main import create_app


def test_ui_websocket_reconnect_starts_with_full_snapshot_and_receives_live_events():
    with TestClient(create_app()) as client:
        call = client.post("/demo/calls", json={"phone_number": "07700 900123"}).json()
        call_id = call["call"]["id"]
        with client.websocket_connect(f"/ws/ui/{call_id}") as socket:
            initial = socket.receive_json()
            assert initial["type"] == "session.snapshot"
            client.post(f"/demo/calls/{call_id}/utterances", json={"speaker": "customer",
                "text": "The asking price feels too high", "is_final": True})
            event = socket.receive_json()
            assert event["type"] == "stt.final"
            coach = socket.receive_json()
            assert coach["type"] == "coach.fast.ready"
            assert "price concern" in coach["payload"]["next_move"].lower()
        with client.websocket_connect(f"/ws/ui/{call_id}") as reconnected:
            snapshot = reconnected.receive_json()
            assert len(snapshot["payload"]["transcript"]) == 1
            assert snapshot["payload"]["conversation_state"]["stage"] == "objection_handling"


def test_external_lookup_refines_after_fast_coach_without_changing_speaker_labels():
    with TestClient(create_app()) as client:
        call_id = client.post("/demo/calls", json={"phone_number": "07700 900123"}).json()["call"]["id"]
        client.post(f"/demo/calls/{call_id}/utterances", json={"speaker": "agent", "text": "What budget are you working to?", "is_final": True})
        client.post(f"/demo/calls/{call_id}/utterances", json={"speaker": "customer", "text": "Prices in Manchester fell 10%", "is_final": True})
        time.sleep(.05)
        snapshot = client.get(f"/calls/{call_id}").json()
        assert [item["speaker"] for item in snapshot["transcript"]] == ["agent", "customer"]
        assert snapshot["evidence"][0]["source_title"].endswith("(synthetic fixture)")
        assert snapshot["recommendations"][0]["type"] == "fast"
        assert snapshot["recommendations"][-1]["type"] == "deep"

