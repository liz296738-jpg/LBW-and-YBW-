"""Contract tests for the P14 project-defined inlet-Mach sensitivity."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from cases.studies import p11_4_project_defined_h2_smoke as baseline
from cases.studies import p14_project_defined_inlet_mach_sensitivity as study
from cases.studies.teacher_thermochemistry_database import build_species_database
from scramjet1d.teacher_combustion import fuel_stoichiometric_ratio


ROOT = Path(__file__).resolve().parents[1]
DEFINITION = (
    ROOT / "cases" / "studies" / "data" / "p14_inlet_mach_sensitivity_definition.json"
)
CONTEXT = (
    ROOT / "cases" / "studies" / "data" / "p14_inlet_mach_literature_context.json"
)


def test_p14_sampling_and_claim_boundary_are_frozen() -> None:
    assert study.PROJECT_TARGET_MACH_VALUES == (2.0, 2.2, 2.4, 2.6)
    assert study.PROJECT_CELL_COUNTS == (20, 40)

    record = json.loads(DEFINITION.read_text(encoding="utf-8"))
    assert record["classification"] == study.CASE_CLASSIFICATION
    assert record["source_reproduction"] is False
    assert record["experimental_validation"] is False
    assert record["varied_parameter"]["sample_values"] == [2.0, 2.2, 2.4, 2.6]
    assert record["varied_parameter"]["teacher_admissible_range_claim"] is False
    assert "fixed-static-state" in record["boundary_parameterization"]["interpretation_boundary"]
    assert "No monotonic" in record["preregistered_algebraic_expectations"][-1]


def test_p14_literature_context_does_not_become_validation_or_teacher_range() -> None:
    record = json.loads(CONTEXT.read_text(encoding="utf-8"))
    consequence = record["project_consequence"]

    assert consequence["engineering_context_interval"] == [2.0, 2.6]
    assert consequence["interval_is_teacher_admissible_range"] is False
    assert consequence["interval_is_validation_range"] is False
    assert consequence["sample_values"] == [2.0, 2.2, 2.4, 2.6]

    dois = {
        row.get("doi")
        for row in record["sources"]
        if row.get("doi") is not None
    }
    assert "10.1063/5.0267063" in dois
    assert "10.2514/1.B39243" in dois


def test_target_mach_maps_exactly_to_teacher_static_inlet_state() -> None:
    species = build_species_database()
    sound_speed = study.inlet_sound_speed_m_per_s(species)

    assert sound_speed > 0.0
    for target in study.PROJECT_TARGET_MACH_VALUES:
        case = study.build_case(20, target)
        actual = case[7]
        velocity = case[8]
        assert actual == pytest.approx(target, rel=2.0e-12, abs=2.0e-12)
        assert velocity == pytest.approx(target * sound_speed, rel=2.0e-15)


def test_fixed_static_state_makes_mass_flows_scale_with_target_mach() -> None:
    cases = {
        target: study.build_case(20, target)
        for target in study.PROJECT_TARGET_MACH_VALUES
    }
    air_per_mach = np.array([cases[m][9] / m for m in study.PROJECT_TARGET_MACH_VALUES])
    fuel_per_mach = np.array([cases[m][10] / m for m in study.PROJECT_TARGET_MACH_VALUES])

    np.testing.assert_allclose(air_per_mach, air_per_mach[0], rtol=2.0e-15, atol=0.0)
    np.testing.assert_allclose(fuel_per_mach, fuel_per_mach[0], rtol=2.0e-15, atol=0.0)

    expected_ratio = baseline.EQUIVALENCE_RATIO * fuel_stoichiometric_ratio("H2")
    for target, case in cases.items():
        mapping = case[2]
        air_mdot = case[9]
        fuel_mdot = case[10]
        dx = case[1]

        assert fuel_mdot / air_mdot == pytest.approx(expected_ratio, rel=2.0e-15)
        integrated_fuel = float(
            np.sum(mapping.fuel_mass_flow_gradient_kg_per_s_per_m) * dx
        )
        assert integrated_fuel == pytest.approx(fuel_mdot, rel=2.0e-15)


def test_p14_keeps_non_mach_baseline_controls_frozen() -> None:
    low = study.build_case(20, 2.0)
    high = study.build_case(20, 2.6)

    low_mapping = low[2]
    high_mapping = high[2]

    assert low[1] == high[1] == baseline.LENGTH_M / 20
    np.testing.assert_allclose(
        low_mapping.equivalence_ratio,
        high_mapping.equivalence_ratio,
        rtol=0.0,
        atol=0.0,
    )
    np.testing.assert_allclose(
        low_mapping.combustion_efficiency,
        high_mapping.combustion_efficiency,
        rtol=0.0,
        atol=0.0,
    )
    assert low_mapping.downstream_closure.mixing_length_m[0] == pytest.approx(
        high_mapping.downstream_closure.mixing_length_m[0],
        rel=0.0,
        abs=0.0,
    )


def test_p14_rejects_subsonic_or_invalid_target_mach() -> None:
    species = build_species_database()
    for bad in (1.0, 0.9, 0.0, -1.0, float("nan"), float("inf")):
        with pytest.raises(ValueError, match="strictly greater than one"):
            study.inlet_velocity_for_target_mach(bad, species)

    with pytest.raises(ValueError, match="cells must be one of"):
        study.build_case(80, 2.2)
