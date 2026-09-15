"""Verification for the isolated fixed-composition variable-thermo Euler operators."""

from __future__ import annotations

import numpy as np
import pytest

from cases.studies.teacher_thermochemistry_database import build_species_database
from scramjet1d.config import GasProperties
from scramjet1d.flux import euler_flux, rusanov_flux
from scramjet1d.geometry import AreaProfile, constant_area_profile
from scramjet1d.state import primitive_to_conservative
from scramjet1d.thermochemistry import (
    SpeciesThermoPolynomial,
    UNIVERSAL_GAS_CONSTANT_J_PER_KMOL_K,
)
from scramjet1d.variable_euler import (
    variable_area_weighted_flux_residual,
    variable_euler_flux,
    variable_finite_volume_residual,
    variable_geometric_area_source,
    variable_quasi_1d_rhs_transmissive,
    variable_rusanov_flux,
    variable_transmissive_interface_fluxes,
)
from scramjet1d.variable_state import variable_primitive_to_conservative


CORE_SPECIES = build_species_database()
AIR_LIKE = {"O2": 0.233, "N2": 0.767}


def _constant_property_fixture() -> tuple[GasProperties, dict[str, float], dict[str, SpeciesThermoPolynomial]]:
    gas = GasProperties(gamma=1.35, R=300.0)
    molecular_weight = UNIVERSAL_GAS_CONSTANT_J_PER_KMOL_K / gas.R
    a1 = gas.cp / gas.R
    species = {
        "X": SpeciesThermoPolynomial(
            name="X",
            molecular_weight_kg_per_kmol=molecular_weight,
            temperature_min_K=200.0,
            temperature_max_K=4000.0,
            coefficients=(a1, 0.0, 0.0, 0.0, 0.0, 0.0),
        )
    }
    return gas, {"X": 1.0}, species


def test_variable_physical_flux_reduces_to_constant_gamma_euler_flux() -> None:
    gas, composition, species = _constant_property_fixture()
    rho = np.array([1.1, 0.7, 0.35])
    u = np.array([250.0, 900.0, 1600.0])
    T = np.array([350.0, 800.0, 1600.0])
    p = rho * gas.R * T

    baseline_U = primitive_to_conservative(rho, u, p, gas)
    variable_U = variable_primitive_to_conservative(rho, u, T, composition, species)
    np.testing.assert_allclose(variable_U, baseline_U, rtol=2.0e-15, atol=2.0e-9)
    np.testing.assert_allclose(
        variable_euler_flux(variable_U, composition, species),
        euler_flux(baseline_U, gas),
        rtol=5.0e-13,
        atol=2.0e-7,
    )


def test_variable_rusanov_reduces_to_constant_gamma_rusanov() -> None:
    gas, composition, species = _constant_property_fixture()
    rho = np.array([1.0, 0.8, 0.5])
    u = np.array([300.0, 700.0, 1200.0])
    T = np.array([400.0, 700.0, 1100.0])
    p = rho * gas.R * T
    states = primitive_to_conservative(rho, u, p, gas)

    baseline = rusanov_flux(states[:-1], states[1:], gas)
    variable = variable_rusanov_flux(states[:-1], states[1:], composition, species)
    np.testing.assert_allclose(variable, baseline, rtol=8.0e-13, atol=2.0e-7)


def test_identical_state_rusanov_equals_variable_physical_flux() -> None:
    U = variable_primitive_to_conservative(
        0.42, 1450.0, 1150.0, AIR_LIKE, CORE_SPECIES
    )
    np.testing.assert_allclose(
        variable_rusanov_flux(U, U, AIR_LIKE, CORE_SPECIES),
        variable_euler_flux(U, AIR_LIKE, CORE_SPECIES),
        rtol=1.0e-13,
        atol=1.0e-7,
    )


def test_uniform_state_constant_area_rhs_is_zero() -> None:
    state = variable_primitive_to_conservative(
        0.5, 1200.0, 900.0, AIR_LIKE, CORE_SPECIES
    )
    states = np.repeat(state[np.newaxis, :], 8, axis=0)
    geometry = constant_area_profile(8, area=0.01)
    rhs = variable_quasi_1d_rhs_transmissive(
        states, geometry, 0.02, AIR_LIKE, CORE_SPECIES
    )
    np.testing.assert_allclose(rhs, 0.0, rtol=0.0, atol=5.0e-9)


