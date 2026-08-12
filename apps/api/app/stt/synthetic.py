from app.models.contracts import Speaker
from app.stt.base import STTProvider, STTResult


class SyntheticSTTProvider(STTProvider):
    def __init__(self, speaker: Speaker) -> None:
        super().__init__(speaker)
        self.connected = False
        self.received_audio: list[bytes] = []

    async def connect(self) -> None:
        self.connected = True

    async def send_audio(self, audio: bytes) -> None:
        if not self.connected:
            raise ConnectionError("Synthetic STT is disconnected")
        self.received_audio.append(audio)

    async def reconnect(self) -> None:
        self.connected = True

    async def close(self) -> None:
        self.connected = False

    async def inject(self, result: STTResult) -> None:
        await self.emit(result)

