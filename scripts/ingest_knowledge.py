from pathlib import Path
root=Path(__file__).parents[1]/"knowledge"; docs=list(root.rglob("*.md")); print(f"Validated {len(docs)} knowledge documents ({sum(len(p.read_text(encoding='utf-8')) for p in docs)} characters)")