def test_constant_area_residual_is_globally_conservative() -> None:
    rho = np.linspace(0.7, 0.35, 9)
    u = np.linspace(700.0, 1500.0, 9)
    T = np.linspace(600.0, 1400.0, 9)
    states = variable_primitive_to_conservative(
        rho, u, T, AIR_LIKE, CORE_SPECIES
    )
    dx = 0.015
    faces = variable_transmissive_interface_fluxes(
        states, AIR_LIKE, CORE_SPECIES
    )
    residual = variable_finite_volume_residual(faces, dx)

    integrated = np.sum(residual, axis=0) * dx
    expected = -(faces[-1] - faces[0])
    np.testing.assert_allclose(integrated, expected, rtol=2.0e-13, atol=2.0e-7)


def test_constant_area_weighted_operator_reduces_to_plain_finite_volume() -> None:
    rho = np.array([0.9, 0.8, 0.65, 0.5])
    u = np.array([500.0, 800.0, 1100.0, 1400.0])
    T = np.array([500.0, 700.0, 900.0, 1200.0])
    states = variable_primitive_to_conservative(
        rho, u, T, AIR_LIKE, CORE_SPECIES
    )
    faces = variable_transmissive_interface_fluxes(
        states, AIR_LIKE, CORE_SPECIES
    )
    geometry = constant_area_profile(4, area=0.023)
    dx = 0.01

    np.testing.assert_allclose(
        variable_area_weighted_flux_residual(faces, geometry, dx),
        variable_finite_volume_residual(faces, dx),
        rtol=2.0e-15,
        atol=2.0e-8,
    )


def test_variable_geometric_source_uses_recovered_local_pressure() -> None:
    rho = np.array([0.8, 0.6, 0.4])
    u = np.array([700.0, 1000.0, 1300.0])
    T = np.array([650.0, 950.0, 1350.0])
    states = variable_primitive_to_conservative(
        rho, u, T, AIR_LIKE, CORE_SPECIES
    )
    geometry = AreaProfile(
        cell_area=np.array([0.0105, 0.0115, 0.0125]),
        face_area=np.array([0.0100, 0.0110, 0.0120, 0.0130]),
    )
    dx = 0.05
    source = variable_geometric_area_source(
        states, geometry, dx, AIR_LIKE, CORE_SPECIES
    )

    # R(Y) is composition-only for the ideal mixture; evaluate one state to get it.
    from scramjet1d.thermochemistry import mixture_thermo_state

    R_mix = mixture_thermo_state(900.0, AIR_LIKE, CORE_SPECIES).gas_constant_J_per_kg_K
    p = rho * R_mix * T
    expected_momentum = p * np.diff(geometry.face_area) / geometry.cell_area / dx
    np.testing.assert_allclose(source[:, 0], 0.0, atol=0.0)
    np.testing.assert_allclose(source[:, 2], 0.0, atol=0.0)
    np.testing.assert_allclose(source[:, 1], expected_momentum, rtol=5.0e-10, atol=1.0e-7)


def test_transmissive_interface_flux_count_and_boundary_physical_flux() -> None:
    states = variable_primitive_to_conservative(
        np.array([0.6, 0.5, 0.4]),
        np.array([800.0, 1100.0, 1400.0]),
        np.array([700.0, 900.0, 1200.0]),
        AIR_LIKE,
        CORE_SPECIES,
    )
    faces = variable_transmissive_interface_fluxes(
        states, AIR_LIKE, CORE_SPECIES
    )
    assert faces.shape == (4, 3)
    np.testing.assert_allclose(
        faces[0], variable_euler_flux(states[0], AIR_LIKE, CORE_SPECIES), rtol=1.0e-13
    )
    np.testing.assert_allclose(
        faces[-1], variable_euler_flux(states[-1], AIR_LIKE, CORE_SPECIES), rtol=1.0e-13
    )


def test_variable_euler_rejects_bad_state_shapes_and_geometry_mismatch() -> None:
    with pytest.raises(ValueError, match="U_left last dimension"):
        variable_rusanov_flux([1.0, 2.0], [1.0, 2.0], AIR_LIKE, CORE_SPECIES)

    states = variable_primitive_to_conservative(
        np.array([0.6, 0.5]),
        np.array([800.0, 900.0]),
        np.array([700.0, 800.0]),
        AIR_LIKE,
        CORE_SPECIES,
    )
    geometry = constant_area_profile(3)
    with pytest.raises(ValueError, match="cell count"):
        variable_geometric_area_source(
            states, geometry, 0.01, AIR_LIKE, CORE_SPECIES
        )
