from enum import StrEnum


class ToolKind(StrEnum):
    NONE = "none"
    KNOWLEDGE = "knowledge"
    PROPERTY = "property"
    MARKET = "market"
    ENVIRONMENT = "environment"
    WEATHER = "weather"
    TRANSPORT = "transport"
    PLANNING = "planning"
    REGULATION = "regulation"


def route_information_need(text: str) -> ToolKind:
    lower = text.lower()
    if any(term in lower for term in ("mortgage rate", "interest rate", "prices", "house price", "market")):
        return ToolKind.MARKET
    if any(term in lower for term in ("flood", "environmental", "subsidence")):
        return ToolKind.ENVIRONMENT
    if any(term in lower for term in ("epc", "energy rating", "energy efficient", "property certificate")):
        return ToolKind.PROPERTY
    if any(term in lower for term in ("planning", "restriction", "listed building")):
        return ToolKind.PLANNING
    if any(term in lower for term in ("fee objection", "price objection", "sales playbook", "compliance")):
        return ToolKind.KNOWLEDGE
    return ToolKind.NONE

