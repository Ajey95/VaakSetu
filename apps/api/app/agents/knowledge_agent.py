from pathlib import Path


class KnowledgeAgent:
    def __init__(self, root: Path) -> None:
        self.root = root

    async def retrieve(self, query: str, limit: int = 3) -> list[dict[str, str]]:
        terms = set(query.lower().split())
        ranked = []
        for path in self.root.rglob("*.md"):
            content = path.read_text(encoding="utf-8")
            score = len(terms & set(content.lower().split()))
            if score:
                ranked.append((score, {"id": path.stem, "content": content[:1500], "source": str(path)}))
        return [item for _, item in sorted(ranked, key=lambda row: row[0], reverse=True)[:limit]]

