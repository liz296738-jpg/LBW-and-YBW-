"""Guard the machine-readable teacher variable-composition readiness ledger."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "cases" / "studies" / "data" / "teacher_variable_composition_field.json"


def test_variable_composition_ledger_preserves_scope_and_gates() -> None:
    with LEDGER.open("r", encoding="utf-8") as stream:
        record = json.load(stream)

    assert record["schema_version"] == 1
    assert record["stage"] == "P11.3E"
    assert record["supported_fuels"] == ["H2", "C2H4"]
    assert "C10H22" in record["blocked_fuels"]

    state = record["state_representation"]
    assert state["flow_state"] == "three conservative variables [rho, rho*u, rho*E]"
    assert state["composition_evolution_in_this_stage"].startswith("algebraically prescribed")

    boundaries = record["scientific_boundaries"]
    assert boundaries["species_transport_equations_added"] is False
    assert boundaries["reaction_heat_source_added"] is False
    assert boundaries["prescribed_Qdot_used_for_teacher_reaction_energy"] is False
    assert boundaries["fuel_injection_source_coupled"] is False
    assert boundaries["numerical_flux_supports_different_left_right_compositions"] is False
    assert boundaries["time_marching_supports_variable_composition"] is False

    readiness = record["readiness"]
    assert readiness["composition_field_ready"] is True
    assert readiness["cellwise_state_conversion_ready"] is True
    assert readiness["variable_composition_flux_ready"] is False
    assert readiness["variable_composition_time_marching_ready"] is False
    assert readiness["integrated_teacher_combustor_case_ready"] is False
    assert readiness["production_solver_replacement_ready"] is False
