"""Contract tests for the P11.4 project-defined integrated H2 smoke case."""
import pytest

from cases.studies.p11_4_project_defined_h2_smoke import (
    CASE_CLASSIFICATION,
    EQUIVALENCE_RATIO,
    NOT_A_SOURCE_REPRODUCTION,
    WALL_HEAT_GRADIENT_J_PER_KG_PER_M,
    build_case,
)
from scramjet1d.teacher_combustion import fuel_stoichiometric_ratio
from scramjet1d.variable_composition import variable_composition_conservative_to_primitive


def test_case_is_explicitly_project_defined_and_not_source_reproduction() -> None:
    assert CASE_CLASSIFICATION == "PROJECT_DEFINED_INTEGRATED_SMOKE_CASE"
    assert NOT_A_SOURCE_REPRODUCTION is True
    assert WALL_HEAT_GRADIENT_J_PER_KG_PER_M == 0.0


def test_case_builds_complete_h2_teacher_path_with_valid_initial_state() -> None:
    species, dx, mapping, geometry, inlet, U0, _ = build_case(40)
    assert mapping.fuel == "H2"
    assert mapping.injector_cell > 0
    assert geometry.num_cells == 40
    assert dx == pytest.approx(0.01)
    primitive = variable_composition_conservative_to_primitive(U0, mapping.composition, species)
    assert primitive.T.min() == pytest.approx(800.0, abs=2.0e-6)
    assert primitive.p.min() == pytest.approx(55_000.0, rel=3.0e-10)
    assert primitive.p.max() == pytest.approx(55_000.0, rel=3.0e-10)
    assert primitive.Mach.min() > 1.0
    expected_fuel = EQUIVALENCE_RATIO * fuel_stoichiometric_ratio("H2")
    assert mapping.fuel_mass_flow_gradient_kg_per_s_per_m.sum() * dx == pytest.approx(expected_fuel)


def test_case_keeps_upstream_air_only_and_downstream_teacher_composition() -> None:
    species, _, mapping, _, _, _, _ = build_case(40)
    upstream = mapping.composition.composition_at(0)
    downstream = mapping.composition.composition_at(mapping.injector_cell + 1)
    assert upstream["H2"] == 0.0
    assert upstream["H2O"] == 0.0
    assert downstream["H2"] >= 0.0
    assert downstream["H2O"] >= 0.0
    assert sum(upstream.values()) == pytest.approx(1.0)
    assert sum(downstream.values()) == pytest.approx(1.0)
