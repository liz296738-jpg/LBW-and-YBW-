"""Regression tests for Jin et al. simple quasi-1D validation applicability."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "cases" / "studies" / "data" / "p11_2b_jin_validation_applicability.json"


def _load() -> dict:
    return json.loads(RECORD.read_text(encoding="utf-8"))


def test_jin_equations_retain_friction_and_energy_inputs() -> None:
    record = _load()
    inputs = record["published_quasi_1d_inputs"]

    assert record["candidate_id"] == "JIN-LIU-MODEL-B-VALIDATION"
    assert record["primary_source"]["source_id"] == "SRC08"
    assert "wall friction coefficient Cf" in inputs["equation_9_pressure_terms"]
    assert "wall friction coefficient Cf" in inputs["equation_10_mach_terms"]
    assert "mass flow rate mdot" in inputs["equation_11_energy_terms"]
    assert "initial stagnation temperature Tt0" in inputs["equation_11_energy_terms"]


def test_source_requires_supersonic_separation_free_simple_validation() -> None:
    record = _load()
    assumptions = record["explicit_source_assumptions"]
    policy = record["solver_applicability_policy"]

    assert assumptions["flow_must_remain_supersonic"] is True
    assert assumptions["flow_separation_absent"] is True
    assert assumptions["shock_wave_train_effects_ignored_under_assumption"] is True
    assert "min(M)>1" in policy["mach_gate"]
    assert "cannot prove absence" in policy["separation_gate"]
    assert "does not resolve a physical shock train" in policy["shock_train_gate"]


def test_inlet_and_numeric_friction_inputs_remain_unresolved_but_convention_is_closed() -> None:
    record = _load()
    unresolved = {item["item"]: item for item in record["unresolved_reproduction_inputs"]}
    resolved = {item["item"]: item for item in record["resolved_reproduction_inputs"]}

    assert unresolved["Fig. 14 station-3 / combustor-inlet boundary state"]["status"] == "NOT_FROZEN"
    assert unresolved["Fig. 14 wall-friction coefficient Cf"]["status"] == "NOT_FROZEN"
    assert "Cf convention to repository Darcy friction factor" not in unresolved

    convention = resolved["Cf convention to repository Darcy friction factor"]
    assert convention["status"] == "RESOLVED_DERIVED_FROM_SOURCE_DEFINITION"
    assert convention["mapping"] == "f_D = 4 Cf"
    assert record["friction_convention_closure"]["mapping"] == "f_D = 4 Cf"
    assert "does not disable friction" in record["cross_source_boundary"]["not_authorized"]
    assert "still not fully specify" in record["formal_case_effect"]
