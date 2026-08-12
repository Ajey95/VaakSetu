from __future__ import annotations

import hashlib

from app.tools.base import ExternalTool, ToolResult
from app.tools.cache import ContextCache


class CachedExternalTool(ExternalTool):
    def __init__(self, inner: ExternalTool, cache: ContextCache) -> None:
        self.inner = inner
        self.cache = cache
        self.last_cache_hit = False

    async def search(self, query: str, topic: str) -> ToolResult:
        digest = hashlib.sha256(query.strip().lower().encode("utf-8")).hexdigest()[:24]
        key = f"{topic}:{digest}"
        cached = self.cache.get(key)
        if cached:
            self.last_cache_hit = True
            return ToolResult.model_validate(cached.value)
        self.last_cache_hit = False
        result = await self.inner.search(query, topic)
        self.cache.put(key, result.model_dump(mode="json"),
                       [item.source_id for item in result.results], topic=topic)
        return result
