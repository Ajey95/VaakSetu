from app.models.contracts import Speaker, Utterance


class FinalTranscriptDeduplicator:
    def __init__(self, max_sequence_gap: int = 8) -> None:
        self.max_sequence_gap = max_sequence_gap
        self._last: dict[Speaker, tuple[int, str]] = {}

    def accept(self, utterance: Utterance) -> bool:
        normalized = " ".join(utterance.text.lower().split())
        previous = self._last.get(utterance.speaker)
        if previous and utterance.sequence - previous[0] <= self.max_sequence_gap:
            prior = previous[1]
            if normalized == prior or normalized in prior or prior in normalized:
                return False
            previous_words = prior.split()
            current_words = normalized.split()
            overlap = min(len(previous_words), len(current_words))
            for size in range(overlap, 2, -1):
                if previous_words[-size:] == current_words[:size]:
                    return False
        self._last[utterance.speaker] = (utterance.sequence, normalized)
        return True

