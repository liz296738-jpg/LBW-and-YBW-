"""Regression tests for the P11.3 solver-observable capability audit."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAPPING = ROOT / "cases" / "studies" / "data" / "p11_3_solver_observable_mapping.json"


def _load() -> dict:
    return json.loads(MAPPING.read_text(encoding="utf-8"))


def test_capability_audit_does_not_promote_a_classifier() -> None:
    record = _load()
    policy = record["classification_policy"]

    assert record["status"] == "CAPABILITY_AUDIT_COMPLETE_CLASSIFIER_MAPPING_PENDING"
    assert policy["can_implement_general_literature_classifier_now"] is False
    assert policy["can_implement_lbw_ybw_classifier_now"] is False
    assert policy["can_generate_lbw_ybw_regime_map_now"] is False


def test_native_mach_and_pressure_profiles_remain_diagnostics_not_silent_mode_labels() -> None:
    record = _load()
    observables = {entry["observable_id"]: entry for entry in record["native_solver_observables"]}

    mach = observables["AXIAL_MACH_PROFILE"]
    pressure = observables["AXIAL_STATIC_PRESSURE_PROFILE"]
    assert mach["status"] == "DIRECTLY_AVAILABLE"
    assert "not by itself" in mach["forbidden_inference"]
    assert pressure["status"] == "DIRECTLY_AVAILABLE"
    assert "not a universal" in pressure["forbidden_inference"]


def test_precombustion_shock_state_is_not_claimed_as_current_native_observable() -> None:
    record = _load()
    missing = {entry["observable_id"]: entry for entry in record["not_natively_resolved"]}

    assert missing["PRECOMBUSTION_SHOCK_TRAIN_PRESENCE"]["status"] == "NOT_SOURCE_DEFINED_IN_CURRENT_SOLVER"
    assert missing["SHOCK_TRAIN_LENGTH"]["status"] == "NOT_SOURCE_DEFINED_IN_CURRENT_SOLVER"
    assert missing["BOUNDARY_LAYER_SEPARATION_REATTACHMENT"]["status"] == "OUTSIDE_CURRENT_MODEL"


def test_existing_accepted_cases_are_not_relabelled_as_mode_transition_validation() -> None:
    record = _load()
    cases = {entry["case_family"]: entry for entry in record["domain_specific_findings"]}

    assert cases["P11.2B_NASA_BURROWS_KURKOV"]["classification_capability"] == "NOT_SUITABLE_FOR_LBW_YBW_MODE_CLASSIFICATION"
    assert cases["P11.2A_LI_PUBLIC_COLD_SURROGATE"]["classification_capability"] == "NOT_SUITABLE_FOR_REACTIVE_MODE_CLASSIFICATION"
    assert cases["FUTURE_P11_3_MODE_TRANSITION_CASE"]["classification_capability"] == "REQUIRES_NEW_SOURCE_BACKED_CASE_DEFINITION"


def test_nonconvergence_is_not_silently_called_unstart() -> None:
    record = _load()
    observables = {entry["observable_id"]: entry for entry in record["native_solver_observables"]}
    text = observables["STEADY_CONVERGENCE_AND_TERMINATION"]["forbidden_inference"].lower()

    assert "nonconvergence" in text
    assert "not physical inlet unstart" in text
