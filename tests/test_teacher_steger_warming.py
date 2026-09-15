"""Verification for teacher Chapter 11 Eqs. (11.42)--(11.44)."""

from __future__ import annotations

import numpy as np
import pytest

from cases.studies.teacher_thermochemistry_database import build_species_database
from scramjet1d.config import GasProperties
from scramjet1d.steger_warming import steger_warming_flux, steger_warming_split_flux
from scramjet1d.teacher_steger_warming import (
    teacher_smoothed_eigenvalue_split,
    teacher_variable_characteristic_speeds,
    teacher_variable_composition_internal_steger_warming_fluxes,
    teacher_variable_steger_warming_flux,
    teacher_variable_steger_warming_split_flux,
)
from scramjet1d.thermochemistry import (
    SpeciesThermoPolynomial,
    UNIVERSAL_GAS_CONSTANT_J_PER_KMOL_K,
)
from scramjet1d.variable_composition import TeacherCompositionField
from scramjet1d.variable_euler import variable_euler_flux
from scramjet1d.variable_state import variable_primitive_to_conservative


SPECIES = build_species_database()
AIR = {"O2": 0.233, "N2": 0.767}


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


def test_eq_11_44_split_preserves_eigenvalue_and_raw_limit() -> None:
    eigenvalues = np.array([-500.0, -2.0, 0.0, 3.0, 900.0])
    plus, minus = teacher_smoothed_eigenvalue_split(
        eigenvalues, epsilon_m_per_s=25.0
    )
    np.testing.assert_allclose(plus + minus, eigenvalues, rtol=0.0, atol=1.0e-13)
    assert np.all(plus >= 0.0)
    assert np.all(minus <= 0.0)

    raw_plus, raw_minus = teacher_smoothed_eigenvalue_split(
        eigenvalues, epsilon_m_per_s=0.0
    )
    np.testing.assert_allclose(raw_plus, 0.5 * (eigenvalues + np.abs(eigenvalues)))
    np.testing.assert_allclose(raw_minus, 0.5 * (eigenvalues - np.abs(eigenvalues)))


def test_epsilon_is_explicit_and_validated() -> None:
    with pytest.raises(TypeError):
        teacher_smoothed_eigenvalue_split(np.array([1.0]))  # type: ignore[call-arg]
    for bad in (-1.0, np.inf, np.nan):
        with pytest.raises(ValueError, match="epsilon_m_per_s"):
            teacher_smoothed_eigenvalue_split(np.array([1.0]), epsilon_m_per_s=bad)


def test_teacher_characteristic_order_is_u_u_minus_c_u_plus_c() -> None:
    U = variable_primitive_to_conservative(0.45, 1250.0, 900.0, AIR, SPECIES)
    speeds = teacher_variable_characteristic_speeds(U, AIR, SPECIES)
    assert speeds.shape == (3,)
    assert speeds[0] == pytest.approx(1250.0, abs=2.0e-9)
    assert speeds[1] < speeds[0] < speeds[2]
    assert speeds[2] - speeds[0] == pytest.approx(speeds[0] - speeds[1], rel=2.0e-12)


def test_literal_eq_11_42_exposes_variable_thermochemistry_energy_compatibility_gap() -> None:
    """Do not hide the textbook/perfect-gas split's energy-identity limitation.

    With source-backed variable cp and absolute species energy, the literal
    Eq.11.42 split still reconstructs mass and momentum flux, but its energy
    recombination is not the repository's physical Euler energy flux.  This is
    a scientific integration blocker, not a tolerance issue.
    """

    U = variable_primitive_to_conservative(0.8, 350.0, 650.0, AIR, SPECIES)
    plus, minus = teacher_variable_steger_warming_split_flux(
        U, AIR, SPECIES, epsilon_m_per_s=37.5
    )
    reconstructed = plus + minus
    physical = variable_euler_flux(U, AIR, SPECIES)
    np.testing.assert_allclose(reconstructed[:2], physical[:2], rtol=2.0e-11, atol=3.0e-5)
    assert not np.isclose(reconstructed[2], physical[2], rtol=1.0e-3, atol=1.0)
    assert abs(reconstructed[2] - physical[2]) / abs(physical[2]) > 0.01


