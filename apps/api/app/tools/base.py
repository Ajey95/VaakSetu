from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from pydantic import BaseModel, Field


class SourceResult(BaseModel):
    source_id: str
    title: str
    url: str | None = None
    provider: str
    source_tier: int = Field(ge=1, le=5)
    retrieved_at: datetime
    published_at: datetime | None = None
    content: str
    structured_data: dict = Field(default_factory=dict)
    confidence: float | None = Field(default=None, ge=0, le=1)


class ToolResult(BaseModel):
    tool: str
    query: str
    topic: str
    results: list[SourceResult]


class ExternalTool(ABC):
    @abstractmethod
    async def search(self, query: str, topic: str) -> ToolResult: ...

