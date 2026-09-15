"""Verification for prescribed-composition SSP-RK3 compatibility marching."""

from __future__ import annotations

import numpy as np
import pytest

from cases.studies.teacher_thermochemistry_database import build_species_database
from scramjet1d.config import NumericalConfig
from scramjet1d.geometry import constant_area_profile
from scramjet1d.variable_composition import (
    build_lean_teacher_composition_field,
    variable_composition_conservative_to_primitive,
    variable_composition_primitive_to_conservative,
)
from scramjet1d.variable_composition_solver import (
    solve_prescribed_composition_quasi_1d,
    variable_composition_cfl_timestep,
    variable_composition_quasi_1d_ssp_rk3_step,
)
from scramjet1d.variable_solver import (
    solve_variable_quasi_1d,
    variable_cfl_timestep,
    variable_quasi_1d_ssp_rk3_step,
)


SPECIES = build_species_database()
NUMERICAL = NumericalConfig(cfl=0.35, tolerance=1.0e-6)


def _uniform_field(num_cells: int):
    return build_lean_teacher_composition_field(
        "H2",
        phi=np.full(num_cells, 0.55),
        eta=np.full(num_cells, 0.45),
        species=SPECIES,
    )


def test_cfl_reduces_to_fixed_composition_variable_solver() -> None:
    field = _uniform_field(5)
    composition = field.composition_at(0)
    U = variable_composition_primitive_to_conservative(
        rho=np.linspace(0.60, 0.35, 5),
        u=np.linspace(700.0, 1450.0, 5),
        temperature_K=np.linspace(650.0, 1450.0, 5),
        field=field,
        species=SPECIES,
    )
    dx = 0.012

    expected = variable_cfl_timestep(U, dx, NUMERICAL, composition, SPECIES)
    actual = variable_composition_cfl_timestep(U, dx, NUMERICAL, field, SPECIES)
    assert actual == pytest.approx(expected, rel=2.0e-13, abs=0.0)


def test_one_rk3_step_reduces_to_fixed_composition_path() -> None:
    field = _uniform_field(6)
    composition = field.composition_at(0)
    U = variable_composition_primitive_to_conservative(
        rho=np.linspace(0.62, 0.34, 6),
        u=np.linspace(750.0, 1500.0, 6),
        temperature_K=np.linspace(700.0, 1500.0, 6),
        field=field,
        species=SPECIES,
    )
    geometry = constant_area_profile(6, area=0.018)
    dx = 0.01
    dt = 0.2 * variable_composition_cfl_timestep(
        U, dx, NUMERICAL, field, SPECIES
    )

    expected = variable_quasi_1d_ssp_rk3_step(
        U, geometry, dx, dt, composition, SPECIES
    )
    actual = variable_composition_quasi_1d_ssp_rk3_step(
        U, field, geometry, dx, dt, SPECIES
    )
    np.testing.assert_allclose(actual, expected, rtol=2.0e-11, atol=3.0e-6)


def test_short_solver_reduces_to_fixed_composition_path() -> None:
    field = _uniform_field(5)
    composition = field.composition_at(0)
    U0 = variable_composition_primitive_to_conservative(
        rho=np.linspace(0.58, 0.38, 5),
        u=np.linspace(800.0, 1350.0, 5),
        temperature_K=np.linspace(750.0, 1300.0, 5),
        field=field,
        species=SPECIES,
    )
    geometry = constant_area_profile(5, area=0.02)
    dx = 0.015
    t_final = 0.15 * variable_composition_cfl_timestep(
        U0, dx, NUMERICAL, field, SPECIES
    )

    expected = solve_variable_quasi_1d(
        U0,
        geometry,
        dx,
        t_final,
        NUMERICAL,
        composition,
        SPECIES,
        max_steps=10,
    )
    actual = solve_prescribed_composition_quasi_1d(
        U0,
        field,
        geometry,
        dx,
        t_final,
        NUMERICAL,
        SPECIES,
        max_steps=10,
    )

    assert actual.time == pytest.approx(t_final, rel=0.0, abs=1.0e-18)
    assert actual.steps == expected.steps == 1
    np.testing.assert_allclose(actual.U, expected.U, rtol=2.0e-11, atol=3.0e-6)


def test_varying_composition_short_transient_remains_thermochemically_valid() -> None:
    field = build_lean_teacher_composition_field(
        "C2H4",
        phi=np.linspace(0.25, 0.80, 7),
        eta=np.linspace(0.10, 0.95, 7),
        species=SPECIES,
    )
    U0 = variable_composition_primitive_to_conservative(
        rho=np.linspace(0.62, 0.32, 7),
        u=np.linspace(750.0, 1500.0, 7),
        temperature_K=np.linspace(700.0, 1500.0, 7),
        field=field,
        species=SPECIES,
    )
    geometry = constant_area_profile(7, area=0.02)
    dx = 0.012
    t_final = 0.10 * variable_composition_cfl_timestep(
        U0, dx, NUMERICAL, field, SPECIES
    )

    result = solve_prescribed_composition_quasi_1d(
        U0,
        field,
        geometry,
        dx,
        t_final,
        NUMERICAL,
        SPECIES,
        max_steps=10,
    )
    primitive = variable_composition_conservative_to_primitive(
        result.U, field, SPECIES
    )

    assert result.steps == 1
    assert result.time == pytest.approx(t_final, rel=0.0, abs=1.0e-18)
    assert np.all(np.isfinite(result.U))
    assert np.all(primitive.rho > 0.0)
    assert np.all(primitive.p > 0.0)
    assert np.all(primitive.T > 0.0)
    assert np.all(primitive.gamma > 1.0)


def test_uniform_flow_is_preserved_when_composition_is_uniform() -> None:
    field = _uniform_field(8)
    U0 = variable_composition_primitive_to_conservative(
        rho=0.5,
        u=1200.0,
        temperature_K=950.0,
        field=field,
        species=SPECIES,
    )
    geometry = constant_area_profile(8, area=0.015)
    dx = 0.01
    dt = 0.25 * variable_composition_cfl_timestep(
        U0, dx, NUMERICAL, field, SPECIES
    )

    result = variable_composition_quasi_1d_ssp_rk3_step(
        U0, field, geometry, dx, dt, SPECIES
    )
    np.testing.assert_allclose(result, U0, rtol=2.0e-14, atol=2.0e-8)


def test_solver_guards_geometry_and_step_limit() -> None:
    field = _uniform_field(3)
    U0 = variable_composition_primitive_to_conservative(
        rho=0.5,
        u=1000.0,
        temperature_K=900.0,
        field=field,
        species=SPECIES,
    )
    with pytest.raises(ValueError, match="geometry.num_cells"):
        solve_prescribed_composition_quasi_1d(
            U0,
            field,
            constant_area_profile(4),
            0.01,
            1.0e-6,
            NUMERICAL,
            SPECIES,
        )

    geometry = constant_area_profile(3)
    dt_cfl = variable_composition_cfl_timestep(
        U0, 0.01, NUMERICAL, field, SPECIES
    )
    with pytest.raises(RuntimeError, match="maximum solver step count"):
        solve_prescribed_composition_quasi_1d(
            U0,
            field,
            geometry,
            0.01,
            2.5 * dt_cfl,
            NUMERICAL,
            SPECIES,
            max_steps=1,
        )
