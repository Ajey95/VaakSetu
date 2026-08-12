from app.tools.router import ToolKind, route_information_need


def test_routes_only_context_that_needs_external_or_domain_data():
    cases = {
        "Prices in Manchester fell 10%": ToolKind.MARKET,
        "Does this street flood?": ToolKind.ENVIRONMENT,
        "Are mortgage rates falling?": ToolKind.MARKET,
        "What is the EPC rating?": ToolKind.PROPERTY,
        "Are there planning restrictions?": ToolKind.PLANNING,
        "How should I handle a fee objection?": ToolKind.KNOWLEDGE,
        "I prefer two bedrooms": ToolKind.NONE,
    }
    for text, expected in cases.items():
        assert route_information_need(text) is expected

