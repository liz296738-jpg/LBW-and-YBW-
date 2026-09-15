"""Verification for teacher Chapter 11 Eq. (11.38) source adapters."""

from __future__ import annotations

import numpy as np
import pytest

from cases.studies.teacher_thermochemistry_database import build_species_database
from scramjet1d.geometry import constant_area_profile
from scramjet1d.teacher_combustion import fuel_stoichiometric_ratio
from scramjet1d.teacher_sources import (
    injected_fuel_specific_total_enthalpy,
    localized_injector_mass_flow_gradient,
    teacher_eq_11_38_non_geometric_source,
)
from scramjet1d.teacher_wall import friction_coefficient_raw
from scramjet1d.variable_composition import (
    build_lean_teacher_composition_field,
    variable_composition_conservative_to_primitive,
    variable_composition_primitive_to_conservative,
)


SPECIES = build_species_database()


def _field(num_cells: int, *, fuel: str = "H2", phi: float = 0.5, eta: float = 0.4):
    return build_lean_teacher_composition_field(
        fuel,
        np.full(num_cells, phi),
        np.full(num_cells, eta),
        SPECIES,
    )


def test_localized_injector_gradient_integrates_to_prescribed_mass_flow() -> None:
    num_cells = 7
    dx = 0.02
    mdot = 0.015
    gradient = localized_injector_mass_flow_gradient(num_cells, 3, mdot, dx)

    assert gradient.shape == (num_cells,)
    assert np.count_nonzero(gradient) == 1
    assert gradient[3] == pytest.approx(mdot / dx, rel=0.0, abs=0.0)
    assert np.sum(gradient) * dx == pytest.approx(mdot, rel=2.0e-16, abs=0.0)


def test_injected_total_enthalpy_uses_absolute_species_h_plus_axial_kinetic_energy() -> None:
    T = 500.0
    u_s = 220.0
    expected = SPECIES["H2"].h(T) + 0.5 * u_s**2
    actual = injected_fuel_specific_total_enthalpy("H2", T, u_s, SPECIES)
    assert actual == pytest.approx(expected, rel=2.0e-15, abs=0.0)


def test_eq_11_38_injection_integrals_match_mass_momentum_and_total_enthalpy_addition() -> None:
    num_cells = 5
    dx = 0.025
    area = 0.02
    mdot = 0.01
    injector_cell = 2
    u_s = 180.0
    h_ts = injected_fuel_specific_total_enthalpy("H2", 450.0, u_s, SPECIES)
    field = _field(num_cells, phi=0.5, eta=0.3)
    U = variable_composition_primitive_to_conservative(
        rho=0.5,
        u=0.0,
        temperature_K=900.0,
        field=field,
        species=SPECIES,
    )
    geometry = constant_area_profile(num_cells, area=area)
    gradient = localized_injector_mass_flow_gradient(num_cells, injector_cell, mdot, dx)

    source = teacher_eq_11_38_non_geometric_source(
        U,
        field,
        geometry,
        SPECIES,
        phi=np.full(num_cells, 0.5),
        eta=np.full(num_cells, 0.3),
        hydraulic_diameter_m=0.04,
        fuel_mass_flow_gradient_kg_per_s_per_m=gradient,
        fuel_axial_velocity_m_per_s=u_s,
        fuel_specific_total_enthalpy_J_per_kg=h_ts,
        wall_specific_heat_gain_gradient_J_per_kg_per_m=0.0,
    )

    integrated = np.sum(source * geometry.cell_area[:, None], axis=0) * dx
    np.testing.assert_allclose(
        integrated,
        np.array([mdot, u_s * mdot, h_ts * mdot]),
        rtol=3.0e-15,
        atol=1.0e-10,
    )


