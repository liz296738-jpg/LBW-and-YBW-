"""Regression lock for the source-backed Cao doctoral Case 2 evidence gate."""

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "cases" / "studies" / "data" / "teacher_cao_case2_source.json"


def _load() -> dict:
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def test_cao_case2_table_2_2_state_is_frozen_exactly() -> None:
    record = _load()
    table = record["table_2_2_isolator_entrance"]
    assert record["status"] == "SOURCE_INLET_FROZEN_FULL_REPRODUCTION_INPUTS_INCOMPLETE"
    assert record["case_identity"]["fuel"] == "H2"
    assert table["Mach"] == pytest.approx(2.12)
    assert table["density_kg_per_m3"] == pytest.approx(0.28)
    assert table["pressure_Pa"] == pytest.approx(46_700.0)
    assert table["temperature_K"] == pytest.approx(521.0)
    assert table["axial_velocity_m_per_s"] == pytest.approx(977.0)
    assert table["reported_heat_capacity_ratio"] == pytest.approx(1.33)
    assert table["equivalence_ratio"] == pytest.approx(0.2)
    assert table["wall_temperature_K"] == pytest.approx(900.0)
    assert table["mass_fractions"] == {"N2": 0.64, "O2": 0.22, "H2O": 0.13, "AR": 0.01}
    assert sum(table["mass_fractions"].values()) == pytest.approx(1.0)


def test_cao_case2_grid_and_prescribed_composition_semantics_are_frozen() -> None:
    record = _load()
    assert record["case_identity"]["reported_grid_spacings_m"] == [0.0001, 0.001]
    chemistry = record["case_identity"]["chemistry_treatment"].lower()
    assert "prescribed" in chemistry
    interpretation = " ".join(record["source_interpretation"]).lower()
    assert "vitiated" in interpretation
    assert "dry-air" in interpretation


def test_formal_reproduction_remains_blocked_until_spatial_inputs_are_frozen() -> None:
    record = _load()
    readiness = record["readiness"]
    assert readiness["source_identity_ready"] is True
    assert readiness["isolator_entrance_state_ready"] is True
    assert readiness["vitiated_inlet_composition_ready"] is True
    assert readiness["exact_geometry_profile_ready"] is False
    assert readiness["exact_prescribed_composition_profile_ready"] is False
    assert readiness["formal_case2_reproduction_ready"] is False
    assert readiness["chapter11_project_defined_integrated_smoke_case_allowed"] is True
    assert len(record["formal_reproduction_blockers"]) >= 4
    assert "PROJECT_DEFINED_INTEGRATED_SMOKE_CASE" in record["project_policy"]
