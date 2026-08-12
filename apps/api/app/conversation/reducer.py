from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.models.contracts import ConversationState, Speaker, Utterance


@dataclass
class ConversationUpdate:
    state: ConversationState
    changes: list[str] = field(default_factory=list)
    invalidation_reasons: list[str] = field(default_factory=list)


def _record(value: object, utterance: Utterance) -> dict[str, object]:
    return {"value": value, "source": "customer" if utterance.speaker is Speaker.CUSTOMER else "agent",
            "utterance_id": utterance.id, "timestamp": utterance.timestamp.isoformat()}


def _append_unique(items: list[dict], item: dict, keys: tuple[str, ...] = ("type", "utterance_id")) -> None:
    if not any(all(existing.get(key) == item.get(key) for key in keys) for existing in items):
        items.append(item)


def apply_final_utterance(state: ConversationState, utterance: Utterance) -> ConversationUpdate:
    updated = state.model_copy(deep=True)
    if not utterance.is_final:
        return ConversationUpdate(updated)

    text = utterance.text
    lower = text.lower()
    changes: list[str] = []
    invalidation: list[str] = []
    customer = updated.customer

    if re.search(r"\b(buyer|buy|buying|looking for|searching for)\b", lower):
        updated.call_type = "buyer"
        changes.append("call_type")
    elif re.search(r"\b(vendor|sell|selling|my property|valuation)\b", lower):
        updated.call_type = "vendor"
        changes.append("call_type")

    budget = re.search(r"(?:budget(?: is)?|up to|maximum|max(?:imum)?)\s*(?:of\s*)?[£$]?\s*([\d,.]+)\s*(k)?", lower)
    if budget:
        value = int(float(budget.group(1).replace(",", "")) * (1000 if budget.group(2) else 1))
        customer["budget"] = _record(value, utterance)
        changes.append("budget")
    mortgage = re.search(r"mortgage\s+(approved|approval|agreement in principle|aip|not approved|pending)", lower)
    if mortgage:
        raw = mortgage.group(1)
        value = "approved" if raw in {"approved", "approval", "agreement in principle", "aip"} else raw
        customer["mortgage_approval"] = _record(value, utterance)
        changes.extend(["mortgage_approval", "sensitive_item"])
        _append_unique(updated.sensitive_items, {"type": "financial_position", "utterance_id": utterance.id, "evidence": text})
    bedrooms = re.search(r"\b(\d+)\s*(?:bed|bedroom)s?\b", lower)
    if bedrooms:
        customer["bedrooms"] = _record(int(bedrooms.group(1)), utterance)
        changes.append("bedrooms")
    timeline = re.search(r"(?:in|within|about)\s+(?:(six|one|two|three|four|five|seven|eight|nine|ten|eleven|twelve)|([\d]+))\s+(day|week|month)s?", lower)
    if timeline:
        words = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
                 "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12}
        amount = words.get(timeline.group(1), int(timeline.group(2)) if timeline.group(2) else 0)
        customer["timeline"] = _record(f"{amount} {timeline.group(3)}s", utterance)
        changes.append("timeline")
        _append_unique(updated.signals, {"type": "fixed_timeline", "utterance_id": utterance.id, "evidence": text})
    location = re.search(r"(?:looking in|in|around|near)\s+([A-Z][A-Za-z]+(?:\s+[A-Za-z]+){0,3}?)(?=\s+(?:for|with|and|city|area)|[,.]|$)", text)
    if "Manchester city centre" in text:
        location_value = "Manchester city centre"
    elif location:
        location_value = location.group(1).strip()
    else:
        location_value = None
    if location_value:
        locations = customer.setdefault("location_preferences", [])
        if not any(item["value"].lower() == location_value.lower() for item in locations):
            locations.append(_record(location_value, utterance))
            changes.append("location")

    old_stage = updated.stage
    objection_type = None
    if re.search(r"\b(overpriced|price.{0,20}(?:high|expensive)|asking price|too expensive)\b", lower):
        objection_type = "price"
    elif re.search(r"\b(fee|commission).{0,20}(?:high|expensive|too much)\b", lower):
        objection_type = "fees"
    if objection_type:
        _append_unique(updated.objections, {"type": objection_type, "utterance_id": utterance.id, "evidence": text})
        updated.stage = "objection_handling"
        updated.temperature = "warm" if updated.temperature in {"unknown", "hot"} else updated.temperature
        changes.extend(["objection", "stage"])

    if re.search(r"\b(ready to instruct|instruct you|appoint you)\b", lower):
        _append_unique(updated.signals, {"type": "instruction_ready", "utterance_id": utterance.id, "evidence": text})
        changes.append("signal")
    if re.search(r"\b(book|arrange|open to|works for me).{0,30}\b(viewing|valuation)\b|\b(viewing|valuation).{0,30}\b(saturday|monday|tuesday|wednesday|thursday|friday|sunday|works)\b", lower):
        kind = "valuation" if "valuation" in lower else "viewing"
        _append_unique(updated.commitments, {"type": kind, "detail": text, "utterance_id": utterance.id})
        updated.stage = "progression"
        updated.temperature = "hot"
        changes.extend(["commitment", "stage"])
    if re.search(r"\b(deposit|afford|financial position)\b", lower):
        _append_unique(updated.sensitive_items, {"type": "financial_position", "utterance_id": utterance.id, "evidence": text})
        changes.append("sensitive_item")
    if re.search(r"\b(divorce|probate|bereavement|must move|personal deadline)\b", lower):
        _append_unique(updated.sensitive_items, {"type": "personal_deadline", "utterance_id": utterance.id, "evidence": text})
        changes.append("sensitive_item")

    claims = (
        ("market", r"\b(prices?|house prices?|market).{0,35}\b(fell|fallen|dropped|drop|rose|risen|up|down)\b|\b(fell|dropped)\s+\d+%"),
        ("environment", r"\b(flood|flooding|environmental risk)\b"),
        ("mortgage_rates", r"\b(mortgage rates?|interest rates?).{0,30}\b(falling|rising|down|up)\b"),
        ("energy", r"\b(epc|energy efficient|energy rating)\b"),
    )
    for topic, pattern in claims:
        if re.search(pattern, lower):
            _append_unique(updated.external_claims, {"claim": text, "topic": topic, "status": "customer_said_unverified",
                                                     "utterance_id": utterance.id}, ("topic", "utterance_id"))
            changes.append("external_claim")

    if old_stage != updated.stage and updated.current_recommendation:
        updated.current_recommendation["lifecycle"] = "stale"
        updated.current_recommendation["stale_reason"] = "stage_changed"
        invalidation.append("stage_changed")
    return ConversationUpdate(updated, list(dict.fromkeys(changes)), invalidation)

