"""Regression tests for fixed-composition variable-thermochemistry state recovery."""

from __future__ import annotations

import numpy as np
import pytest

from cases.studies.teacher_thermochemistry_database import build_species_database
from scramjet1d.thermochemistry import mixture_thermo_state
from scramjet1d.variable_state import (
    common_temperature_bounds,
    variable_conservative_to_primitive,
    variable_primitive_to_conservative,
)


SPECIES = build_species_database()
AIR_LIKE = {"O2": 0.233, "N2": 0.767}
VITIATED_LIKE = {"O2": 0.20, "N2": 0.55, "H2O": 0.20, "CO2": 0.05}
H2_RICH = {"H2": 0.10, "O2": 0.20, "N2": 0.60, "H2O": 0.10}
C2H4_MIX = {"C2H4": 0.05, "O2": 0.22, "N2": 0.68, "CO2": 0.05}


def _assert_round_trip(rho: np.ndarray, u: np.ndarray, T: np.ndarray, composition: dict[str, float]) -> None:
    U = variable_primitive_to_conservative(rho, u, T, composition, SPECIES)
    recovered = variable_conservative_to_primitive(U, composition, SPECIES)

    np.testing.assert_allclose(recovered.rho, rho, rtol=0.0, atol=1.0e-13)
    np.testing.assert_allclose(recovered.u, u, rtol=0.0, atol=1.0e-12)
    np.testing.assert_allclose(recovered.T, T, rtol=0.0, atol=2.0e-7)

    expected_p = np.empty_like(T, dtype=float)
    expected_gamma = np.empty_like(T, dtype=float)
    expected_R = np.empty_like(T, dtype=float)
    expected_cp = np.empty_like(T, dtype=float)
    expected_h = np.empty_like(T, dtype=float)
    for index in np.ndindex(T.shape):
        thermo = mixture_thermo_state(float(T[index]), composition, SPECIES)
        expected_p[index] = rho[index] * thermo.gas_constant_J_per_kg_K * T[index]
        expected_gamma[index] = thermo.gamma
        expected_R[index] = thermo.gas_constant_J_per_kg_K
        expected_cp[index] = thermo.cp_J_per_kg_K
        expected_h[index] = thermo.specific_enthalpy_J_per_kg

    np.testing.assert_allclose(recovered.p, expected_p, rtol=5.0e-10, atol=1.0e-7)
    np.testing.assert_allclose(recovered.gamma, expected_gamma, rtol=5.0e-10, atol=1.0e-12)
    np.testing.assert_allclose(recovered.R, expected_R, rtol=0.0, atol=1.0e-12)
    np.testing.assert_allclose(recovered.cp, expected_cp, rtol=5.0e-10, atol=1.0e-8)
    np.testing.assert_allclose(recovered.h, expected_h, rtol=5.0e-10, atol=1.0e-4)


def test_air_like_scalar_round_trip() -> None:
    U = variable_primitive_to_conservative(0.45, 1500.0, 900.0, AIR_LIKE, SPECIES)
    assert U.shape == (3,)

    recovered = variable_conservative_to_primitive(U, AIR_LIKE, SPECIES)
    assert recovered.rho.shape == ()
    assert recovered.T == pytest.approx(900.0, abs=2.0e-7)
    assert recovered.u == pytest.approx(1500.0, abs=1.0e-12)
    assert recovered.p > 0.0
    assert recovered.gamma > 1.0


def test_vector_round_trip_across_low_and_high_temperature_intervals() -> None:
    rho = np.array([1.0, 0.7, 0.4, 0.2])
    u = np.array([200.0, 900.0, 1500.0, 2200.0])
    T = np.array([300.0, 999.0, 1001.0, 2500.0])
    _assert_round_trip(rho, u, T, AIR_LIKE)


def test_exact_switch_temperature_round_trip_is_stable() -> None:
    rho = np.array([0.8, 0.5, 0.3])
    u = np.array([400.0, 1200.0, 1800.0])
    T = np.array([999.999, 1000.0, 1000.001])
    _assert_round_trip(rho, u, T, VITIATED_LIKE)


