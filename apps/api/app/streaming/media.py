from dataclasses import dataclass
from enum import StrEnum

from app.models.contracts import Speaker


class PacketDecision(StrEnum):
    ACCEPT = "accept"
    GAP = "gap"
    DUPLICATE = "duplicate"
    OUT_OF_ORDER = "out_of_order"


@dataclass(frozen=True)
class MediaPacket:
    sequence: int
    track: str
    timestamp_ms: int
    payload: bytes


def map_twilio_track(track: str) -> Speaker:
    normalized = track.removesuffix("_track")
    if normalized == "inbound":
        return Speaker.CUSTOMER
    if normalized == "outbound":
        return Speaker.AGENT
    raise ValueError(f"Unsupported Twilio media track: {track}")


class MediaSequencer:
    def __init__(self) -> None:
        self._last_by_track: dict[str, int] = {}

    def accept(self, packet: MediaPacket) -> PacketDecision:
        previous = self._last_by_track.get(packet.track)
        if previous is None:
            self._last_by_track[packet.track] = packet.sequence
            return PacketDecision.ACCEPT
        if packet.sequence == previous:
            return PacketDecision.DUPLICATE
        if packet.sequence < previous:
            return PacketDecision.OUT_OF_ORDER
        self._last_by_track[packet.track] = packet.sequence
        if packet.sequence > previous + 1:
            return PacketDecision.GAP
        return PacketDecision.ACCEPT

