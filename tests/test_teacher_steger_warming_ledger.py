"""Regression lock for the P11.3M Steger-Warming source/readiness boundary."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "cases" / "studies" / "data" / "teacher_steger_warming.json"


def _load() -> dict:
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def test_teacher_steger_warming_formulas_are_frozen_but_epsilon_value_is_not() -> None:
    record = _load()
    readiness = record["readiness"]
    assert record["stage"] == "P11.3M"
    assert readiness["eq_11_42_formula_frozen"] is True
    assert readiness["eq_11_43_formula_frozen"] is True
    assert readiness["eq_11_44_formula_frozen"] is True
    assert readiness["epsilon_numeric_value_frozen"] is False
    assert record["equations"]["11.44"]["epsilon_numeric_value_in_current_source"] == "NOT_SPECIFIED"


def test_no_default_epsilon_and_energy_compatibility_block_remain_explicit() -> None:
    record = _load()
    readiness = record["readiness"]
    verification = record["verification"]
    boundaries = " ".join(record["scientific_boundaries"]).lower()
    assert "no default epsilon" in boundaries
    assert "epsilon=0" in boundaries
    assert readiness["literal_source_split_operator_implemented"] is True
    assert verification["literal_variable_thermochemistry_mass_flux_identity"] is True
    assert verification["literal_variable_thermochemistry_momentum_flux_identity"] is True
    assert verification["literal_variable_thermochemistry_energy_flux_identity"] is False
    assert verification["variable_energy_compatibility_blocker_detected"] is True
    assert readiness["variable_thermochemistry_energy_flux_compatibility_ready"] is False
    assert readiness["teacher_boundary_fvs_integration_ready"] is False
    assert readiness["source_enabled_steger_warming_solver_ready"] is False
    assert readiness["formal_teacher_steger_warming_case_ready"] is False
    assert readiness["rusanov_integrated_compatibility_path_remains_accepted"] is True


def test_area_weighting_convention_is_explicit() -> None:
    record = _load()
    convention = record["equations"]["11.42"]["implementation_convention"].lower()
    assert "per-unit-area" in convention
    assert "face area" in convention
