"""Guard the P11.3H source-aligned spatial closure boundary."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "cases" / "studies" / "data" / "teacher_spatial_composition_closure.json"


def test_spatial_closure_ledger_freezes_source_aligned_interpretation() -> None:
    record = json.loads(LEDGER.read_text(encoding="utf-8"))

    assert record["schema_version"] == 1
    assert record["stage"] == "P11.3H"
    assert record["status"] == (
        "SINGLE_INJECTOR_LEAN_SPATIAL_COMPOSITION_CLOSURE_IMPLEMENTED_SOURCE_COUPLING_PENDING"
    )
    decision = record["source_alignment_decision"]
    assert decision["model_interpretation"] == "STATIC_SPATIAL_ALGEBRAIC_CLOSURE_DURING_PSEUDO_TIME"
    assert "dynamic phi/eta/y_i" in decision["correction_to_prior_planning_language"].lower()


def test_spatial_closure_readiness_does_not_overclaim_source_coupling() -> None:
    record = json.loads(LEDGER.read_text(encoding="utf-8"))
    readiness = record["readiness"]

    assert readiness["teacher_phi_profile_ready"] is True
    assert readiness["teacher_mixing_length_profile_ready"] is True
    assert readiness["teacher_raw_mixing_efficiency_profile_ready"] is True
    assert readiness["teacher_physical_combustion_efficiency_profile_ready"] is True
    assert readiness["teacher_H2_C2H4_composition_field_ready"] is True
    assert readiness["prescribed_composition_solver_compatibility_ready"] is True
    assert readiness["distributed_fuel_injection_adapter_ready"] is False
    assert readiness["teacher_fuel_source_coupling_ready"] is False
    assert readiness["teacher_wall_source_coupling_ready"] is False
    assert readiness["integrated_teacher_case_ready"] is False


def test_spatial_closure_ledger_preserves_scientific_boundaries() -> None:
    record = json.loads(LEDGER.read_text(encoding="utf-8"))
    text = " ".join(record["scientific_boundaries"]).lower()

    assert "one prescribed injection station" in text
    assert "phi <= 1" in text
    assert "c10h22" in text
    assert "no species-transport pde" in text
    assert "no independent chemical qdot" in text
