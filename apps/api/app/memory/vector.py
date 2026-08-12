from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass
class VectorChunk:
    id: str
    content: str
    embedding: list[float]
    metadata: dict


class InMemoryVectorStore:
    def __init__(self) -> None:
        self.chunks: list[VectorChunk] = []

    async def add(self, chunk: VectorChunk) -> None:
        self.chunks.append(chunk)

    async def search(self, embedding: list[float], limit: int = 3) -> list[VectorChunk]:
        def cosine(item: VectorChunk) -> float:
            numerator = sum(a * b for a, b in zip(embedding, item.embedding))
            denominator = math.sqrt(sum(a * a for a in embedding)) * math.sqrt(sum(b * b for b in item.embedding))
            return numerator / denominator if denominator else 0
        return sorted(self.chunks, key=cosine, reverse=True)[:limit]


class PgVectorStore:
    def __init__(self, session_factory) -> None:
        self.session_factory = session_factory

    async def add(self, chunk: VectorChunk) -> None:
        from sqlalchemy import text
        async with self.session_factory() as session:
            await session.execute(text("""
                INSERT INTO knowledge_chunks (id, document_id, content, embedding, metadata)
                VALUES (:id, :document_id, :content, CAST(:embedding AS vector), CAST(:metadata AS jsonb))
                ON CONFLICT (id) DO UPDATE SET content = EXCLUDED.content, embedding = EXCLUDED.embedding, metadata = EXCLUDED.metadata
            """), {"id": chunk.id, "document_id": chunk.metadata.get("document_id", "domain"),
                    "content": chunk.content, "embedding": str(chunk.embedding),
                    "metadata": __import__("json").dumps(chunk.metadata)})
            await session.commit()

    async def search(self, embedding: list[float], limit: int = 3) -> list[VectorChunk]:
        from sqlalchemy import text
        async with self.session_factory() as session:
            result = await session.execute(text("""
                SELECT id, content, embedding::text, metadata
                FROM knowledge_chunks ORDER BY embedding <=> CAST(:embedding AS vector) LIMIT :limit
            """), {"embedding": str(embedding), "limit": limit})
            return [VectorChunk(id=row.id, content=row.content,
                embedding=[float(value) for value in row[2].strip("[]").split(",")], metadata=row.metadata) for row in result]
