import pytest
from app.llm.synthetic import SyntheticLLMProvider
from app.llm.resilient import ResilientLLMProvider
from app.llm.base import LLMProvider


class FlakyLLM(LLMProvider):
    def __init__(self, failures: int): self.failures = failures; self.attempts = 0
    async def complete_structured(self, purpose, payload, schema):
        self.attempts += 1
        if self.attempts <= self.failures: raise TimeoutError("retryable")
        return {"next_move":"Recovered", "reason":"Bounded retry succeeded"}


@pytest.mark.asyncio
async def test_synthetic_provider_returns_validated_structured_output():
    result = await SyntheticLLMProvider().complete_structured("coach", {"stage": "discovery"}, {"next_move": str, "reason": str})
    assert result["next_move"]
    assert result["reason"]


@pytest.mark.asyncio
async def test_malformed_output_is_rejected_at_provider_boundary():
    with pytest.raises(ValueError, match="structured output"):
        await SyntheticLLMProvider(malformed=True).complete_structured("coach", {}, {"next_move": str})


@pytest.mark.asyncio
async def test_llm_retries_once_then_returns_validated_result():
    inner = FlakyLLM(failures=1)
    result = await ResilientLLMProvider(inner, max_attempts=2, backoff_seconds=0).complete_structured(
        "coach", {}, {"next_move":str, "reason":str})
    assert result["next_move"] == "Recovered"
    assert inner.attempts == 2


@pytest.mark.asyncio
async def test_llm_retry_is_bounded_and_raises_after_final_attempt():
    inner = FlakyLLM(failures=3)
    with pytest.raises(TimeoutError):
        await ResilientLLMProvider(inner, max_attempts=2, backoff_seconds=0).complete_structured(
            "coach", {}, {"next_move":str, "reason":str})
    assert inner.attempts == 2
