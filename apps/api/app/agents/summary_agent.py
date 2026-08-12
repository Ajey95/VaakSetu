from app.models.contracts import CallSummary, ConversationState, Evidence


class SummaryAgent:
    def summarize(self, state: ConversationState, evidence: list[Evidence], inferences: list[str]) -> CallSummary:
        facts: list[str] = []
        labels = {"budget": "Budget", "mortgage_approval": "Mortgage", "bedrooms": "Bedrooms", "timeline": "Timeline"}
        for key, item in state.customer.items():
            if key == "location_preferences":
                facts.extend(f"Location: {entry['value']}" for entry in item)
            elif isinstance(item, dict) and "value" in item:
                value = item["value"]
                if key == "budget" and isinstance(value, int):
                    value = f"£{value:,}"
                facts.append(f"{labels.get(key, key.replace('_', ' ').title())}: {value}")
        return CallSummary(
            customer_facts=facts,
            sales_signals=[item.get("evidence", item.get("type", "")) for item in state.signals],
            objections=[item.get("type", "") for item in state.objections],
            commitments=[f"{item.get('type', '').title()}: {item.get('detail', '')}" for item in state.commitments],
            external_verified_context=[{"claim": item.claim, "source": item.source_title,
                "retrieved_at": item.retrieved_at.isoformat(), "status": item.support_status} for item in evidence if item.safe_to_surface_as_fact],
            unverified_claims=[item["claim"] for item in state.external_claims if item.get("status") == "customer_said_unverified"],
            ai_inferences=inferences,
            next_steps=[state.current_recommendation["next_move"]] if state.current_recommendation else [],
            follow_up_memory=facts + [f"Commitment: {item.get('detail', '')}" for item in state.commitments],
        )

