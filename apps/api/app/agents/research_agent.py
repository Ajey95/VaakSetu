from app.tools.base import ExternalTool, ToolResult
from app.tools.router import ToolKind, route_information_need


class ResearchAgent:
    def __init__(self, tool: ExternalTool) -> None:
        self.tool = tool

    async def research(self, text: str) -> ToolResult | None:
        kind = route_information_need(text)
        if kind in {ToolKind.NONE, ToolKind.KNOWLEDGE}:
            return None
        return await self.tool.search(text, kind.value)

