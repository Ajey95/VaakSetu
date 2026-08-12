from __future__ import annotations

from enum import StrEnum
from pydantic import BaseModel
from app.models.contracts import ConversationState, Utterance


class TriggerType(StrEnum):
    PRICE_OBJECTION = "price_objection"
    FEE_OBJECTION = "fee_objection"
    TIMELINE_MENTIONED = "timeline_mentioned"
    MORTGAGE_STATUS = "mortgage_status"
    VIEWING_INTENT = "viewing_intent"
    COMMITMENT = "commitment"
    MARKET_CLAIM = "market_claim"
    ENVIRONMENT_CLAIM = "environment_claim"
    PROPERTY_QUESTION = "property_question"


class ConversationTrigger(BaseModel):
    type: TriggerType
    priority: int
    utterance_id: str
    requires_domain_retrieval: bool = False
    requires_external_context: bool = False
    fast_coach_allowed: bool = True


def detect_triggers(state: ConversationState, utterance: Utterance) -> list[ConversationTrigger]:
    if not utterance.is_final:
        return []
    found: list[ConversationTrigger] = []
    for objection in state.objections:
        if objection.get("utterance_id") == utterance.id:
            kind = TriggerType.PRICE_OBJECTION if objection.get("type") == "price" else TriggerType.FEE_OBJECTION
            found.append(ConversationTrigger(type=kind, priority=100, utterance_id=utterance.id, requires_domain_retrieval=True))
    for claim in state.external_claims:
        if claim.get("utterance_id") == utterance.id:
            mapping = {"market": TriggerType.MARKET_CLAIM, "environment": TriggerType.ENVIRONMENT_CLAIM,
                       "energy": TriggerType.PROPERTY_QUESTION, "mortgage_rates": TriggerType.MARKET_CLAIM}
            found.append(ConversationTrigger(type=mapping.get(claim.get("topic"), TriggerType.PROPERTY_QUESTION),
                priority=90, utterance_id=utterance.id, requires_external_context=True))
    customer = state.customer
    if customer.get("timeline", {}).get("utterance_id") == utterance.id:
        found.append(ConversationTrigger(type=TriggerType.TIMELINE_MENTIONED, priority=70, utterance_id=utterance.id))
    if customer.get("mortgage_approval", {}).get("utterance_id") == utterance.id:
        found.append(ConversationTrigger(type=TriggerType.MORTGAGE_STATUS, priority=75, utterance_id=utterance.id))
    for commitment in state.commitments:
        if commitment.get("utterance_id") == utterance.id:
            found.append(ConversationTrigger(type=TriggerType.COMMITMENT, priority=95, utterance_id=utterance.id))
    return sorted(found, key=lambda trigger: trigger.priority, reverse=True)

