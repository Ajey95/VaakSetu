from uuid import uuid4
from app.models.contracts import ConversationState, Recommendation


class FastCoach:
    def recommend(self, state: ConversationState, trigger: str) -> Recommendation:
        mortgage = state.customer.get("mortgage_approval", {}).get("value")
        timeline = state.customer.get("timeline", {}).get("value")
        if trigger == "price_objection":
            position = "their approved mortgage position" if mortgage == "approved" else "their financing position"
            move = f"Acknowledge the price concern, confirm {position}, then offer a specific viewing time."
            reason = "The customer raised a price objection; acknowledge it before progressing with known qualification context."
            confidence = "high"
        elif trigger == "timeline_mentioned" and timeline:
            move = f"They need to move in {timeline}; ask whether they have a mortgage agreement in principle before proposing a viewing."
            reason = "A fixed timeline is a high-intent signal, but financing must be qualified before progression."
            confidence = "high"
        else:
            move = "Reflect the customer's latest point, then ask the single highest-priority unanswered qualification question."
            reason = "This advances discovery without inventing facts or overwhelming the customer."
            confidence = "medium"
        return Recommendation(id=f"rec_{uuid4().hex[:10]}", type="fast", next_move=move, reason=reason,
                              confidence=confidence)

