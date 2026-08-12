from __future__ import annotations

import asyncio

from app.llm.base import LLMProvider


class ResilientLLMProvider(LLMProvider):
    def __init__(self, inner: LLMProvider, max_attempts: int = 2, backoff_seconds: float = .05) -> None:
        self.inner = inner
        self.max_attempts = max_attempts
        self.backoff_seconds = backoff_seconds

    async def complete_structured(self, purpose: str, payload: dict, schema: dict[str, type]) -> dict:
        for attempt in range(self.max_attempts):
            try:
                return await self.inner.complete_structured(purpose, payload, schema)
            except (TimeoutError, ConnectionError):
                if attempt + 1 == self.max_attempts:
                    raise
                await asyncio.sleep(self.backoff_seconds * (attempt + 1))
        raise RuntimeError("unreachable")
