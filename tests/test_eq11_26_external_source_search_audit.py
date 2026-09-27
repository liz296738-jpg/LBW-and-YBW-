"""Guard the unresolved teacher Eq.11.26 dimensional-coupling boundary."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = (
    ROOT
    / "cases"
    / "studies"
    / "data"
    / "eq11_26_external_source_search_audit.json"
)


def test_eq11_26_external_search_does_not_promote_an_unsourced_adapter() -> None:
    record = json.loads(LEDGER.read_text(encoding="utf-8"))

    assert record["status"] == "NO_UNIQUE_SOURCE_TRACEABLE_DIMENSIONAL_ADAPTER_RECOVERED"
    recovered = record["recovered"]
    assert recovered["eq_11_25_external_lineage_corroboration"] is True
    assert recovered["eq_11_26_exact_polynomial_external_primary_definition"] is False
    assert recovered["eq_11_26_units_recovered"] is False
    assert recovered["eq_11_26_to_delta_q_mapping_recovered"] is False
    assert recovered["production_adapter_ready"] is False

    policy = record["production_policy"]
    assert policy["explicit_dimensional_input_channel_ready"] is True
    assert policy["project_baseline_value_J_per_kg_per_m"] == 0.0
    assert "SOURCE_GATED_NEUTRALIZATION" in policy["baseline_zero_classification"]
    assert policy["external_model_silent_substitution_allowed"] is False


def test_external_heat_transfer_models_are_recorded_as_non_substitutable() -> None:
    record = json.loads(LEDGER.read_text(encoding="utf-8"))
    alternatives = " ".join(record["non_substitutable_alternatives"]).lower()

    assert "eckert" in alternatives
    assert "regenerative" in alternatives
    assert "convective" in alternatives
