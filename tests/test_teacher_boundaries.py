"""Verification for teacher variable-composition p/T/u inlet and outlet boundaries."""

from __future__ import annotations

import numpy as np
import pytest

from cases.studies.teacher_thermochemistry_database import build_species_database
from scramjet1d.config import NumericalConfig
from scramjet1d.geometry import constant_area_profile
from scramjet1d.teacher_boundaries import (
    TeacherStaticInletState,
    teacher_boundary_interface_fluxes,
    teacher_static_inlet_conservative_state,
)
from scramjet1d.teacher_boundary_solver import solve_teacher_boundary_compatibility
from scramjet1d.teacher_single_injector import build_teacher_single_injector_mapping
from scramjet1d.variable_composition import (
    variable_composition_conservative_to_primitive,
    variable_composition_primitive_to_conservative,
)
from scramjet1d.variable_composition_euler import variable_composition_internal_rusanov_fluxes
from scramjet1d.variable_euler import variable_euler_flux
from scramjet1d.variable_state import variable_conservative_to_primitive


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


def test_teacher_static_inlet_recovers_prescribed_p_T_u_and_is_supersonic_air() -> None:
    mapping = _mapping()
    inlet = _inlet()
    U = teacher_static_inlet_conservative_state(inlet, mapping, SPECIES)
    primitive = variable_conservative_to_primitive(
        U, mapping.composition.composition_at(0), SPECIES
    )
    assert float(primitive.p) == pytest.approx(inlet.pressure_Pa, rel=2.0e-11)
    assert float(primitive.T) == pytest.approx(inlet.temperature_K, abs=3.0e-7)
    assert float(primitive.u) == pytest.approx(inlet.axial_velocity_m_per_s, rel=0.0, abs=1.0e-12)
    assert float(primitive.Mach) > 1.0
    first = mapping.composition.composition_at(0)
    assert first["H2"] == 0.0 and first["H2O"] == 0.0 and first["CO2"] == 0.0


def test_boundary_fluxes_use_fixed_physical_inlet_internal_rusanov_and_extrapolated_outlet() -> None:
    mapping = _mapping()
    inlet = _inlet()
    U = _interior(mapping)
    # Perturb the first interior state: prescribed left flux must not change.
    U_perturbed = U.copy()
    U_perturbed[0, 0] *= 1.15
    U_perturbed[0, 1] *= 0.92
    U_perturbed[0, 2] *= 1.07

    fluxes = teacher_boundary_interface_fluxes(U, mapping, inlet, SPECIES)
    fluxes_perturbed = teacher_boundary_interface_fluxes(U_perturbed, mapping, inlet, SPECIES)
    inlet_U = teacher_static_inlet_conservative_state(inlet, mapping, SPECIES)
    expected_left = variable_euler_flux(
        inlet_U, mapping.composition.composition_at(0), SPECIES
    )
    np.testing.assert_allclose(fluxes[0], expected_left, rtol=0.0, atol=0.0)
    np.testing.assert_allclose(fluxes_perturbed[0], expected_left, rtol=0.0, atol=0.0)

    internal = variable_composition_internal_rusanov_fluxes(U, mapping.composition, SPECIES)
    np.testing.assert_allclose(fluxes[1:-1], internal, rtol=0.0, atol=0.0)
    expected_right = variable_euler_flux(
        U[-1], mapping.composition.composition_at(mapping.composition.num_cells - 1), SPECIES
    )
    np.testing.assert_allclose(fluxes[-1], expected_right, rtol=0.0, atol=0.0)


def test_boundary_solver_runs_short_source_enabled_transient_with_fixed_inlet() -> None:
    mapping = _mapping()
    geometry = constant_area_profile(mapping.composition.num_cells, area=0.025)
    U0 = _interior(mapping)
    result = solve_teacher_boundary_compatibility(
        U0,
        mapping,
        geometry,
        DX,
        5.0e-7,
        NumericalConfig(cfl=0.15, tolerance=1.0e-6),
        _inlet(),
        SPECIES,
        hydraulic_diameter_m=0.05,
        wall_specific_heat_gain_gradient_J_per_kg_per_m=0.0,
        max_steps=100,
    )
    primitive = variable_composition_conservative_to_primitive(
        result.U, mapping.composition, SPECIES
    )
    assert result.time == pytest.approx(5.0e-7, abs=0.0)
    assert result.steps >= 1
    assert np.all(np.isfinite(result.U))
    assert np.all(primitive.rho > 0.0)
    assert np.all(primitive.p > 0.0)
    assert np.all(primitive.T > 0.0)


def test_subsonic_prescribed_inlet_is_rejected_by_current_scramjet_adapter() -> None:
    mapping = _mapping()
    inlet = TeacherStaticInletState(
        pressure_Pa=55_000.0,
        temperature_K=800.0,
        axial_velocity_m_per_s=150.0,
    )
    with pytest.raises(ValueError, match="supersonic inlet Mach"):
        teacher_static_inlet_conservative_state(inlet, mapping, SPECIES)


def test_boundary_state_validation_rejects_nonphysical_static_inputs() -> None:
    with pytest.raises(ValueError, match="pressure and temperature"):
        TeacherStaticInletState(pressure_Pa=-1.0, temperature_K=800.0, axial_velocity_m_per_s=1000.0)
    with pytest.raises(ValueError, match="velocity"):
        TeacherStaticInletState(pressure_Pa=50_000.0, temperature_K=800.0, axial_velocity_m_per_s=0.0)
