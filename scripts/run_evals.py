from pathlib import Path
import json, sys
sys.path.insert(0, str(Path(__file__).parents[1] / "apps" / "api"))
from app.evals.runner import run
result=run(Path(__file__).parents[1]/"evals"/"datasets"/"scenarios.jsonl")
print(json.dumps({"total":result["total"],"fully_matching":result["fully_matching"]},indent=2))
raise SystemExit(0 if result["fully_matching"]==result["total"] else 1)
