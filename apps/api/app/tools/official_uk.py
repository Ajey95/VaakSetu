from __future__ import annotations

import httpx
from datetime import UTC, datetime

from app.tools.base import ExternalTool, SourceResult, ToolResult


class OfficialUKTool(ExternalTool):
    """Small official-source adapter; unsupported topics abstain instead of web guessing."""

    async def search(self, query: str, topic: str) -> ToolResult:
        if topic != "market":
            return ToolResult(tool="official_uk", query=query, topic=topic, results=[])
        url = "https://landregistry.data.gov.uk/app/ukhpi"
        async with httpx.AsyncClient(timeout=2.5, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
        return ToolResult(tool="official_uk", query=query, topic=topic, results=[SourceResult(
            source_id="uk-hpi", title="UK House Price Index", url=url, provider="HM Land Registry",
            source_tier=1, retrieved_at=datetime.now(UTC), content=response.text[:5000])])

