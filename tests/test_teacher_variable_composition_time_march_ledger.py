"""Guard the P11.3G prescribed-composition time-march promotion boundary."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "cases" / "studies" / "data" / "teacher_variable_composition_time_march.json"


def test_prescribed_composition_time_march_readiness_is_scoped() -> None:
    record = json.loads(LEDGER.read_text(encoding="utf-8"))

    assert record["schema_version"] == 1
    assert record["stage"] == "P11.3G"
    assert record["status"] == (
        "PRESCRIBED_COMPOSITION_SSP_RK3_IMPLEMENTED_DYNAMIC_CLOSURE_PENDING"
    )
    assert all(record["verification"].values())

    readiness = record["readiness"]
    assert readiness["variable_composition_state_ready"] is True
    assert readiness["variable_composition_euler_operator_ready"] is True
    assert readiness["variable_composition_cfl_ready"] is True
    assert readiness["prescribed_composition_ssp_rk3_ready"] is True
    assert readiness["dynamic_phi_eta_composition_update_ready"] is False
    assert readiness["teacher_fuel_source_coupling_ready"] is False
    assert readiness["teacher_wall_source_coupling_ready"] is False
    assert readiness["integrated_teacher_case_ready"] is False


def test_time_march_ledger_forbids_dynamic_reaction_overclaim() -> None:
    record = json.loads(LEDGER.read_text(encoding="utf-8"))
    text = " ".join(record["scientific_boundaries"]).lower()

    assert "immutable" in text
    assert "no species-transport pde" in text
    assert "no fuel injection" in text
    assert "no independent teacher chemical qdot" in text
    assert "steger-warming" in text
