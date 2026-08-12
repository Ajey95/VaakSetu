from app.agents.summary_agent import SummaryAgent
from app.models.contracts import ConversationState, Evidence
from datetime import UTC, datetime


def test_summary_keeps_customer_facts_evidence_claims_and_inference_separate():
    state = ConversationState(call_id="call-1", customer={"budget": {"value": 450000, "source": "customer"}},
        signals=[{"type": "high_intent", "evidence": "six-week timeline"}], objections=[{"type": "price"}],
        commitments=[{"type": "viewing", "detail": "Saturday"}],
        external_claims=[{"claim": "prices fell 10%", "status": "customer_said_unverified"}])
    evidence = [Evidence(id="ev-1", claim="regional prices changed", source_title="UK House Price Index",
        retrieved_at=datetime.now(UTC), support_status="partial", confidence=.8, freshness="current",
        safe_to_surface_as_fact=True)]
    summary = SummaryAgent().summarize(state, evidence, ["Buyer appears price-sensitive"])
    assert summary.customer_facts == ["Budget: £450,000"]
    assert summary.external_verified_context[0]["source"] == "UK House Price Index"
    assert summary.unverified_claims == ["prices fell 10%"]
    assert summary.ai_inferences == ["Buyer appears price-sensitive"]
    assert summary.commitments == ["Viewing: Saturday"]

