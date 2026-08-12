import asyncio


class AsyncEvaluationService:
    def __init__(self) -> None:
        self.tasks: set[asyncio.Task] = set()
        self.records: list[dict] = []

    def queue(self, trajectory: dict) -> None:
        task = asyncio.create_task(self._evaluate(trajectory))
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)

    async def _evaluate(self, trajectory: dict) -> None:
        await asyncio.sleep(0)
        self.records.append({"event_id": trajectory["event_id"], "queued": True})
