"""Regression locks for the teacher-reference thermochemistry evidence boundary."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "cases" / "studies" / "data" / "teacher_thermochemistry_equations.json"


def _load() -> dict:
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def test_teacher_thermochemistry_core_data_are_frozen_before_solver_integration() -> None:
    record = _load()
    readiness = record["readiness"]

    assert record["stage"] == "P11.3B"
    assert record["status"] == "EQUATIONS_AND_CORE_DATA_IMPLEMENTED_FULL_FUEL_DATABASE_PENDING"
    assert readiness["equation_transcription_ready"] is True
    assert readiness["isolated_thermochemistry_implementation_ready"] is True
    assert readiness["piecewise_interval_selection_ready"] is True
    assert readiness["core_H2_C2H4_species_data_ready"] is True
    assert readiness["complete_all_teacher_fuels_species_data_ready"] is False
    assert readiness["solver_integration_ready"] is False


def test_primary_teacher_and_cao_sources_are_both_recorded() -> None:
    sources = {entry["source_id"]: entry for entry in _load()["primary_sources"]}

    assert sources["TEACHER-CH11-P258-259"]["authority"] == "PRIMARY_PROJECT_REFERENCE"
    assert sources["CAO-PHD-CH2-EQ2-28-2-34"]["authority"] == "TEACHER_LINEAGE_CORROBORATION"


def test_core_database_is_ready_but_kerosene_cannot_be_silently_promoted() -> None:
    policy = _load()["coefficient_policy"]

    assert policy["core_H2_C2H4_branch_database_ready"] is True
    assert policy["complete_all_teacher_fuels_database_ready"] is False
    assert policy["blocked_species"] == ["C10H22"]
    assert "Do not invent" in policy["rule"]
    assert "temperature interval" in policy["rule"]


def test_chemical_energy_double_counting_is_explicitly_forbidden() -> None:
    policy = _load()["energy_accounting_policy"]

    assert policy["chemical_energy_in_absolute_species_enthalpy"] is True
    assert policy["direct_Qdot_surrogate_must_not_double_count_same_reaction_energy"] is True
    assert policy["external_wall_or_added_heat_remains_a_separate_source"] is True
