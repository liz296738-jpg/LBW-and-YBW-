"""Verification for fixed-composition variable-thermo SSP-RK3 time marching."""

from __future__ import annotations

import numpy as np
import pytest

from cases.studies.teacher_thermochemistry_database import build_species_database
from scramjet1d.config import GasProperties, NumericalConfig
from scramjet1d.geometry import constant_area_profile
from scramjet1d.solver import cfl_timestep, quasi_1d_rhs_transmissive, solve_quasi_1d
from scramjet1d.state import primitive_to_conservative
from scramjet1d.thermochemistry import (
    SpeciesThermoPolynomial,
    UNIVERSAL_GAS_CONSTANT_J_PER_KMOL_K,
)
from scramjet1d.time_integration import ssp_rk3_step
from scramjet1d.variable_solver import (
    solve_variable_quasi_1d,
    variable_cfl_timestep,
    variable_quasi_1d_ssp_rk3_step,
)
from scramjet1d.variable_state import (
    variable_conservative_to_primitive,
    variable_primitive_to_conservative,
)


CORE_SPECIES = build_species_database()
AIR_LIKE = {"O2": 0.233, "N2": 0.767}


def _constant_property_fixture() -> tuple[
    GasProperties, dict[str, float], dict[str, SpeciesThermoPolynomial]
]:
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


def test_variable_cfl_reduces_to_constant_gamma_cfl() -> None:
    gas, composition, species = _constant_property_fixture()
    numerical = NumericalConfig(cfl=0.42, tolerance=1.0e-6)
    rho = np.array([1.0, 0.8, 0.55, 0.4])
    u = np.array([250.0, 600.0, 900.0, 1250.0])
    T = np.array([350.0, 550.0, 800.0, 1150.0])
    p = rho * gas.R * T
    U = primitive_to_conservative(rho, u, p, gas)

    expected = cfl_timestep(U, 0.01, gas, numerical)
    actual = variable_cfl_timestep(U, 0.01, numerical, composition, species)
    assert actual == pytest.approx(expected, rel=2.0e-12, abs=1.0e-16)


def test_one_ssp_rk3_step_reduces_to_constant_property_baseline() -> None:
    gas, composition, species = _constant_property_fixture()
    rho = np.array([0.9, 0.82, 0.72, 0.62, 0.55])
    u = np.array([450.0, 600.0, 800.0, 1000.0, 1150.0])
    T = np.array([500.0, 580.0, 700.0, 850.0, 1000.0])
    p = rho * gas.R * T
    U = primitive_to_conservative(rho, u, p, gas)
    geometry = constant_area_profile(5, area=0.012)
    dx = 0.02
    dt = 1.0e-6

    baseline = ssp_rk3_step(
        U,
        dt,
        lambda state: quasi_1d_rhs_transmissive(state, geometry, dx, gas),
    )
    variable = variable_quasi_1d_ssp_rk3_step(
        U, geometry, dx, dt, composition, species
    )
    np.testing.assert_allclose(variable, baseline, rtol=2.0e-10, atol=2.0e-5)


def test_uniform_real_mixture_flow_is_preserved_over_many_steps() -> None:
    numerical = NumericalConfig(cfl=0.4, tolerance=1.0e-6)
    state = variable_primitive_to_conservative(
        0.45, 1150.0, 950.0, AIR_LIKE, CORE_SPECIES
    )
    U0 = np.repeat(state[np.newaxis, :], 12, axis=0)
    geometry = constant_area_profile(12, area=0.01)

    result = solve_variable_quasi_1d(
        U0,
        geometry,
        dx=0.01,
        t_final=4.0e-5,
        numerical=numerical,
        mass_fractions=AIR_LIKE,
        species=CORE_SPECIES,
    )

    assert result.steps > 1
    assert result.time == pytest.approx(4.0e-5, rel=0.0, abs=1.0e-15)
    np.testing.assert_allclose(result.U, U0, rtol=1.0e-13, atol=2.0e-8)


