from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime

from app.models.contracts import CallSummary


@dataclass
class StoredCall:
    call_id: str
    customer_id: str
    summary: CallSummary
    ended_at: datetime


class CallRepository(ABC):
    @abstractmethod
    async def save_call(self, call_id: str, customer_id: str, summary: CallSummary) -> None: ...
    @abstractmethod
    async def latest_for_customer(self, customer_id: str) -> StoredCall | None: ...
    @abstractmethod
    async def history_for_customer(self, customer_id: str) -> list[StoredCall]: ...


class InMemoryCallRepository(CallRepository):
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.summaries: dict[str, CallSummary] = {}
        self.calls: list[StoredCall] = []

    async def save_call(self, call_id: str, customer_id: str, summary: CallSummary) -> None:
        if self.fail:
            raise ConnectionError("Relational store unavailable")
        saved = summary.model_copy(deep=True)
        self.summaries[call_id] = saved
        self.calls.append(StoredCall(call_id, customer_id, saved, datetime.now(UTC)))

    async def latest_for_customer(self, customer_id: str) -> StoredCall | None:
        matches = [call for call in self.calls if call.customer_id == customer_id]
        return max(matches, key=lambda call: call.ended_at) if matches else None

    async def history_for_customer(self, customer_id: str) -> list[StoredCall]:
        return sorted((call for call in self.calls if call.customer_id == customer_id),
                      key=lambda call: call.ended_at, reverse=True)


class PostgreSQLCallRepository(CallRepository):
    def __init__(self, session_factory) -> None:
        self.session_factory = session_factory

    async def save_call(self, call_id: str, customer_id: str, summary: CallSummary) -> None:
        from app.db.models import CallSummaryRow
        async with self.session_factory() as session:
            existing = await session.get(CallSummaryRow, call_id)
            if existing:
                existing.content = summary.model_dump(mode="json")
                existing.customer_id = customer_id
            else:
                session.add(CallSummaryRow(id=call_id, call_id=call_id, customer_id=customer_id,
                    content=summary.model_dump(mode="json"), created_at=datetime.now(UTC)))
            await session.commit()

    async def latest_for_customer(self, customer_id: str) -> StoredCall | None:
        from sqlalchemy import select
        from app.db.models import CallSummaryRow
        async with self.session_factory() as session:
            result = await session.execute(select(CallSummaryRow).where(
                CallSummaryRow.customer_id == customer_id).order_by(CallSummaryRow.created_at.desc()).limit(1))
            row = result.scalar_one_or_none()
            if not row:
                return None
            return StoredCall(row.call_id, customer_id, CallSummary.model_validate(row.content), row.created_at)

    async def history_for_customer(self, customer_id: str) -> list[StoredCall]:
        from sqlalchemy import select
        from app.db.models import CallSummaryRow
        async with self.session_factory() as session:
            result = await session.execute(select(CallSummaryRow).where(
                CallSummaryRow.customer_id == customer_id).order_by(CallSummaryRow.created_at.desc()))
            return [StoredCall(row.call_id, customer_id, CallSummary.model_validate(row.content), row.created_at)
                    for row in result.scalars()]
