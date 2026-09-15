"""Regression lock for variable-thermo Euler compatibility promotion boundaries."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "cases" / "studies" / "data" / "teacher_variable_euler_compatibility.json"


def _load() -> dict:
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def test_variable_euler_operator_is_ready_before_time_march_promotion() -> None:
    record = _load()
    readiness = record["readiness"]

    assert record["stage"] == "P11.3B"
    assert record["status"] == "FIXED_COMPOSITION_EULER_COMPATIBILITY_IMPLEMENTED_SOLVER_TIME_MARCH_PENDING"
    assert readiness["variable_state_recovery_ready"] is True
    assert readiness["variable_physical_flux_ready"] is True
    assert readiness["variable_rusanov_ready"] is True
    assert readiness["variable_quasi_1d_operator_ready"] is True
    assert readiness["fixed_composition_time_march_ready"] is False


def test_compatibility_stage_does_not_claim_teacher_reaction_or_steger_warming_completion() -> None:
    readiness = _load()["readiness"]

    assert readiness["teacher_steger_warming_variable_thermo_ready"] is False
    assert readiness["teacher_boundary_case_adapter_ready"] is False
    assert readiness["teacher_mixing_reaction_closure_ready"] is False
    assert readiness["integrated_teacher_case_ready"] is False


def test_energy_and_boundary_scientific_limits_are_explicit() -> None:
    boundaries = " ".join(_load()["scientific_boundaries"]).lower()

    assert "composition remains fixed" in boundaries
    assert "rusanov first" in boundaries
    assert "not the final teacher inlet" in boundaries
    assert "double counting" in boundaries
    assert "constant-gamma production solver remains unchanged" in boundaries
