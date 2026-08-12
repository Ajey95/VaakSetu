from __future__ import annotations

import httpx
from app.llm.base import LLMProvider, validate_structured_output


class OpenAICompatibleLLMProvider(LLMProvider):
    def __init__(self, api_key: str, model: str, base_url: str = "https://api.openai.com/v1") -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    async def complete_structured(self, purpose: str, payload: dict, schema: dict[str, type]) -> dict:
        response_schema = {"type": "object", "properties": {key: {"type": "string"} for key in schema},
                           "required": list(schema), "additionalProperties": False}
        request = {"model": self.model, "input": [{"role": "system", "content": [{"type": "input_text",
            "text": "Return specific real-estate coaching. Never invent external facts; abstain when evidence is unverified."}]},
            {"role": "user", "content": [{"type": "input_text", "text": str(payload)}]}],
            "text": {"format": {"type": "json_schema", "name": purpose, "strict": True, "schema": response_schema}}}
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.post(f"{self.base_url}/responses", headers={"Authorization": f"Bearer {self.api_key}"}, json=request)
            response.raise_for_status()
        import json
        data = response.json()
        return validate_structured_output(json.loads(data["output_text"]), schema)

