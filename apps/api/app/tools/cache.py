from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pydantic import BaseModel


class CacheEntry(BaseModel):
    cache_key: str
    value: dict
    source_ids: list[str]
    fetched_at: datetime
    expires_at: datetime


class ContextCache:
    TTLS = {"weather": timedelta(minutes=30), "market": timedelta(hours=6),
            "rates": timedelta(hours=6), "property": timedelta(days=30),
            "environment": timedelta(days=7), "planning": timedelta(days=7)}

    def __init__(self, clock: Callable[[], datetime] = lambda: datetime.now(UTC)) -> None:
        self._clock = clock
        self._values: dict[str, CacheEntry] = {}

    def put(self, key: str, value: dict, source_ids: list[str], topic: str) -> CacheEntry:
        now = self._clock()
        entry = CacheEntry(cache_key=key, value=value, source_ids=list(source_ids), fetched_at=now,
                           expires_at=now + self.TTLS.get(topic, timedelta(hours=1)))
        self._values[key] = entry
        return entry

    def get(self, key: str) -> CacheEntry | None:
        entry = self._values.get(key)
        if not entry or self._clock() >= entry.expires_at:
            self._values.pop(key, None)
            return None
        return entry.model_copy(deep=True)

