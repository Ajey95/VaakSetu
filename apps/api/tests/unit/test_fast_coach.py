from app.agents.fast_coach import FastCoach
from app.models.contracts import ConversationState


def test_price_objection_recommendation_is_specific_to_known_context():
    state = ConversationState(call_id="call-1", stage="objection_handling", temperature="warm",
        customer={"mortgage_approval": {"value": "approved"}}, objections=[{"type": "price"}])
    recommendation = FastCoach().recommend(state, trigger="price_objection")
    assert recommendation.next_move == "Acknowledge the price concern, confirm their approved mortgage position, then offer a specific viewing time."
    assert "price objection" in recommendation.reason.lower()
    assert recommendation.confidence == "high"


def test_missing_mortgage_after_timeline_mention_prompts_one_concrete_question():
    state = ConversationState(call_id="call-1", customer={"timeline": {"value": "6 weeks"}})
    recommendation = FastCoach().recommend(state, trigger="timeline_mentioned")
    assert recommendation.next_move == "They need to move in 6 weeks; ask whether they have a mortgage agreement in principle before proposing a viewing."

