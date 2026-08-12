from __future__ import annotations

import re
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pydantic import BaseModel, Field

from app.tools.base import SourceResult


class EvidenceEvaluation(BaseModel):
    claim: str
    status: str
    confidence: float = Field(ge=0, le=1)
    freshness: str
    safe_to_surface_as_fact: bool
    preferred_source_id: str | None = None
    conflicts: list[str] = Field(default_factory=list)


class EvidenceAgent:
    def __init__(self, clock: Callable[[], datetime] = lambda: datetime.now(UTC)) -> None:
        self.clock = clock

    def evaluate(self, claim: str, sources: list[SourceResult]) -> EvidenceEvaluation:
        if not sources:
            return EvidenceEvaluation(claim=claim, status="unverified", confidence=0, freshness="unknown",
                                      safe_to_surface_as_fact=False)
        ordered = sorted(sources, key=lambda source: (source.source_tier, -(source.confidence or 0)))
        claim_lower = claim.lower()
        claim_direction = self._direction(claim_lower)
        directions = {source.source_id: self._direction(source.content.lower()) for source in ordered}
        non_neutral = {direction for direction in directions.values() if direction}
        if len(non_neutral) > 1:
            return EvidenceEvaluation(claim=claim, status="conflicting", confidence=.35, freshness="current",
                                      safe_to_surface_as_fact=False, preferred_source_id=ordered[0].source_id,
                                      conflicts=[source.source_id for source in ordered])
        preferred = ordered[0]
        published = preferred.published_at or preferred.retrieved_at
        age = self.clock() - published
        freshness = "current" if age <= timedelta(days=30) else "recent" if age <= timedelta(days=365) else "stale"
        content = preferred.content.lower()
        numbers = re.findall(r"-?\d+(?:\.\d+)?%", claim_lower)
        exact_number = any(number in content for number in numbers)
        status = "supported" if (claim_direction and claim_direction == directions[preferred.source_id] and (not numbers or exact_number)) else "partial"
        confidence = .95 if status == "supported" and preferred.source_tier == 1 else .72 if status == "partial" else .6
        return EvidenceEvaluation(claim=claim, status=status, confidence=confidence, freshness=freshness,
                                  safe_to_surface_as_fact=status in {"supported", "partial"} and freshness != "stale",
                                  preferred_source_id=preferred.source_id)

    @staticmethod
    def _direction(text: str) -> str | None:
        if re.search(r"\b(rose|risen|increased|up)\b", text):
            return "up"
        if re.search(r"\b(fell|fallen|dropped|decreased|down)\b", text):
            return "down"
        return None

