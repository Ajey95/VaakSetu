from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from app.agents.deep_coach import DeepCoach
from app.agents.evidence_agent import EvidenceAgent
from app.agents.fast_coach import FastCoach
from app.agents.research_agent import ResearchAgent
from app.llm.base import LLMProvider
from app.models.contracts import ConversationState, Evidence, Recommendation
from app.tools.base import ExternalTool


class GraphState(TypedDict, total=False):
    state: ConversationState
    text: str
    trigger: str
    fast: Recommendation
    evidence: list[Evidence]
    deep: Recommendation | None


@dataclass
class IntelligenceResult:
    fast_recommendation: Recommendation
    evidence: list[Evidence]
    deep_recommendation: Recommendation | None


class IntelligenceGraph:
    def __init__(self, llm: LLMProvider, tool: ExternalTool, publish: Callable[[Recommendation], None]) -> None:
        self.fast = FastCoach()
        self.deep = DeepCoach(llm)
        self.research = ResearchAgent(tool)
        self.evidence_agent = EvidenceAgent()
        self.publish = publish
        builder = StateGraph(GraphState)
        builder.add_node("fast", self._fast_node)
        builder.add_node("research", self._research_node)
        builder.add_node("deep", self._deep_node)
        builder.add_edge(START, "fast")
        builder.add_edge("fast", "research")
        builder.add_edge("research", "deep")
        builder.add_edge("deep", END)
        self.compiled = builder.compile()

    async def _fast_node(self, graph: GraphState) -> dict:
        recommendation = self.fast.recommend(graph["state"], graph["trigger"])
        self.publish(recommendation)
        return {"fast": recommendation, "evidence": [], "deep": None}

    async def _research_node(self, graph: GraphState) -> dict:
        try:
            result = await self.research.research(graph["text"])
        except Exception:
            evaluation = self.evidence_agent.evaluate(graph["text"], [])
            return {"evidence": [Evidence(id=f"ev_{uuid4().hex[:10]}", claim=graph["text"], retrieved_at=datetime.now(UTC),
                support_status=evaluation.status, confidence=evaluation.confidence, freshness=evaluation.freshness,
                safe_to_surface_as_fact=False)]}
        if not result:
            return {"evidence": []}
        evaluation = self.evidence_agent.evaluate(graph["text"], result.results)
        preferred = next((item for item in result.results if item.source_id == evaluation.preferred_source_id), None)
        evidence = Evidence(id=f"ev_{uuid4().hex[:10]}", claim=graph["text"], source_id=preferred.source_id if preferred else None,
            source_title=preferred.title if preferred else None, source_url=preferred.url if preferred else None,
            source_tier=preferred.source_tier if preferred else None, retrieved_at=preferred.retrieved_at if preferred else datetime.now(UTC),
            published_at=preferred.published_at if preferred else None, support_status=evaluation.status,
            confidence=evaluation.confidence, freshness=evaluation.freshness,
            safe_to_surface_as_fact=evaluation.safe_to_surface_as_fact)
        return {"evidence": [evidence]}

    async def _deep_node(self, graph: GraphState) -> dict:
        evidence = graph.get("evidence", [])
        if not evidence or not any(item.safe_to_surface_as_fact for item in evidence):
            return {"deep": None}
        try:
            recommendation = await self.deep.recommend(graph["state"], graph["fast"], evidence)
        except Exception:
            return {"deep": None}
        self.publish(recommendation)
        return {"deep": recommendation}

    async def run(self, state: ConversationState, text: str, trigger: str) -> IntelligenceResult:
        result = await self.compiled.ainvoke({"state": state, "text": text, "trigger": trigger})
        return IntelligenceResult(result["fast"], result.get("evidence", []), result.get("deep"))

