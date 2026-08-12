import json
from pathlib import Path
from app.evals.runner import evaluate_scenario, load_scenarios


DATASET = Path(__file__).parents[4] / "evals" / "datasets" / "scenarios.jsonl"


def test_seed_dataset_has_at_least_25_scenarios_across_required_categories():
    scenarios = load_scenarios(DATASET)
    assert len(scenarios) >= 25
    assert {item["category"] for item in scenarios} >= {"buyer", "vendor", "external_context", "recovery"}
    assert all(item.get("expected_stage") and item.get("expected_action_contains") for item in scenarios)


def test_literal_buyer_price_objection_scenario_scores_expected_behavior():
    scenario = {"id":"buyer-price","category":"buyer","utterance":"This asking price is too high",
        "expected_stage":"objection_handling","expected_trigger":"price_objection",
        "expected_action_contains":["price","viewing"]}
    result = evaluate_scenario(scenario)
    assert result["stage_match"] is True
    assert result["trigger_match"] is True
    assert result["action_terms_match"] is True

