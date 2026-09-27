"""Contract tests for the P11.4 project-defined integrated H2 smoke case."""
import numpy as np
import pytest

from cases.studies.p11_4_project_defined_h2_smoke import (
    CASE_CLASSIFICATION,
    EQUIVALENCE_RATIO,
    EXIT_AREA_M2,
    INLET_AREA_M2,
    INLET_VELOCITY_M_PER_S,
    MIXING_C_M,
    NOT_A_SOURCE_REPRODUCTION,
    WALL_HEAT_GRADIENT_J_PER_KG_PER_M,
    build_case,
    project_inlet_air_mass_flow,
)
from scramjet1d.teacher_combustion import fuel_stoichiometric_ratio
from scramjet1d.variable_composition import variable_composition_conservative_to_primitive


def test_case_is_explicitly_project_defined_and_not_source_reproduction() -> None:
    assert CASE_CLASSIFICATION == "PROJECT_DEFINED_INTEGRATED_SMOKE_CASE"
    assert NOT_A_SOURCE_REPRODUCTION is True
    assert WALL_HEAT_GRADIENT_J_PER_KG_PER_M == 0.0


def test_case_builds_complete_h2_teacher_path_with_valid_initial_state() -> None:
    (
        species,
        dx,
        mapping,
        geometry,
        hydraulic_diameter,
        inlet,
        U0,
        inlet_primitive,
    ) = build_case(40)
    assert mapping.fuel == "H2"
    assert mapping.injector_cell > 0
    assert geometry.num_cells == 40
    assert dx == pytest.approx(0.01)
    assert geometry.face_area[0] == pytest.approx(INLET_AREA_M2)
    assert geometry.face_area[-1] == pytest.approx(EXIT_AREA_M2)
    assert np.all(np.diff(geometry.face_area) > 0.0)
    assert np.all(hydraulic_diameter > 0.0)

    primitive = variable_composition_conservative_to_primitive(
        U0, mapping.composition, species
    )
    assert primitive.T.min() == pytest.approx(800.0, abs=2.0e-6)
    assert primitive.p.min() == pytest.approx(55_000.0, rel=3.0e-10)
    assert primitive.p.max() == pytest.approx(55_000.0, rel=3.0e-10)
    assert primitive.Mach.min() > 1.0

    air_mdot = project_inlet_air_mass_flow(species)
    inlet_flux_mdot = (
        inlet_primitive.rho * INLET_VELOCITY_M_PER_S * INLET_AREA_M2
    )
    assert air_mdot == pytest.approx(inlet_flux_mdot, rel=2.0e-12)
    expected_fuel = (
        EQUIVALENCE_RATIO * fuel_stoichiometric_ratio("H2") * air_mdot
    )
    assert (
        mapping.fuel_mass_flow_gradient_kg_per_s_per_m.sum() * dx
        == pytest.approx(expected_fuel)
    )


def test_case_keeps_upstream_air_only_and_downstream_teacher_composition() -> None:
    species, _, mapping, _, _, _, _, _ = build_case(40)
    upstream = mapping.composition.composition_at(0)
    downstream = mapping.composition.composition_at(mapping.injector_cell + 1)
    assert upstream["H2"] == 0.0
    assert upstream["H2O"] == 0.0
    assert downstream["H2"] >= 0.0
    assert downstream["H2O"] >= 0.0
    assert sum(upstream.values()) == pytest.approx(1.0)
    assert sum(downstream.values()) == pytest.approx(1.0)


def test_baseline_mixing_constant_is_explicit_and_default_build_is_unchanged() -> None:
    default = build_case(20)
    explicit = build_case(20, mixing_C_m=MIXING_C_M)

    default_mapping = default[2]
    explicit_mapping = explicit[2]

    assert MIXING_C_M == 30.0
    np.testing.assert_allclose(
        default_mapping.downstream_closure.mixing_length_m,
        explicit_mapping.downstream_closure.mixing_length_m,
        rtol=0.0,
        atol=0.0,
    )
    np.testing.assert_allclose(
        default_mapping.composition.mass_fractions,
        explicit_mapping.composition.mass_fractions,
        rtol=0.0,
        atol=0.0,
    )


def test_mixing_constant_outside_teacher_range_is_rejected() -> None:
    with pytest.raises(ValueError, match="outside the teacher-source range"):
        build_case(20, mixing_C_m=24.999)
    with pytest.raises(ValueError, match="outside the teacher-source range"):
        build_case(20, mixing_C_m=60.001)
