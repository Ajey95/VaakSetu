from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime

from app.memory.relational import CallRepository
from app.memory.temporal_graph import TemporalFact, TemporalGraphStore
from app.models.contracts import CallSummary, ConversationState


@dataclass
class PersistenceResult:
    relational_saved: bool
    graph_queued: bool


class MemoryService:
    def __init__(self, repository: CallRepository, graph: TemporalGraphStore) -> None:
        self.repository = repository
        self.graph = graph
        self.graph_tasks: set[asyncio.Task] = set()

    async def persist_call(self, call_id: str, customer_id: str, state: ConversationState, summary: CallSummary) -> PersistenceResult:
        try:
            await self.repository.save_call(call_id, customer_id, summary)
        except Exception:
            return PersistenceResult(False, False)
        queued = False
        for predicate, item in state.customer.items():
            if predicate == "location_preferences":
                values = item
            else:
                values = [item]
            for value in values:
                if not isinstance(value, dict) or "value" not in value:
                    continue
                timestamp = value.get("timestamp")
                try:
                    valid_from = datetime.fromisoformat(timestamp) if timestamp else datetime.now(UTC)
                except (TypeError, ValueError):
                    valid_from = datetime.now(UTC)
                fact = TemporalFact(entity_id=customer_id, predicate=predicate, value=value["value"],
                    valid_from=valid_from,
                    source_event_id=value.get("utterance_id", call_id))
                task = asyncio.create_task(self._safe_graph_write(fact))
                self.graph_tasks.add(task)
                task.add_done_callback(self.graph_tasks.discard)
                queued = True
        return PersistenceResult(True, queued)

    async def _safe_graph_write(self, fact: TemporalFact) -> None:
        try:
            await self.graph.upsert_fact(fact)
        except Exception:
            pass

    async def pre_call_brief(self, customer_id: str) -> dict:
        latest = await self.repository.latest_for_customer(customer_id)
        if not latest:
            return {"customer_id": customer_id, "known": [], "source_call_id": None}
        summary = latest.summary
        return {"customer_id": customer_id, "last_contact": latest.ended_at.isoformat(),
            "known": summary.customer_facts, "last_concern": summary.objections,
            "last_commitment": summary.commitments, "unresolved": summary.next_steps,
            "suggested_opening": "Refer to the last commitment and ask what has changed since the previous call.",
            "do_not_repeat": summary.customer_facts, "source_call_id": latest.call_id}
