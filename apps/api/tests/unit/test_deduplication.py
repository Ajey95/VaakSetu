from app.conversation.deduplication import FinalTranscriptDeduplicator
from app.models.contracts import Speaker, Utterance


def item(identifier: str, text: str, speaker: Speaker, sequence: int) -> Utterance:
    return Utterance(id=identifier, call_id="call-1", speaker=speaker, text=text, sequence=sequence,
                     source_track="inbound_track" if speaker is Speaker.CUSTOMER else "outbound_track")


def test_replayed_same_track_overlap_is_rejected():
    deduper = FinalTranscriptDeduplicator()
    assert deduper.accept(item("a", "My budget is four hundred thousand", Speaker.CUSTOMER, 10)) is True
    assert deduper.accept(item("b", "budget is four hundred thousand", Speaker.CUSTOMER, 11)) is False


def test_identical_words_from_other_speaker_are_preserved():
    deduper = FinalTranscriptDeduplicator()
    assert deduper.accept(item("a", "Saturday works", Speaker.CUSTOMER, 10)) is True
    assert deduper.accept(item("b", "Saturday works", Speaker.AGENT, 11)) is True


def test_old_repeated_phrase_outside_replay_window_is_preserved():
    deduper = FinalTranscriptDeduplicator(max_sequence_gap=3)
    assert deduper.accept(item("a", "Thank you", Speaker.CUSTOMER, 1)) is True
    assert deduper.accept(item("b", "Thank you", Speaker.CUSTOMER, 10)) is True