def test_short_transient_constant_property_solver_matches_baseline() -> None:
    gas, composition, species = _constant_property_fixture()
    numerical = NumericalConfig(cfl=0.25, tolerance=1.0e-6)
    n = 8
    rho = np.linspace(0.85, 0.55, n)
    u = np.linspace(500.0, 900.0, n)
    T = np.linspace(550.0, 850.0, n)
    p = rho * gas.R * T
    U0 = primitive_to_conservative(rho, u, p, gas)
    geometry = constant_area_profile(n, area=0.015)
    dx = 0.02
    t_final = 4.0e-6

    baseline = solve_quasi_1d(
        U0,
        geometry,
        dx,
        t_final,
        gas,
        numerical,
        max_steps=100,
    )
    variable = solve_variable_quasi_1d(
        U0,
        geometry,
        dx,
        t_final,
        numerical,
        composition,
        species,
        max_steps=100,
    )

    assert variable.steps == baseline.steps
    assert variable.time == baseline.time
    np.testing.assert_allclose(variable.U, baseline.U, rtol=4.0e-10, atol=5.0e-5)


def test_real_mixture_transient_remains_finite_and_source_valid() -> None:
    numerical = NumericalConfig(cfl=0.2, tolerance=1.0e-6)
    n = 10
    rho = np.linspace(0.7, 0.45, n)
    u = np.linspace(650.0, 1200.0, n)
    T = np.linspace(650.0, 1250.0, n)
    U0 = variable_primitive_to_conservative(
        rho, u, T, AIR_LIKE, CORE_SPECIES
    )
    geometry = constant_area_profile(n, area=0.011)

    result = solve_variable_quasi_1d(
        U0,
        geometry,
        dx=0.015,
        t_final=3.0e-6,
        numerical=numerical,
        mass_fractions=AIR_LIKE,
        species=CORE_SPECIES,
        max_steps=200,
    )
    primitive = variable_conservative_to_primitive(
        result.U, AIR_LIKE, CORE_SPECIES
    )
    assert np.all(np.isfinite(result.U))
    assert np.all(primitive.rho > 0.0)
    assert np.all(primitive.p > 0.0)
    assert np.all((primitive.T >= 250.0) & (primitive.T <= 3500.0))


def test_solver_respects_max_steps_guard() -> None:
    numerical = NumericalConfig(cfl=0.1, tolerance=1.0e-6)
    state = variable_primitive_to_conservative(
        0.5, 1000.0, 800.0, AIR_LIKE, CORE_SPECIES
    )
    U0 = np.repeat(state[np.newaxis, :], 4, axis=0)
    geometry = constant_area_profile(4)
    with pytest.raises(RuntimeError, match="maximum solver step count"):
        solve_variable_quasi_1d(
            U0,
            geometry,
            dx=0.001,
            t_final=1.0,
            numerical=numerical,
            mass_fractions=AIR_LIKE,
            species=CORE_SPECIES,
            max_steps=1,
        )


def test_solver_validates_geometry_and_state_shape() -> None:
    numerical = NumericalConfig()
    with pytest.raises(ValueError, match="U0 must have shape"):
        solve_variable_quasi_1d(
            [1.0, 2.0, 3.0],
            constant_area_profile(1),
            0.01,
            1.0e-6,
            numerical,
            AIR_LIKE,
            CORE_SPECIES,
        )

    state = variable_primitive_to_conservative(
        0.5, 900.0, 700.0, AIR_LIKE, CORE_SPECIES
    )
    U0 = np.repeat(state[np.newaxis, :], 3, axis=0)
    with pytest.raises(ValueError, match="geometry.num_cells"):
        solve_variable_quasi_1d(
            U0,
            constant_area_profile(4),
            0.01,
            1.0e-6,
            numerical,
            AIR_LIKE,
            CORE_SPECIES,
        )
