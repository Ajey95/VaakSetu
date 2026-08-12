from uuid import uuid4
from app.llm.base import LLMProvider
from app.models.contracts import ConversationState, Evidence, Recommendation


class DeepCoach:
    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    async def recommend(self, state: ConversationState, fast: Recommendation, evidence: list[Evidence]) -> Recommendation:
        output = await self.llm.complete_structured("deep_coach", {"state": state.model_dump(mode="json"),
            "fast_recommendation": fast.model_dump(mode="json"), "evidence": [item.model_dump(mode="json") for item in evidence]},
            {"next_move": str, "reason": str})
        return Recommendation(id=f"rec_{uuid4().hex[:10]}", type="deep", next_move=output["next_move"],
            reason=output["reason"], confidence="high", lifecycle="refined", evidence_ids=[item.id for item in evidence])

