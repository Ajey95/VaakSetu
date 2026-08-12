from __future__ import annotations

from collections.abc import Callable
from uuid import uuid4

from app.conversation.deduplication import FinalTranscriptDeduplicator
from app.models.contracts import HealthState, Speaker, Utterance
from app.streaming.buffer import AudioReplayBuffer
from app.stt.base import STTProvider, STTResult
from app.stt.synthetic import SyntheticSTTProvider


class STTManager:
    def __init__(self, factory: Callable[[Speaker], STTProvider], publish: Callable[[Utterance], None], call_id: str = "active") -> None:
        self._providers = {speaker: factory(speaker) for speaker in Speaker}
        self._publish = publish
        self.call_id = call_id
        self._buffers = {speaker: AudioReplayBuffer(3000) for speaker in Speaker}
        self._deduper = FinalTranscriptDeduplicator()
        self.health = {speaker: HealthState.CONNECTING for speaker in Speaker}
        for speaker, provider in self._providers.items():
            provider.on_result(self._handler_for(speaker))

    def provider(self, speaker: Speaker) -> STTProvider:
        return self._providers[speaker]

    async def start(self) -> None:
        for speaker, provider in self._providers.items():
            await provider.connect()
            self.health[speaker] = HealthState.LIVE

    async def send_audio(self, speaker: Speaker, audio: bytes, sequence: int, timestamp_ms: int) -> None:
        self._buffers[speaker].append(timestamp_ms, audio)
        await self._providers[speaker].send_audio(audio)

    async def reconnect(self, speaker: Speaker) -> None:
        self.health[speaker] = HealthState.RECONNECTING
        await self._providers[speaker].reconnect()
        for chunk in self._buffers[speaker].replay():
            await self._providers[speaker].send_audio(chunk.payload)
        self.health[speaker] = HealthState.LIVE

    async def inject_synthetic(self, speaker: Speaker, result: STTResult) -> None:
        provider = self._providers[speaker]
        if not isinstance(provider, SyntheticSTTProvider):
            raise TypeError("Synthetic injection is available only for the synthetic provider")
        await provider.inject(result)

    async def close(self) -> None:
        for speaker, provider in self._providers.items():
            await provider.close()
            self.health[speaker] = HealthState.UNAVAILABLE

    def _handler_for(self, speaker: Speaker):
        async def handler(result: STTResult) -> None:
            sequence = result.sequence or 0
            utterance = Utterance(id=f"utt_{uuid4().hex[:12]}" if result.is_final else f"partial_{speaker.value}",
                call_id=self.call_id, speaker=speaker, text=result.text, sequence=sequence, is_final=result.is_final,
                confidence=result.confidence, source_track="inbound_track" if speaker is Speaker.CUSTOMER else "outbound_track")
            if result.is_final and not self._deduper.accept(utterance):
                return
            self._publish(utterance)
        return handler