def test_eq_11_38_friction_matches_teacher_forward_flow_formula() -> None:
    num_cells = 4
    phi = np.linspace(0.3, 0.7, num_cells)
    eta = np.linspace(0.2, 0.8, num_cells)
    field = build_lean_teacher_composition_field("H2", phi, eta, SPECIES)
    U = variable_composition_primitive_to_conservative(
        rho=np.linspace(0.6, 0.45, num_cells),
        u=np.linspace(700.0, 1000.0, num_cells),
        temperature_K=np.linspace(800.0, 1100.0, num_cells),
        field=field,
        species=SPECIES,
    )
    geometry = constant_area_profile(num_cells, area=0.018)
    diameter = np.linspace(0.035, 0.045, num_cells)
    zeros = np.zeros(num_cells)

    source = teacher_eq_11_38_non_geometric_source(
        U,
        field,
        geometry,
        SPECIES,
        phi=phi,
        eta=eta,
        hydraulic_diameter_m=diameter,
        fuel_mass_flow_gradient_kg_per_s_per_m=zeros,
        fuel_axial_velocity_m_per_s=zeros,
        fuel_specific_total_enthalpy_J_per_kg=zeros,
        wall_specific_heat_gain_gradient_J_per_kg_per_m=zeros,
    )
    primitive = variable_composition_conservative_to_primitive(U, field, SPECIES)
    f = friction_coefficient_raw(phi, eta)
    expected = -0.5 * primitive.rho * primitive.u**2 * (4.0 * f / diameter)

    np.testing.assert_allclose(source[:, 0], 0.0, atol=0.0)
    np.testing.assert_allclose(source[:, 1], expected, rtol=2.0e-14, atol=1.0e-8)
    np.testing.assert_allclose(source[:, 2], 0.0, atol=0.0)


def test_explicit_dimensional_wall_heat_gradient_maps_exactly_to_energy_source() -> None:
    num_cells = 3
    field = _field(num_cells, fuel="C2H4", phi=0.6, eta=0.5)
    U = variable_composition_primitive_to_conservative(
        rho=np.array([0.55, 0.50, 0.45]),
        u=np.array([700.0, 850.0, 1000.0]),
        temperature_K=np.array([850.0, 950.0, 1050.0]),
        field=field,
        species=SPECIES,
    )
    geometry = constant_area_profile(num_cells, area=0.02)
    dqdx = np.array([-5.0e4, 0.0, 8.0e4])
    zeros = np.zeros(num_cells)
    source = teacher_eq_11_38_non_geometric_source(
        U,
        field,
        geometry,
        SPECIES,
        phi=0.6,
        eta=0.5,
        hydraulic_diameter_m=0.04,
        fuel_mass_flow_gradient_kg_per_s_per_m=zeros,
        fuel_axial_velocity_m_per_s=zeros,
        fuel_specific_total_enthalpy_J_per_kg=zeros,
        wall_specific_heat_gain_gradient_J_per_kg_per_m=dqdx,
    )
    primitive = variable_composition_conservative_to_primitive(U, field, SPECIES)
    np.testing.assert_allclose(source[:, 2], primitive.rho * primitive.u * dqdx, rtol=2.0e-14)


def test_source_adapter_rejects_reverse_flow_and_blocked_kerosene_enthalpy() -> None:
    field = _field(2)
    U = variable_composition_primitive_to_conservative(
        rho=0.5,
        u=np.array([500.0, -10.0]),
        temperature_K=900.0,
        field=field,
        species=SPECIES,
    )
    geometry = constant_area_profile(2)
    with pytest.raises(ValueError, match="forward axial flow"):
        teacher_eq_11_38_non_geometric_source(
            U,
            field,
            geometry,
            SPECIES,
            phi=0.5,
            eta=0.4,
            hydraulic_diameter_m=0.04,
            fuel_mass_flow_gradient_kg_per_s_per_m=0.0,
            fuel_axial_velocity_m_per_s=0.0,
            fuel_specific_total_enthalpy_J_per_kg=0.0,
            wall_specific_heat_gain_gradient_J_per_kg_per_m=0.0,
        )
    with pytest.raises(ValueError, match="C10H22 thermochemistry"):
        injected_fuel_specific_total_enthalpy("C10H22", 500.0, 100.0, SPECIES)


def test_injection_strength_can_be_built_from_teacher_phi_operating_point() -> None:
    fst = fuel_stoichiometric_ratio("H2")
    air_mdot = 1.2
    phi = 0.55
    expected_fuel_mdot = phi * fst * air_mdot
    gradient = localized_injector_mass_flow_gradient(4, 1, expected_fuel_mdot, 0.03)
    assert np.sum(gradient) * 0.03 == pytest.approx(expected_fuel_mdot, rel=2.0e-16)
