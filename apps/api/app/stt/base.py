from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from pydantic import BaseModel, Field

from app.models.contracts import Speaker


class STTResult(BaseModel):
    text: str = Field(min_length=1)
    is_final: bool
    confidence: float | None = Field(default=None, ge=0, le=1)
    sequence: int = 0


ResultHandler = Callable[[STTResult], Awaitable[None]]


class STTProvider(ABC):
    def __init__(self, speaker: Speaker) -> None:
        self.speaker = speaker
        self._handler: ResultHandler | None = None

    def on_result(self, handler: ResultHandler) -> None:
        self._handler = handler

    async def emit(self, result: STTResult) -> None:
        if self._handler:
            await self._handler(result)

    @abstractmethod
    async def connect(self) -> None: ...

    @abstractmethod
    async def send_audio(self, audio: bytes) -> None: ...

    @abstractmethod
    async def reconnect(self) -> None: ...

    @abstractmethod
    async def close(self) -> None: ...

