"""Verification for teacher Eq. (11.45)--(11.46) steady compatibility march."""

from __future__ import annotations

import numpy as np
import pytest

from cases.studies.teacher_thermochemistry_database import build_species_database
from scramjet1d.config import NumericalConfig
from scramjet1d.geometry import constant_area_profile
from scramjet1d.teacher_boundaries import TeacherStaticInletState
from scramjet1d.teacher_single_injector import build_teacher_single_injector_mapping
from scramjet1d.teacher_steady_solver import (
    normalized_teacher_variable_residual,
    solve_teacher_boundary_steady,
    teacher_eq_11_45_timestep,
    teacher_max_relative_density_change,
    teacher_variable_residual_reference,
)
from scramjet1d.variable_composition import variable_composition_primitive_to_conservative
from scramjet1d.variable_composition_solver import variable_composition_cfl_timestep


SPECIES = build_species_database()
DX = 0.02


def _mapping():
    x = np.arange(8, dtype=float) * DX
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


def _inlet():
    return TeacherStaticInletState(
        pressure_Pa=55_000.0,
        temperature_K=800.0,
        axial_velocity_m_per_s=1250.0,
    )


def _interior(mapping):
    return variable_composition_primitive_to_conservative(
        rho=0.32,
        u=1050.0,
        temperature_K=900.0,
        field=mapping.composition,
        species=SPECIES,
    )


def test_eq_11_46_density_change_uses_conservative_density_directly() -> None:
    previous = np.array([[1.0, 2.0, 3.0], [2.0, 4.0, 8.0]])
    current = np.array([[1.01, 7.0, 9.0], [1.9, 1.0, 2.0]])
    assert teacher_max_relative_density_change(previous, current) == pytest.approx(0.05)


def test_eq_11_46_rejects_nonpositive_density() -> None:
    previous = np.array([[1.0, 0.0, 1.0], [2.0, 0.0, 1.0]])
    current = previous.copy()
    current[1, 0] = 0.0
    with pytest.raises(ValueError, match="density"):
        teacher_max_relative_density_change(previous, current)


def test_eq_11_45_optional_dt0_cap_is_explicit_minimum() -> None:
    mapping = _mapping()
    U = _interior(mapping)
    numerical = NumericalConfig(cfl=0.5, tolerance=1.0e-4)
    spectral = variable_composition_cfl_timestep(
        U, DX, numerical, mapping.composition, SPECIES
    )
    assert teacher_eq_11_45_timestep(
        U, DX, numerical, mapping, SPECIES
    ) == pytest.approx(spectral)
    assert teacher_eq_11_45_timestep(
        U, DX, numerical, mapping, SPECIES, dt_cap_s=0.25 * spectral
    ) == pytest.approx(0.25 * spectral)
    assert teacher_eq_11_45_timestep(
        U, DX, numerical, mapping, SPECIES, dt_cap_s=4.0 * spectral
    ) == pytest.approx(spectral)


def test_variable_residual_reference_and_zero_residual_are_finite() -> None:
    mapping = _mapping()
    U = _interior(mapping)
    reference = teacher_variable_residual_reference(U, DX, mapping, SPECIES)
    value = normalized_teacher_variable_residual(np.zeros_like(U), reference)
    assert reference.time_scale_s > 0.0
    assert np.all(reference.conservative_scales > 0.0)
    assert value == 0.0


def test_steady_wrapper_uses_density_criterion_as_primary_stop() -> None:
    mapping = _mapping()
    geometry = constant_area_profile(mapping.composition.num_cells, area=0.025)
    U0 = _interior(mapping)
    result = solve_teacher_boundary_steady(
        U0,
        mapping,
        geometry,
        DX,
        NumericalConfig(cfl=0.02, tolerance=1.0),
        _inlet(),
        SPECIES,
        hydraulic_diameter_m=0.05,
        wall_specific_heat_gain_gradient_J_per_kg_per_m=0.0,
        max_steps=10,
    )
    assert result.converged is True
    assert result.termination_reason == "converged"
    assert result.steps == 1
    assert result.density_change <= 1.0
    assert np.isfinite(result.normalized_residual)
    assert result.density_change_history.shape == (1,)
    assert result.residual_history.shape == (1,)
    assert result.time_history_s.shape == (1,)


def test_steady_wrapper_reports_max_steps_without_false_convergence() -> None:
    mapping = _mapping()
    geometry = constant_area_profile(mapping.composition.num_cells, area=0.025)
    result = solve_teacher_boundary_steady(
        _interior(mapping),
        mapping,
        geometry,
        DX,
        NumericalConfig(cfl=0.02, tolerance=1.0e-30),
        _inlet(),
        SPECIES,
        hydraulic_diameter_m=0.05,
        wall_specific_heat_gain_gradient_J_per_kg_per_m=0.0,
        max_steps=1,
    )
    assert result.converged is False
    assert result.termination_reason == "max-steps"
    assert result.steps == 1
    assert result.density_change > 1.0e-30
    assert result.pseudo_time_s > 0.0
