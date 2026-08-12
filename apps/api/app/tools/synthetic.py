from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from app.tools.base import ExternalTool, SourceResult, ToolResult


class SyntheticExternalTool(ExternalTool):
    def __init__(self, delay_seconds: float = 0, fail: bool = False) -> None:
        self.delay_seconds = delay_seconds
        self.fail = fail

    async def search(self, query: str, topic: str) -> ToolResult:
        if self.delay_seconds:
            await asyncio.sleep(self.delay_seconds)
        if self.fail:
            raise TimeoutError("Synthetic external provider timeout")
        now = datetime.now(UTC)
        return ToolResult(tool="synthetic_official_uk", query=query, topic=topic, results=[SourceResult(
            source_id="synthetic-uk-hpi", title="UK House Price Index (synthetic fixture)",
            url="https://www.gov.uk/government/collections/uk-house-price-index-reports",
            provider="synthetic", source_tier=1, retrieved_at=now, published_at=now,
            content="Manchester prices rose 3.1% year on year; the customer claim of a 10% fall is not supported.",
            structured_data={"annual_change_percent": 3.1}, confidence=1,
        )])

