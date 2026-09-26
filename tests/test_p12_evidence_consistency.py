"""Cross-file consistency guards for frozen P12 scientific evidence."""
from __future__ import annotations

import json
from pathlib import Path

from cases.studies import p12_project_defined_response_sweep as sweep


ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE = (
    ROOT
    / "cases"
    / "studies"
    / "data"
    / "p12_project_defined_response_sweep_acceptance.json"
)
FOUNDATION = ROOT / "docs" / "p12_project_defined_mode_transition_foundation.md"


def _acceptance() -> dict:
    return json.loads(ACCEPTANCE.read_text(encoding="utf-8"))


def test_eq_11_46_numeric_tolerance_is_explicitly_project_defined() -> None:
    record = _acceptance()

    assert sweep.PROJECT_EQ_11_46_STEADY_TOLERANCE == 2.0e-5
    assert (
        sweep.TEACHER_EQ_11_46_STEADY_TOLERANCE
        == sweep.PROJECT_EQ_11_46_STEADY_TOLERANCE
    )
    provenance = record["acceptance_policy"]["tolerance_provenance"]
    assert "project numerical choice" in provenance
    assert "does not claim" in provenance


def test_p12_foundation_matches_frozen_response_minimum_mach_values() -> None:
    record = _acceptance()
    text = FOUNDATION.read_text(encoding="utf-8")
    converged = [
        point for point in record["points"] if point["status"] == "CONVERGED"
    ]

    assert len(converged) == 2
    for point in converged:
        phi = point["equivalence_ratio"]
        min_mach = point["min_mach"]
        assert f"phi={phi:.2f}" in text
        assert f"min(Ma)={min_mach:.6f}..." in text


def test_mass_inventory_gate_is_explicitly_project_defined() -> None:
    record = _acceptance()
    policy = record["acceptance_policy"]

    assert "project-defined QA threshold" in policy["mass_inventory_gate"]
    assert "internal project acceptance threshold" in policy["mass_inventory_gate_provenance"]
    assert "no teacher, paper, experiment, or universal CFD standard" in (
        policy["mass_inventory_gate_provenance"]
    )
