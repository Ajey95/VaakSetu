from app.conversation.reducer import apply_final_utterance
from app.models.contracts import ConversationState, Speaker, Utterance


def utterance(text: str, *, speaker: Speaker = Speaker.CUSTOMER, sequence: int = 1, final: bool = True) -> Utterance:
    return Utterance(id=f"utt-{sequence}", call_id="call-1", speaker=speaker, text=text,
                     sequence=sequence, is_final=final, source_track="inbound_track")


def test_partial_transcript_cannot_mutate_durable_state():
    state = ConversationState(call_id="call-1")
    update = apply_final_utterance(state, utterance("My budget is £450,000", final=False))
    assert update.state.customer == {}
    assert update.changes == []


def test_extracts_buyer_profile_with_transcript_provenance():
    state = ConversationState(call_id="call-1")
    update = apply_final_utterance(
        state,
        utterance("I'm a buyer looking in Manchester city centre for 2 bedrooms. My budget is £450,000, mortgage approved, moving in six weeks."),
    )
    customer = update.state.customer
    assert update.state.call_type == "buyer"
    assert customer["budget"]["value"] == 450000
    assert customer["budget"]["utterance_id"] == "utt-1"
    assert customer["mortgage_approval"]["value"] == "approved"
    assert customer["bedrooms"]["value"] == 2
    assert customer["timeline"]["value"] == "6 weeks"
    assert customer["location_preferences"][0]["value"] == "Manchester city centre"


def test_price_objection_changes_stage_and_invalidates_visible_recommendation():
    state = ConversationState(
        call_id="call-1", stage="discovery",
        current_recommendation={"id": "rec-1", "lifecycle": "visible", "next_move": "Ask about budget"},
    )
    update = apply_final_utterance(state, utterance("The asking price feels too high and overpriced."))
    assert update.state.stage == "objection_handling"
    assert update.state.objections[-1]["type"] == "price"
    assert update.state.current_recommendation["lifecycle"] == "stale"
    assert "stage_changed" in update.invalidation_reasons


def test_vendor_fee_objection_and_instruction_signal_are_distinct():
    state = ConversationState(call_id="call-1", call_type="vendor")
    update = apply_final_utterance(state, utterance("Your agency fee is too high, but I am ready to instruct you if we agree."))
    assert update.state.objections[-1]["type"] == "fees"
    assert any(item["type"] == "instruction_ready" for item in update.state.signals)


def test_commitment_is_captured_and_moves_to_progression():
    state = ConversationState(call_id="call-1", stage="discovery")
    update = apply_final_utterance(state, utterance("Yes, let's book a Saturday viewing at 10."))
    assert update.state.stage == "progression"
    assert update.state.commitments[-1]["type"] == "viewing"


def test_financial_and_personal_constraints_are_marked_sensitive():
    state = ConversationState(call_id="call-1")
    update = apply_final_utterance(state, utterance("I only have a £30,000 deposit and must move before my divorce completes."))
    assert {item["type"] for item in update.state.sensitive_items} == {"financial_position", "personal_deadline"}


def test_external_market_claim_is_not_promoted_to_fact():
    state = ConversationState(call_id="call-1")
    update = apply_final_utterance(state, utterance("Prices around Manchester have fallen 10% this year."))
    assert update.state.external_claims[-1]["status"] == "customer_said_unverified"
    assert "market" in update.state.external_claims[-1]["topic"]
    assert "market_change" not in update.state.customer


def test_natural_mortgage_and_flood_phrasing_still_produce_typed_state():
    state = ConversationState(call_id="call-1")
    mortgage = apply_final_utterance(state, utterance("My mortgage is approved"))
    flood = apply_final_utterance(mortgage.state, utterance("I am worried this area floods", sequence=2))
    assert mortgage.state.customer["mortgage_approval"]["value"] == "approved"
    assert flood.state.external_claims[-1]["topic"] == "environment"
