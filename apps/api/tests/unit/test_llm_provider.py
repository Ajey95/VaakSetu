import pytest
from app.llm.synthetic import SyntheticLLMProvider


@pytest.mark.asyncio
async def test_synthetic_provider_returns_validated_structured_output():
    result = await SyntheticLLMProvider().complete_structured("coach", {"stage": "discovery"}, {"next_move": str, "reason": str})
    assert result["next_move"]
    assert result["reason"]


@pytest.mark.asyncio
async def test_malformed_output_is_rejected_at_provider_boundary():
    with pytest.raises(ValueError, match="structured output"):
        await SyntheticLLMProvider(malformed=True).complete_structured("coach", {}, {"next_move": str})