def test_constant_property_raw_split_reduces_to_existing_steger_warming() -> None:
    gas, composition, species = _constant_property_fixture()
    U = variable_primitive_to_conservative(0.7, 850.0, 1100.0, composition, species)
    new_plus, new_minus = teacher_variable_steger_warming_split_flux(
        U, composition, species, epsilon_m_per_s=0.0
    )
    old_plus, old_minus = steger_warming_split_flux(U, gas)
    np.testing.assert_allclose(new_plus, old_plus, rtol=2.0e-11, atol=3.0e-5)
    np.testing.assert_allclose(new_minus, old_minus, rtol=2.0e-11, atol=3.0e-5)


def test_constant_property_interface_reduces_to_existing_steger_warming() -> None:
    gas, composition, species = _constant_property_fixture()
    left = variable_primitive_to_conservative(0.8, 700.0, 900.0, composition, species)
    right = variable_primitive_to_conservative(0.55, 1150.0, 1250.0, composition, species)
    new_flux = teacher_variable_steger_warming_flux(
        left,
        right,
        composition,
        composition,
        species,
        epsilon_m_per_s=0.0,
    )
    old_flux = steger_warming_flux(left, right, gas)
    np.testing.assert_allclose(new_flux, old_flux, rtol=2.0e-11, atol=4.0e-5)


def test_variable_composition_internal_fluxes_use_cell_local_compositions() -> None:
    names = ("H2", "O2", "N2", "AR", "H2O", "CO2")
    rows = np.array(
        [
            [0.04, 0.20, 0.72, 0.01, 0.03, 0.00],
            [0.02, 0.16, 0.70, 0.01, 0.08, 0.03],
            [0.01, 0.12, 0.68, 0.01, 0.12, 0.06],
        ]
    )
    rows = rows / np.sum(rows, axis=1)[:, None]
    field = TeacherCompositionField(names, rows)
    states = np.vstack(
        [
            variable_primitive_to_conservative(
                rho, u, T, field.composition_at(i), SPECIES
            )
            for i, (rho, u, T) in enumerate(
                [(0.62, 700.0, 800.0), (0.48, 1050.0, 1150.0), (0.34, 1450.0, 1550.0)]
            )
        ]
    )
    fluxes = teacher_variable_composition_internal_steger_warming_fluxes(
        states, field, SPECIES, epsilon_m_per_s=20.0
    )
    assert fluxes.shape == (2, 3)
    assert np.all(np.isfinite(fluxes))
    np.testing.assert_allclose(
        fluxes[0],
        teacher_variable_steger_warming_flux(
            states[0],
            states[1],
            field.composition_at(0),
            field.composition_at(1),
            SPECIES,
            epsilon_m_per_s=20.0,
        ),
        rtol=0.0,
        atol=0.0,
    )


def test_near_sonic_smoothing_is_finite_and_changes_zero_characteristic_split() -> None:
    U0 = variable_primitive_to_conservative(0.5, 900.0, 1000.0, AIR, SPECIES)
    speeds0 = teacher_variable_characteristic_speeds(U0, AIR, SPECIES)
    sound_speed = speeds0[2] - speeds0[0]
    U = variable_primitive_to_conservative(0.5, sound_speed, 1000.0, AIR, SPECIES)
    speeds = teacher_variable_characteristic_speeds(U, AIR, SPECIES)
    assert speeds[1] == pytest.approx(0.0, abs=3.0e-7)

    raw_plus, raw_minus = teacher_smoothed_eigenvalue_split(
        speeds, epsilon_m_per_s=0.0
    )
    smooth_plus, smooth_minus = teacher_smoothed_eigenvalue_split(
        speeds, epsilon_m_per_s=30.0
    )
    assert np.all(np.isfinite(smooth_plus))
    assert np.all(np.isfinite(smooth_minus))
    assert smooth_plus[1] > raw_plus[1]
    assert smooth_minus[1] < raw_minus[1]
    np.testing.assert_allclose(smooth_plus + smooth_minus, speeds, atol=1.0e-13)


def test_state_and_field_guards_remain_explicit() -> None:
    with pytest.raises(ValueError, match="shape"):
        teacher_variable_characteristic_speeds([1.0, 2.0], AIR, SPECIES)

    field = TeacherCompositionField(("O2", "N2"), np.array([[0.233, 0.767]]))
    U = variable_primitive_to_conservative(0.5, 1000.0, 900.0, AIR, SPECIES)
    with pytest.raises(ValueError, match="at least two"):
        teacher_variable_composition_internal_steger_warming_fluxes(
            U[None, :], field, SPECIES, epsilon_m_per_s=0.0
        )
