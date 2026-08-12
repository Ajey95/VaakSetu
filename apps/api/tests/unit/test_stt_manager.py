import pytest

from app.models.contracts import HealthState, Speaker
from app.stt.base import STTResult
from app.stt.manager import STTManager
from app.stt.synthetic import SyntheticSTTProvider


@pytest.mark.asyncio
async def test_manager_owns_independent_provider_per_speaker():
    events = []
    manager = STTManager(lambda speaker: SyntheticSTTProvider(speaker), events.append)
    await manager.start()
    await manager.send_audio(Speaker.CUSTOMER, b"customer", sequence=1, timestamp_ms=10)
    await manager.send_audio(Speaker.AGENT, b"agent", sequence=1, timestamp_ms=10)
    await manager.inject_synthetic(Speaker.CUSTOMER, STTResult(text="hello", is_final=True, confidence=.99))
    await manager.inject_synthetic(Speaker.AGENT, STTResult(text="hi", is_final=True, confidence=.98))
    assert [(event.speaker, event.text) for event in events if event.is_final] == [
        (Speaker.CUSTOMER, "hello"), (Speaker.AGENT, "hi")]


@pytest.mark.asyncio
async def test_disconnect_reconnects_replays_buffer_and_never_controls_call():
    events = []
    manager = STTManager(lambda speaker: SyntheticSTTProvider(speaker), events.append)
    await manager.start()
    await manager.send_audio(Speaker.CUSTOMER, b"one", sequence=1, timestamp_ms=10)
    await manager.send_audio(Speaker.CUSTOMER, b"two", sequence=2, timestamp_ms=20)
    await manager.reconnect(Speaker.CUSTOMER)
    provider = manager.provider(Speaker.CUSTOMER)
    assert manager.health[Speaker.CUSTOMER] is HealthState.LIVE
    assert provider.received_audio[-2:] == [b"one", b"two"]
    assert not hasattr(manager, "hang_up")


@pytest.mark.asyncio
async def test_replayed_final_is_deduplicated_by_speaker():
    events = []
    manager = STTManager(lambda speaker: SyntheticSTTProvider(speaker), events.append)
    await manager.start()
    result = STTResult(text="My budget is four hundred thousand", is_final=True, confidence=.9, sequence=7)
    await manager.inject_synthetic(Speaker.CUSTOMER, result)
    await manager.inject_synthetic(Speaker.CUSTOMER, result.model_copy(update={"text": "budget is four hundred thousand", "sequence": 8}))
    assert [event.text for event in events] == ["My budget is four hundred thousand"]
