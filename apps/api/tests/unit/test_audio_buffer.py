from app.streaming.buffer import AudioReplayBuffer


def test_replay_buffer_evicts_audio_older_than_three_seconds():
    buffer = AudioReplayBuffer(duration_ms=3000)
    for timestamp in (0, 1000, 2000, 3000, 4000):
        buffer.append(timestamp, f"a{timestamp}".encode())
    assert [chunk.timestamp_ms for chunk in buffer.replay()] == [1000, 2000, 3000, 4000]


def test_buffer_preserves_packet_order_when_timestamp_ties():
    buffer = AudioReplayBuffer(duration_ms=3000)
    buffer.append(10, b"first")
    buffer.append(10, b"second")
    assert [chunk.payload for chunk in buffer.replay()] == [b"first", b"second"]

