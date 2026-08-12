from __future__ import annotations

import base64
from fastapi import WebSocket, WebSocketDisconnect
from app.streaming.media import MediaPacket, MediaSequencer, PacketDecision, map_twilio_track


async def media_socket(websocket: WebSocket, call_id: str) -> None:
    await websocket.accept()
    sequencer = MediaSequencer()
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
            # The provider-specific STT manager is attached by the real call lifecycle once credentials are configured.
            # Keeping this socket transport-only ensures packet faults cannot control the Twilio call.
            map_twilio_track(packet.track)
    except WebSocketDisconnect:
        pass

