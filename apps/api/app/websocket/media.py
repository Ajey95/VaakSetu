from __future__ import annotations

import base64
from fastapi import WebSocket, WebSocketDisconnect
from app.streaming.media import MediaPacket, MediaSequencer, PacketDecision, map_twilio_track


async def media_socket(websocket: WebSocket, call_id: str) -> None:
    if call_id not in websocket.app.state.calls._call_sessions:
        await websocket.close(code=4404)
        return
    await websocket.accept()
    sequencer = MediaSequencer()
    try:
        manager = await websocket.app.state.calls.start_stt(call_id)
    except Exception:
        manager = None
    try:
        while True:
            message = await websocket.receive_json()
            if message.get("event") == "stop":
                break
            if message.get("event") != "media":
                continue
            media = message["media"]
            packet = MediaPacket(sequence=int(message.get("sequenceNumber", media.get("chunk", 0))),
                track=media["track"], timestamp_ms=int(media.get("timestamp", 0)), payload=base64.b64decode(media["payload"]))
            decision = sequencer.accept(packet)
            if decision in {PacketDecision.DUPLICATE, PacketDecision.OUT_OF_ORDER}:
                continue
            if decision is PacketDecision.GAP:
                websocket.app.state.calls.record_media_gap(call_id)
            speaker = map_twilio_track(packet.track)
            if manager:
                try:
                    await manager.send_audio(speaker, packet.payload, packet.sequence, packet.timestamp_ms)
                except Exception:
                    try:
                        websocket.app.state.calls.record_stt_reconnect(call_id)
                        await manager.reconnect(speaker)
                    except Exception:
                        pass
    except WebSocketDisconnect:
        pass
    finally:
        await websocket.app.state.calls.stop_stt(call_id)
