from fastapi import WebSocket, WebSocketDisconnect


async def ui_socket(websocket: WebSocket, call_id: str) -> None:
    await websocket.accept()
    calls = websocket.app.state.calls
    try:
        snapshot = await calls.snapshot(call_id)
    except KeyError:
        await websocket.close(code=4404)
        return
    await websocket.send_json({"type": "session.snapshot", "event_id": "snapshot", "trace_id": f"trace_{call_id}",
        "call_id": call_id, "session_id": snapshot.call["session_id"], "timestamp": __import__("datetime").datetime.now(__import__("datetime").UTC).isoformat(),
        "payload": snapshot.model_dump(mode="json")})
    queue = calls.subscribe(call_id)
    try:
        while True:
            await websocket.send_json(await queue.get())
    except (WebSocketDisconnect, RuntimeError):
        pass
    finally:
        calls.unsubscribe(call_id, queue)

