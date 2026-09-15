"""Verification for the source-enabled teacher compatibility solver."""

from __future__ import annotations

import numpy as np
import pytest

from cases.studies.teacher_thermochemistry_database import build_species_database
from scramjet1d.config import NumericalConfig
from scramjet1d.geometry import constant_area_profile
from scramjet1d.teacher_integrated_solver import (
    solve_teacher_single_injector_compatibility,
    teacher_single_injector_rhs_transmissive,
    teacher_single_injector_ssp_rk3_step,
)
from scramjet1d.teacher_single_injector import build_teacher_single_injector_mapping
from scramjet1d.teacher_sources import teacher_eq_11_38_non_geometric_source
from scramjet1d.time_integration import ssp_rk3_step
from scramjet1d.variable_composition import (
    variable_composition_conservative_to_primitive,
    variable_composition_primitive_to_conservative,
)
from scramjet1d.variable_composition_euler import variable_composition_quasi_1d_rhs_transmissive


SPECIES = build_species_database()
DX = 0.02


def _mapping():
    x = np.arange(9, dtype=float) * DX
    return build_teacher_single_injector_mapping(
        fuel="H2",
        injected_fuel_mass_flow_rate_kg_per_s=0.002,
        incoming_air_mass_flow_rate_kg_per_s=1.0,
        x_cell_m=x,
        dx_m=DX,
        injector_cell=2,
        combustor_height_m=0.04,
        C_m=35.0,
        injection_mode="parallel",
        injected_fuel_temperature_K=450.0,
        injected_fuel_axial_velocity_m_per_s=120.0,
        species=SPECIES,
    )


def _state(mapping):
    return variable_composition_primitive_to_conservative(
        rho=0.45,
        u=900.0,
        temperature_K=950.0,
        field=mapping.composition,
        species=SPECIES,
    )


def test_integrated_rhs_is_exact_sum_of_verified_euler_and_eq11_source() -> None:
    mapping = _mapping()
    geometry = constant_area_profile(mapping.composition.num_cells, area=0.025)
    U = _state(mapping)
    wall_heat_gradient = np.linspace(0.0, 25.0, mapping.composition.num_cells)

    actual = teacher_single_injector_rhs_transmissive(
        U,
        mapping,
        geometry,
        DX,
        SPECIES,
        hydraulic_diameter_m=0.05,
        wall_specific_heat_gain_gradient_J_per_kg_per_m=wall_heat_gradient,
    )
    expected = variable_composition_quasi_1d_rhs_transmissive(
        U, mapping.composition, geometry, DX, SPECIES
    ) + teacher_eq_11_38_non_geometric_source(
        U,
        mapping.composition,
        geometry,
        SPECIES,
        phi=mapping.equivalence_ratio,
        eta=mapping.combustion_efficiency,
        hydraulic_diameter_m=0.05,
        fuel_mass_flow_gradient_kg_per_s_per_m=mapping.fuel_mass_flow_gradient_kg_per_s_per_m,
        fuel_axial_velocity_m_per_s=mapping.fuel_axial_velocity_m_per_s,
        fuel_specific_total_enthalpy_J_per_kg=mapping.fuel_specific_total_enthalpy_J_per_kg,
        wall_specific_heat_gain_gradient_J_per_kg_per_m=wall_heat_gradient,
    )
    np.testing.assert_allclose(actual, expected, rtol=0.0, atol=0.0)


def test_mass_equation_adds_exactly_one_prescribed_fuel_source_on_constant_area_grid() -> None:
    mapping = _mapping()
    area = 0.025
    geometry = constant_area_profile(mapping.composition.num_cells, area=area)
    U = _state(mapping)
    rhs = teacher_single_injector_rhs_transmissive(
        U,
        mapping,
        geometry,
        DX,
        SPECIES,
        hydraulic_diameter_m=0.05,
        wall_specific_heat_gain_gradient_J_per_kg_per_m=0.0,
    )
    # For identical rho/u in every cell the mass Euler flux is constant even
    # though composition varies, so the integrated mass RHS is the fuel source.
    integrated_mass_rate = np.sum(rhs[:, 0] * geometry.cell_area) * DX
    assert integrated_mass_rate == pytest.approx(0.002, rel=2.0e-12, abs=2.0e-15)


