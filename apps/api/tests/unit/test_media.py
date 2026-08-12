from app.models.contracts import Speaker
from app.streaming.media import MediaPacket, MediaSequencer, PacketDecision, map_twilio_track


def test_twilio_track_mapping_is_stable_for_outbound_browser_call():
    assert map_twilio_track("inbound") is Speaker.CUSTOMER
    assert map_twilio_track("inbound_track") is Speaker.CUSTOMER
    assert map_twilio_track("outbound") is Speaker.AGENT
    assert map_twilio_track("outbound_track") is Speaker.AGENT


def test_media_sequencer_reports_duplicate_gap_and_out_of_order_without_throwing():
    sequencer = MediaSequencer()
    packet = lambda seq: MediaPacket(sequence=seq, track="inbound", timestamp_ms=seq * 20, payload=b"audio")
    assert sequencer.accept(packet(1)) is PacketDecision.ACCEPT
    assert sequencer.accept(packet(1)) is PacketDecision.DUPLICATE
    assert sequencer.accept(packet(4)) is PacketDecision.GAP
    assert sequencer.accept(packet(3)) is PacketDecision.OUT_OF_ORDER
    assert sequencer.accept(packet(5)) is PacketDecision.ACCEPT

