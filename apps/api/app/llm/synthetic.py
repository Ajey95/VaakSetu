from app.llm.base import LLMProvider, validate_structured_output


class SyntheticLLMProvider(LLMProvider):
    def __init__(self, malformed: bool = False) -> None:
        self.malformed = malformed

    async def complete_structured(self, purpose: str, payload: dict, schema: dict[str, type]) -> dict:
        value = {"unexpected": True} if self.malformed else {
            "next_move": "Use the validated market context to acknowledge the concern without repeating the customer's claim as fact, then offer a Saturday viewing.",
            "reason": "Official context does not support a ten-percent fall, so qualify the claim while preserving momentum.",
        }
        return validate_structured_output(value, schema)

