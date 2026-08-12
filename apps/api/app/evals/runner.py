from __future__ import annotations

import json
from pathlib import Path
from app.conversation.reducer import apply_final_utterance
from app.conversation.triggers import detect_triggers
from app.agents.fast_coach import FastCoach
from app.models.contracts import ConversationState, Speaker, Utterance


def load_scenarios(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def evaluate_scenario(scenario: dict) -> dict:
    state = ConversationState(call_id=scenario["id"], call_type=scenario.get("call_type", "unknown"))
    utterance = Utterance(id="utt-eval", call_id=scenario["id"], speaker=Speaker.CUSTOMER,
        text=scenario["utterance"], sequence=1, source_track="inbound_track")
    updated = apply_final_utterance(state, utterance).state
    triggers = detect_triggers(updated, utterance)
    trigger = triggers[0].type.value if triggers else scenario.get("fallback_trigger", "")
    recommendation = FastCoach().recommend(updated, trigger)
    terms = [term.lower() for term in scenario["expected_action_contains"]]
    return {"id": scenario["id"], "stage_match": updated.stage == scenario["expected_stage"],
        "trigger_match": trigger == scenario["expected_trigger"],
        "action_terms_match": all(term in recommendation.next_move.lower() for term in terms),
        "actual_stage": updated.stage, "actual_trigger": trigger, "next_move": recommendation.next_move}


def run(path: Path) -> dict:
    results = [evaluate_scenario(item) for item in load_scenarios(path)]
    return {"total": len(results), "fully_matching": sum(all(item[key] for key in ("stage_match","trigger_match","action_terms_match")) for item in results),
            "results": results}

