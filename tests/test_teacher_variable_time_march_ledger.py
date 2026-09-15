"""Regression lock for P11.3B fixed-composition time-march promotion boundary."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "cases" / "studies" / "data" / "teacher_variable_time_march.json"


def _load() -> dict:
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def test_time_march_is_ready_before_reaction_closure() -> None:
    record = _load()
    readiness = record["readiness"]

    assert record["stage"] == "P11.3B"
    assert record["status"] == "FIXED_COMPOSITION_SSP_RK3_TIME_MARCH_IMPLEMENTED_REACTION_CLOSURE_PENDING"
    assert readiness["fixed_composition_variable_state_ready"] is True
    assert readiness["fixed_composition_variable_euler_operator_ready"] is True
    assert readiness["local_variable_cfl_ready"] is True
    assert readiness["fixed_composition_ssp_rk3_time_march_ready"] is True
    assert readiness["teacher_mixing_reaction_closure_ready"] is False
    assert readiness["variable_composition_solver_ready"] is False


def test_time_march_scope_keeps_unimplemented_physics_explicit() -> None:
    text = " ".join(_load()["scientific_boundaries"]).lower()

    assert "composition is fixed" in text
    assert "no fuel injection" in text
    assert "rusanov" in text
    assert "transmissive boundaries" in text
    assert "constant-gamma production solver remains unchanged" in text
    assert "no direct chemical qdot" in text


def test_next_step_returns_to_teacher_mixing_and_composition_equations() -> None:
    next_step = _load()["next_step"]
    assert "11.19-11.29" in next_step
    assert "mixing efficiency" in next_step
    assert "equivalence-ratio" in next_step
    assert "fuel-specific composition" in next_step
