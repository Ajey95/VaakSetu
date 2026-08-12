from pathlib import Path
import hashlib

from app.memory.vector import InMemoryVectorStore, VectorChunk


class KnowledgeAgent:
    def __init__(self, root: Path, store=None, dimensions: int = 1536) -> None:
        self.root = root
        self.store = store or InMemoryVectorStore()
        self.dimensions = dimensions
        self._indexed = False

    def _embedding(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for term in text.lower().split():
            digest = hashlib.sha256(term.strip(".,:;!?()[]").encode("utf-8")).digest()
            vector[int.from_bytes(digest[:4], "big") % self.dimensions] += 1.0
        return vector

    async def index(self) -> None:
        if self._indexed:
            return
        for path in self.root.rglob("*.md"):
            content = path.read_text(encoding="utf-8")
            await self.store.add(VectorChunk(
                id=hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:24],
                content=content, embedding=self._embedding(content),
                metadata={"document_id": path.stem, "source": str(path)}))
        self._indexed = True

    async def retrieve(self, query: str, limit: int = 3) -> list[dict[str, str]]:
        await self.index()
        chunks = await self.store.search(self._embedding(query), limit)
        return [{"id": item.id, "content": item.content[:1500], "source": item.metadata.get("source", "unknown"),
                 "retrieval": "vector"} for item in chunks]
