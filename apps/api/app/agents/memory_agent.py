from app.memory.service import MemoryService, PersistenceResult
from app.models.contracts import CallSummary, ConversationState


class MemoryAgent:
    def __init__(self, service: MemoryService) -> None:
        self.service = service

    async def persist(self, call_id: str, customer_id: str, state: ConversationState, summary: CallSummary) -> PersistenceResult:
        return await self.service.persist_call(call_id, customer_id, state, summary)

    async def drain(self) -> None:
        import asyncio
        tasks = list(self.service.graph_tasks)
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