def test_hydrogen_and_ethylene_branches_round_trip() -> None:
    for composition in (H2_RICH, C2H4_MIX):
        rho = np.array([0.65, 0.32])
        u = np.array([1100.0, 1900.0])
        T = np.array([700.0, 1800.0])
        _assert_round_trip(rho, u, T, composition)


def test_common_temperature_bounds_ignore_zero_fraction_species() -> None:
    composition = {"O2": 0.233, "N2": 0.767, "AR": 0.0}
    lower, upper = common_temperature_bounds(composition, SPECIES)
    assert lower == pytest.approx(250.0)
    assert upper == pytest.approx(5000.0)


def test_common_temperature_bounds_respect_active_species_limits() -> None:
    lower, upper = common_temperature_bounds(AIR_LIKE, SPECIES)
    assert lower == pytest.approx(250.0)
    assert upper == pytest.approx(5000.0)

    lower, upper = common_temperature_bounds(C2H4_MIX, SPECIES)
    assert lower == pytest.approx(200.0)
    assert upper == pytest.approx(3500.0)


def test_primitive_path_rejects_temperature_extrapolation() -> None:
    with pytest.raises(ValueError, match="common range"):
        variable_primitive_to_conservative(1.0, 100.0, 199.0, C2H4_MIX, SPECIES)
    with pytest.raises(ValueError, match="common range"):
        variable_primitive_to_conservative(1.0, 100.0, 3501.0, C2H4_MIX, SPECIES)


def test_conservative_path_rejects_internal_energy_outside_source_temperature_range() -> None:
    U = variable_primitive_to_conservative(1.0, 0.0, 300.0, AIR_LIKE, SPECIES)
    bad = U.copy()
    bad[2] -= 2.0e6
    with pytest.raises(ValueError, match="outside the supplied temperature bracket"):
        variable_conservative_to_primitive(bad, AIR_LIKE, SPECIES)


def test_invalid_density_and_nonfinite_states_are_rejected() -> None:
    with pytest.raises(ValueError, match="rho must be finite and strictly positive"):
        variable_primitive_to_conservative(0.0, 100.0, 500.0, AIR_LIKE, SPECIES)
    with pytest.raises(ValueError, match="U must be finite"):
        variable_conservative_to_primitive([1.0, np.nan, 10.0], AIR_LIKE, SPECIES)
    with pytest.raises(ValueError, match="rho must be strictly positive"):
        variable_conservative_to_primitive([0.0, 0.0, 0.0], AIR_LIKE, SPECIES)


def test_mass_fraction_validation_is_not_silently_renormalized() -> None:
    with pytest.raises(ValueError, match="mass fractions must sum to one"):
        variable_primitive_to_conservative(
            1.0,
            100.0,
            500.0,
            {"O2": 0.2, "N2": 0.7},
            SPECIES,
        )


def test_absolute_energy_datum_is_allowed_to_be_negative_when_thermochemically_valid() -> None:
    composition = {"CO2": 1.0}
    U = variable_primitive_to_conservative(1.0, 0.0, 300.0, composition, SPECIES)
    assert U[2] < 0.0
    recovered = variable_conservative_to_primitive(U, composition, SPECIES)
    assert recovered.T == pytest.approx(300.0, abs=2.0e-7)
    assert recovered.p > 0.0


def test_mach_uses_local_variable_gamma_and_gas_constant() -> None:
    rho = np.array([0.6, 0.6])
    u = np.array([1000.0, 1000.0])
    T = np.array([500.0, 2500.0])
    U = variable_primitive_to_conservative(rho, u, T, AIR_LIKE, SPECIES)
    recovered = variable_conservative_to_primitive(U, AIR_LIKE, SPECIES)

    expected = u / np.sqrt(recovered.gamma * recovered.R * recovered.T)
    np.testing.assert_allclose(recovered.Mach, expected, rtol=1.0e-12, atol=0.0)
    assert recovered.gamma[0] != pytest.approx(recovered.gamma[1], rel=1.0e-4)
