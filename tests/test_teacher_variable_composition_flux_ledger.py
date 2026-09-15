"""Guard the P11.3F variable-composition Euler readiness ledger."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "cases" / "studies" / "data" / "teacher_variable_composition_flux.json"


def test_variable_composition_flux_ledger_preserves_scope_and_gates() -> None:
    record = json.loads(LEDGER.read_text(encoding="utf-8"))

    assert record["schema_version"] == 1
    assert record["stage"] == "P11.3F"
    assert record["status"] == (
        "VARIABLE_COMPOSITION_EULER_RUSANOV_COMPATIBILITY_IMPLEMENTED_TIME_MARCH_PENDING"
    )

    verification = record["verification"]
    assert all(verification.values())

    readiness = record["readiness"]
    assert readiness["variable_composition_state_recovery_ready"] is True
    assert readiness["variable_composition_physical_flux_ready"] is True
    assert readiness["variable_composition_rusanov_ready"] is True
    assert readiness["variable_composition_quasi_1d_operator_ready"] is True
    assert readiness["variable_composition_time_march_ready"] is False
    assert readiness["teacher_source_coupling_ready"] is False
    assert readiness["teacher_steger_warming_variable_composition_ready"] is False
    assert readiness["integrated_teacher_case_ready"] is False


def test_variable_composition_flux_ledger_forbids_species_and_qdot_overclaim() -> None:
    record = json.loads(LEDGER.read_text(encoding="utf-8"))
    boundaries = " ".join(record["scientific_boundaries"]).lower()

    assert "no species transport pde" in boundaries
    assert "no teacher reaction-energy qdot" in boundaries
    assert "three conservative flow variables only" in boundaries
    assert "steger-warming" in boundaries
