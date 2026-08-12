from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class AudioChunk:
    timestamp_ms: int
    payload: bytes


class AudioReplayBuffer:
    def __init__(self, duration_ms: int = 3000) -> None:
        self.duration_ms = duration_ms
        self._chunks: deque[AudioChunk] = deque()

    def append(self, timestamp_ms: int, payload: bytes) -> None:
        self._chunks.append(AudioChunk(timestamp_ms, payload))
        cutoff = timestamp_ms - self.duration_ms
        while self._chunks and self._chunks[0].timestamp_ms < cutoff:
            self._chunks.popleft()

    def replay(self) -> list[AudioChunk]:
        return list(self._chunks)

