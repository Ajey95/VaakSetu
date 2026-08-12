from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from pydantic import BaseModel


class TemporalFact(BaseModel):
    entity_id: str
    predicate: str
    value: object
    valid_from: datetime
    source_event_id: str
    valid_to: datetime | None = None
    observed_at: datetime | None = None
    current: bool = True


class TemporalGraphStore(ABC):
    @abstractmethod
    async def upsert_fact(self, fact: TemporalFact) -> None: ...
    @abstractmethod
    async def history(self, entity_id: str, predicate: str) -> list[TemporalFact]: ...


class InMemoryTemporalGraphStore(TemporalGraphStore):
    def __init__(self, fail: bool = False, write_gate: asyncio.Event | None = None) -> None:
        self.fail = fail
        self.write_gate = write_gate
        self.facts: list[TemporalFact] = []
        self.pending_writes = 0
        self.read_count = 0

    async def upsert_fact(self, fact: TemporalFact) -> None:
        self.pending_writes += 1
        try:
            if self.write_gate:
                await self.write_gate.wait()
            if self.fail:
                raise ConnectionError("Graph unavailable")
            for prior in self.facts:
                if prior.entity_id == fact.entity_id and prior.predicate == fact.predicate and prior.current:
                    prior.valid_to = fact.valid_from
                    prior.current = False
            self.facts.append(fact.model_copy(deep=True))
        finally:
            self.pending_writes -= 1

    async def history(self, entity_id: str, predicate: str) -> list[TemporalFact]:
        self.read_count += 1
        return [item.model_copy(deep=True) for item in self.facts if item.entity_id == entity_id and item.predicate == predicate]


class Neo4jTemporalGraphStore(TemporalGraphStore):
    def __init__(self, uri: str, username: str, password: str) -> None:
        from neo4j import AsyncGraphDatabase
        self.driver = AsyncGraphDatabase.driver(uri, auth=(username, password))

    async def upsert_fact(self, fact: TemporalFact) -> None:
        query = """
        MATCH (e:Entity {id: $entity_id})-[old:HAS_FACT {predicate: $predicate, current: true}]->(:Fact)
        SET old.current = false, old.valid_to = $valid_from
        WITH e
        CREATE (f:Fact {value: $value, observed_at: $observed_at, source_event_id: $source_event_id})
        CREATE (e)-[:HAS_FACT {predicate: $predicate, current: true, valid_from: $valid_from}]->(f)
        """
        create_entity = "MERGE (:Entity {id: $entity_id})"
        params = fact.model_dump(mode="json")
        params["observed_at"] = params["observed_at"] or params["valid_from"]
        async with self.driver.session() as session:
            await session.run(create_entity, entity_id=fact.entity_id)
            await session.run(query, **params)

    async def history(self, entity_id: str, predicate: str) -> list[TemporalFact]:
        query = """
        MATCH (:Entity {id: $entity_id})-[r:HAS_FACT {predicate: $predicate}]->(f:Fact)
        RETURN f.value AS value, r.valid_from AS valid_from, r.valid_to AS valid_to,
               r.current AS current, f.observed_at AS observed_at, f.source_event_id AS source_event_id
        ORDER BY r.valid_from
        """
        async with self.driver.session() as session:
            result = await session.run(query, entity_id=entity_id, predicate=predicate)
            return [TemporalFact(entity_id=entity_id, predicate=predicate, **record.data()) async for record in result]

    async def close(self) -> None:
        await self.driver.close()
