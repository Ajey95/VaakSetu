from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    async def complete_structured(self, purpose: str, payload: dict, schema: dict[str, type]) -> dict: ...


def validate_structured_output(value: object, schema: dict[str, type]) -> dict:
    if not isinstance(value, dict) or any(key not in value or not isinstance(value[key], expected) for key, expected in schema.items()):
        raise ValueError("LLM returned invalid structured output")
    return value

