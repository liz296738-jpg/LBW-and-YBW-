"""Regression tests for the Jin-Liu P11.2B validation-condition discrepancy."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "cases" / "studies" / "data" / "p11_2b_jin_liu_condition_discrepancy.json"


def _load() -> dict:
    return json.loads(RECORD.read_text(encoding="utf-8"))


def test_jin_liu_condition_conflict_remains_explicitly_unresolved() -> None:
    record = _load()

    assert record["schema_version"] == 1
    assert record["candidate_id"] == "JIN-LIU-MODEL-B-VALIDATION"
    assert record["status"] == "UNRESOLVED_CROSS_MODEL_EQUIVALENCE_RATIO_CONFLICT"

    jin = record["sources"]["jin_2026"]
    liu_match = record["sources"]["liu_2019_matching_exit_mach"]
    liu_phi = record["sources"]["liu_2019_exact_phi_1_04"]

    assert jin["reported_configuration"] == "scramjet model B"
    assert jin["reported_equivalence_ratio"] == 1.04
    assert jin["reported_experimental_exit_Mach"] == 2.27

    assert liu_match["configuration"] == "model B"
    assert liu_match["equivalence_ratio"] == 1.03
    assert liu_match["exit_Mach"] == 2.27
    assert liu_match["Ht4_over_Ht3"] == 1.16

    assert liu_phi["configuration"] == "model A"
    assert liu_phi["equivalence_ratio"] == 1.04
    assert liu_phi["exit_Mach"] == 1.76
    assert liu_phi["Ht4_over_Ht3"] == 1.29


def test_discrepancy_record_forbids_silent_rounding_or_cross_model_promotion() -> None:
    record = _load()
    boundary = record["inference_boundary"]

    assert any("model A" in statement for statement in boundary["confirmed"])
    assert any("typographical or rounding error" in statement for statement in boundary["not_resolved"])
    assert "Do not promote" in boundary["promotion_policy"]