def test_one_rk3_step_recomputes_the_complete_stage_rhs() -> None:
    mapping = _mapping()
    geometry = constant_area_profile(mapping.composition.num_cells, area=0.025)
    U = _state(mapping)
    dt = 2.0e-7

    actual = teacher_single_injector_ssp_rk3_step(
        U,
        mapping,
        geometry,
        DX,
        dt,
        SPECIES,
        hydraulic_diameter_m=0.05,
        wall_specific_heat_gain_gradient_J_per_kg_per_m=0.0,
    )

    def rhs(stage_state):
        return teacher_single_injector_rhs_transmissive(
            stage_state,
            mapping,
            geometry,
            DX,
            SPECIES,
            hydraulic_diameter_m=0.05,
            wall_specific_heat_gain_gradient_J_per_kg_per_m=0.0,
        )

    expected = ssp_rk3_step(U, dt, rhs)
    np.testing.assert_allclose(actual, expected, rtol=0.0, atol=0.0)


def test_short_source_enabled_transient_remains_thermochemically_valid() -> None:
    mapping = _mapping()
    geometry = constant_area_profile(mapping.composition.num_cells, area=0.025)
    U0 = _state(mapping)
    result = solve_teacher_single_injector_compatibility(
        U0,
        mapping,
        geometry,
        DX,
        8.0e-7,
        NumericalConfig(cfl=0.2, tolerance=1.0e-6),
        SPECIES,
        hydraulic_diameter_m=0.05,
        wall_specific_heat_gain_gradient_J_per_kg_per_m=0.0,
        max_steps=100,
    )
    primitive = variable_composition_conservative_to_primitive(
        result.U, mapping.composition, SPECIES
    )
    assert result.time == pytest.approx(8.0e-7, abs=0.0)
    assert result.steps >= 1
    assert np.all(np.isfinite(result.U))
    assert np.all(primitive.rho > 0.0)
    assert np.all(primitive.p > 0.0)
    assert np.all(primitive.T > 0.0)
    assert np.all(np.isfinite(primitive.Mach))


def test_wall_heat_gradient_is_explicit_and_changes_only_energy_source_directly() -> None:
    mapping = _mapping()
    geometry = constant_area_profile(mapping.composition.num_cells, area=0.025)
    U = _state(mapping)
    zero = teacher_single_injector_rhs_transmissive(
        U,
        mapping,
        geometry,
        DX,
        SPECIES,
        hydraulic_diameter_m=0.05,
        wall_specific_heat_gain_gradient_J_per_kg_per_m=0.0,
    )
    gradient = np.linspace(10.0, 40.0, mapping.composition.num_cells)
    heated = teacher_single_injector_rhs_transmissive(
        U,
        mapping,
        geometry,
        DX,
        SPECIES,
        hydraulic_diameter_m=0.05,
        wall_specific_heat_gain_gradient_J_per_kg_per_m=gradient,
    )
    delta = heated - zero
    primitive = variable_composition_conservative_to_primitive(U, mapping.composition, SPECIES)
    np.testing.assert_allclose(delta[:, 0], 0.0, atol=0.0)
    np.testing.assert_allclose(delta[:, 1], 0.0, atol=0.0)
    np.testing.assert_allclose(
        delta[:, 2], primitive.rho * primitive.u * gradient, rtol=2.0e-13, atol=2.0e-8
    )


def test_solver_rejects_mismatched_dx_geometry_and_bad_step_budget() -> None:
    mapping = _mapping()
    geometry = constant_area_profile(mapping.composition.num_cells, area=0.025)
    U = _state(mapping)
    with pytest.raises(ValueError, match="grid spacing"):
        teacher_single_injector_rhs_transmissive(
            U,
            mapping,
            geometry,
            0.021,
            SPECIES,
            hydraulic_diameter_m=0.05,
            wall_specific_heat_gain_gradient_J_per_kg_per_m=0.0,
        )
    wrong_geometry = constant_area_profile(mapping.composition.num_cells + 1, area=0.025)
    with pytest.raises(ValueError, match="geometry.num_cells"):
        teacher_single_injector_rhs_transmissive(
            U,
            mapping,
            wrong_geometry,
            DX,
            SPECIES,
            hydraulic_diameter_m=0.05,
            wall_specific_heat_gain_gradient_J_per_kg_per_m=0.0,
        )
    with pytest.raises(ValueError, match="max_steps"):
        solve_teacher_single_injector_compatibility(
            U,
            mapping,
            geometry,
            DX,
            1.0e-6,
            NumericalConfig(),
            SPECIES,
            hydraulic_diameter_m=0.05,
            wall_specific_heat_gain_gradient_J_per_kg_per_m=0.0,
            max_steps=0,
        )
