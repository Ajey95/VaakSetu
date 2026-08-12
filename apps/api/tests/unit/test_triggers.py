from app.conversation.triggers import TriggerType, detect_triggers
from app.models.contracts import ConversationState, Speaker, Utterance


def test_final_price_objection_triggers_high_priority_coaching_and_domain_knowledge():
    state = ConversationState(call_id="call-1", objections=[{"type": "price", "utterance_id": "utt-1"}])
    triggers = detect_triggers(state, Utterance(id="utt-1", call_id="call-1", speaker=Speaker.CUSTOMER,
        text="It is overpriced", sequence=1, source_track="inbound_track"))
    by_type = {trigger.type: trigger for trigger in triggers}
    assert by_type[TriggerType.PRICE_OBJECTION].priority == 100
    assert by_type[TriggerType.PRICE_OBJECTION].requires_domain_retrieval is True
    assert by_type[TriggerType.PRICE_OBJECTION].requires_external_context is False


def test_market_claim_requests_external_context_without_blocking_fast_coach():
    state = ConversationState(call_id="call-1", external_claims=[{"utterance_id": "utt-2", "topic": "market"}])
    utterance = Utterance(id="utt-2", call_id="call-1", speaker=Speaker.CUSTOMER,
        text="Prices fell ten percent", sequence=2, source_track="inbound_track")
    trigger = detect_triggers(state, utterance)[0]
    assert trigger.type is TriggerType.MARKET_CLAIM
    assert trigger.requires_external_context is True
    assert trigger.fast_coach_allowed is True


def test_partial_transcript_never_triggers_intelligence():
    state = ConversationState(call_id="call-1")
    utterance = Utterance(id="partial", call_id="call-1", speaker=Speaker.CUSTOMER,
        text="I think", sequence=3, source_track="inbound_track", is_final=False)
    assert detect_triggers(state, utterance) == []

