import pytest
from app.models.contracts import CallStatus, ConversationState, Speaker, Utterance
from app.sessions.store import InMemorySessionStore


@pytest.mark.asyncio
async def test_snapshot_is_canonical_and_partial_updates_replace_in_place():
    store = InMemorySessionStore()
    session = await store.create(call_id="call-1", customer_id=None)
    partial_a = Utterance(id="partial-customer", call_id="call-1", speaker=Speaker.CUSTOMER,
        text="My budget", sequence=1, is_final=False, source_track="inbound_track")
    partial_b = partial_a.model_copy(update={"text": "My budget is £450,000"})
    await store.add_utterance(session.session_id, partial_a)
    await store.add_utterance(session.session_id, partial_b)
    snapshot = await store.snapshot(session.session_id)
    assert [item.text for item in snapshot.transcript] == ["My budget is £450,000"]
    assert snapshot.call["status"] == CallStatus.IDLE


@pytest.mark.asyncio
async def test_final_replaces_matching_partial_and_survives_snapshot_recovery():
    store = InMemorySessionStore()
    session = await store.create(call_id="call-1", customer_id="customer-1")
    partial = Utterance(id="partial-customer", call_id="call-1", speaker=Speaker.CUSTOMER,
        text="Saturday", sequence=1, is_final=False, source_track="inbound_track")
    final = Utterance(id="utt-1", call_id="call-1", speaker=Speaker.CUSTOMER,
        text="Saturday works", sequence=1, is_final=True, source_track="inbound_track")
    await store.add_utterance(session.session_id, partial)
    await store.add_utterance(session.session_id, final)
    await store.update_conversation(session.session_id, ConversationState(call_id="call-1", stage="progression"))
    snapshot = await store.snapshot(session.session_id)
    assert [item.id for item in snapshot.transcript] == ["utt-1"]
    assert snapshot.conversation_state.stage == "progression"
