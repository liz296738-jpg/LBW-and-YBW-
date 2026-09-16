"""Regression locks for teacher-reference project alignment."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "cases" / "studies" / "data" / "teacher_reference_alignment.json"


def _load() -> dict:
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def test_lbw_ybw_are_project_names_not_physical_modes() -> None:
    record = _load()
    naming = record["project_naming"]

    assert naming["LBW"] == "PERSON_OR_COLLABORATOR_IDENTIFIER"
    assert naming["YBW"] == "PERSON_OR_COLLABORATOR_IDENTIFIER"
    assert "not combustion-mode labels" in naming["policy"]


def test_teacher_core_h2_c2h4_path_is_ready_but_full_source_parity_is_not() -> None:
    record = _load()
    alignment = record["alignment"]
    assessment = record["overall_assessment"]

    assert assessment["direction_conflict"] is False
    assert assessment["foundation_is_reusable"] is True
    assert assessment["core_h2_c2h4_teacher_path_ready"] is True
    assert assessment["full_teacher_second_scheme_ready"] is False
    assert alignment["unsteady_quasi_1d_conservative_pde"]["ready"] is True
    assert alignment["third_order_tvd_ssp_rk"]["ready"] is True
    assert alignment["integrated_variable_thermochemistry_rusanov_path"]["ready"] is True


def test_completed_teacher_physics_closures_remain_marked_ready() -> None:
    alignment = _load()["alignment"]

    assert alignment["temperature_and_composition_dependent_thermodynamics"]["ready"] is True
    assert alignment["mixing_efficiency_and_mixing_length_closure"]["ready"] is True
    assert alignment["equivalence_ratio_and_fuel_specific_composition_closure"]["ready"] is True
    assert alignment["teacher_empirical_friction_closure"]["ready"] is True
    assert alignment["chemical_energy_bookkeeping_consistency"]["ready"] is True


def test_remaining_source_gaps_cannot_silently_be_marked_ready() -> None:
    alignment = _load()["alignment"]

    assert alignment["teacher_empirical_wall_heat_closure"]["ready"] is False
    assert alignment["near_sonic_eigenvalue_smoothing"]["ready"] is False
    assert alignment["cao_case2_formal_reproduction"]["ready"] is False


def test_teacher_density_convergence_compatibility_is_implemented_without_unsourced_residual_gate() -> None:
    entry = _load()["alignment"]["teacher_relative_density_convergence_metric"]

    assert entry["ready"] is True
    assert entry["implementation"] == "scramjet1d.convergence.max_relative_density_change"
    assert "independent diagnostic" in entry["policy"]
    assert "without inventing a source threshold" in entry["policy"]
