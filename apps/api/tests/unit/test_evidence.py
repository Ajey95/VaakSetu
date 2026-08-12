from datetime import UTC, datetime, timedelta
from app.agents.evidence_agent import EvidenceAgent
from app.tools.base import SourceResult


NOW = datetime(2026, 8, 12, tzinfo=UTC)


def source(identifier: str, tier: int, content: str, days_old: int = 0) -> SourceResult:
    return SourceResult(source_id=identifier, title=identifier, url=f"https://example.gov/{identifier}",
        provider="test", source_tier=tier, retrieved_at=NOW, published_at=NOW - timedelta(days=days_old), content=content)


def test_official_supporting_source_wins_over_general_web():
    result = EvidenceAgent(clock=lambda: NOW).evaluate("Manchester prices rose 3.1%", [
        source("blog", 4, "Manchester prices rose 5%"),
        source("uk-hpi", 1, "Manchester prices rose 3.1% year on year"),
    ])
    assert result.status == "supported"
    assert result.preferred_source_id == "uk-hpi"
    assert result.safe_to_surface_as_fact is True


def test_conflicting_sources_are_never_surfaced_as_fact():
    result = EvidenceAgent(clock=lambda: NOW).evaluate("Prices fell 10%", [
        source("official-a", 1, "Prices rose 3%"), source("official-b", 1, "Prices fell 2%")])
    assert result.status == "conflicting"
    assert result.safe_to_surface_as_fact is False
    assert len(result.conflicts) == 2


def test_no_reliable_source_returns_explicit_unverified_state():
    result = EvidenceAgent(clock=lambda: NOW).evaluate("This area always floods", [])
    assert result.status == "unverified"
    assert result.confidence == 0
    assert result.preferred_source_id is None

