"""Regression lock for P11.3B variable-state recovery promotion boundary."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "cases" / "studies" / "data" / "teacher_variable_state_recovery.json"


def _load() -> dict:
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def test_isolated_state_recovery_is_ready_but_solver_integration_is_not() -> None:
    record = _load()
    readiness = record["readiness"]

    assert record["stage"] == "P11.3B"
    assert record["status"] == "ISOLATED_STATE_RECOVERY_IMPLEMENTED_SOLVER_INTEGRATION_PENDING"
    assert readiness["piecewise_species_data_ready"] is True
    assert readiness["fixed_composition_state_recovery_ready"] is True
    assert readiness["production_solver_integration_ready"] is False
    assert readiness["cellwise_species_transport_ready"] is False
    assert readiness["teacher_mixing_reaction_closure_ready"] is False


def test_state_recovery_boundary_forbids_clipping_and_silent_renormalization() -> None:
    boundaries = " ".join(_load()["scientific_boundaries"]).lower()

    assert "no temperature clipping" in boundaries
    assert "no mass-fraction renormalization" in boundaries
    assert "absolute chemical-energy enthalpy" in boundaries
    assert "constant-gamma production state path" in boundaries


def test_next_step_is_fixed_composition_euler_compatibility_not_reaction_shortcut() -> None:
    next_step = _load()["next_step"].lower()

    assert "variable-thermo euler flux/rhs compatibility path" in next_step
    assert "fixed composition" in next_step
    assert "source terms" in next_step
