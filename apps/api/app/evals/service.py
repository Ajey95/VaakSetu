import asyncio


class AsyncEvaluationService:
    def __init__(self, delay_seconds: float = 0) -> None:
        self.tasks: set[asyncio.Task] = set()
        self.records: list[dict] = []
        self.delay_seconds = delay_seconds

    def queue(self, trajectory: dict) -> None:
        task = asyncio.create_task(self._evaluate(trajectory))
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)

    async def _evaluate(self, trajectory: dict) -> None:
        await asyncio.sleep(self.delay_seconds)
        self.records.append({"event_id": trajectory["event_id"], "queued": True})

    async def drain(self) -> None:
        tasks = list(self.tasks)
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
