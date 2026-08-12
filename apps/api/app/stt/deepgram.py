from __future__ import annotations

import asyncio
import json
from urllib.parse import urlencode

from websockets.asyncio.client import connect

from app.models.contracts import Speaker
from app.stt.base import STTProvider, STTResult


class DeepgramSTTProvider(STTProvider):
    def __init__(self, speaker: Speaker, api_key: str, model: str = "nova-3") -> None:
        super().__init__(speaker)
        self.api_key = api_key
        self.model = model
        self._socket = None
        self._receive_task: asyncio.Task | None = None
        self._keepalive_task: asyncio.Task | None = None
        self._sequence = 0

    async def connect(self) -> None:
        query = urlencode({"model": self.model, "encoding": "mulaw", "sample_rate": 8000,
                           "channels": 1, "interim_results": "true", "smart_format": "true",
                           "endpointing": 300})
        self._socket = await connect(f"wss://api.deepgram.com/v1/listen?{query}",
                                     additional_headers={"Authorization": f"Token {self.api_key}"})
        self._receive_task = asyncio.create_task(self._receive())
        self._keepalive_task = asyncio.create_task(self._keepalive())

    async def send_audio(self, audio: bytes) -> None:
        if not self._socket:
            raise ConnectionError("Deepgram STT is disconnected")
        await self._socket.send(audio)

    async def reconnect(self) -> None:
        await self.close()
        await self.connect()

    async def close(self) -> None:
        for task in (self._keepalive_task, self._receive_task):
            if task:
                task.cancel()
        if self._socket:
            try:
                await self._socket.send(json.dumps({"type": "CloseStream"}))
                await self._socket.close()
            except Exception:
                pass
        self._socket = None

    async def _keepalive(self) -> None:
        while self._socket:
            await asyncio.sleep(8)
            await self._socket.send(json.dumps({"type": "KeepAlive"}))

    async def _receive(self) -> None:
        async for message in self._socket:
            data = json.loads(message)
            if data.get("type") != "Results":
                continue
            alternatives = data.get("channel", {}).get("alternatives", [])
            if not alternatives or not alternatives[0].get("transcript", "").strip():
                continue
            self._sequence += 1
            await self.emit(STTResult(text=alternatives[0]["transcript"].strip(), is_final=bool(data.get("is_final")),
                                      confidence=alternatives[0].get("confidence"), sequence=self._sequence))

