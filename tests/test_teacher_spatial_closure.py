"""Verification for the source-aligned Chapter 11 spatial composition closure."""

from __future__ import annotations

import numpy as np
import pytest

from cases.studies.teacher_thermochemistry_database import build_species_database
from scramjet1d.config import NumericalConfig
from scramjet1d.geometry import constant_area_profile
from scramjet1d.teacher_combustion import (
    fuel_stoichiometric_ratio,
    lean_reaction_mass_fractions,
    mixing_length,
)
from scramjet1d.teacher_efficiency import combustion_efficiency_from_fuel_mass_rates
from scramjet1d.teacher_spatial_closure import build_teacher_lean_spatial_closure
from scramjet1d.variable_composition import variable_composition_primitive_to_conservative
from scramjet1d.variable_composition_solver import (
    solve_prescribed_composition_quasi_1d,
    variable_composition_cfl_timestep,
)


SPECIES = build_species_database()


def test_equivalence_ratio_is_exact_teacher_eq_11_23() -> None:
    fst = fuel_stoichiometric_ratio("H2")
    air_flow = 2.0
    target_phi = 0.60
    fuel_flow = target_phi * fst * air_flow

    closure = build_teacher_lean_spatial_closure(
        fuel="H2",
        injected_fuel_mass_flow_rate_kg_per_s=fuel_flow,
        incoming_air_mass_flow_rate_kg_per_s=air_flow,
        x_from_injector_m=np.array([0.0, 0.05, 0.10]),
        combustor_height_m=np.full(3, 0.04),
        C_m=30.0,
        injection_mode="parallel",
        species=SPECIES,
    )
    np.testing.assert_allclose(closure.equivalence_ratio, target_phi, rtol=0.0, atol=2.0e-15)


def test_local_mixing_length_uses_local_height_and_teacher_eq_11_20() -> None:
    fst = fuel_stoichiometric_ratio("C2H4")
    phi = 0.72
    heights = np.array([0.030, 0.036, 0.045])
    closure = build_teacher_lean_spatial_closure(
        fuel="C2H4",
        injected_fuel_mass_flow_rate_kg_per_s=phi * fst,
        incoming_air_mass_flow_rate_kg_per_s=1.0,
        x_from_injector_m=np.array([0.0, 0.04, 0.08]),
        combustor_height_m=heights,
        C_m=35.0,
        injection_mode="strut",
        A=2.2,
        species=SPECIES,
    )
    expected = np.array([mixing_length(phi, b, 35.0) for b in heights])
    np.testing.assert_allclose(closure.mixing_length_m, expected, rtol=2.0e-15, atol=0.0)


def test_parallel_raw_efficiency_and_explicit_saturation_are_separate() -> None:
    fst = fuel_stoichiometric_ratio("H2")
    phi = 0.5
    height = 0.04
    Lm = mixing_length(phi, height, 30.0)
    x = np.array([0.0, 0.5 * Lm, Lm, 1.25 * Lm])

    closure = build_teacher_lean_spatial_closure(
        fuel="H2",
        injected_fuel_mass_flow_rate_kg_per_s=phi * fst,
        incoming_air_mass_flow_rate_kg_per_s=1.0,
        x_from_injector_m=x,
        combustor_height_m=np.full(x.size, height),
        C_m=30.0,
        injection_mode="parallel",
        species=SPECIES,
    )
    np.testing.assert_allclose(
        closure.raw_mixing_efficiency,
        np.array([0.0, 0.5, 1.0, 1.25]),
        rtol=2.0e-15,
        atol=2.0e-15,
    )
    np.testing.assert_allclose(
        closure.combustion_efficiency,
        np.array([0.0, 0.5, 1.0, 1.0]),
        rtol=0.0,
        atol=2.0e-15,
    )


def test_normal_injection_raw_value_above_one_is_preserved_but_physical_eta_saturates() -> None:
    fst = fuel_stoichiometric_ratio("H2")
    phi = 0.5
    height = 0.04
    Lm = mixing_length(phi, height, 30.0)
    closure = build_teacher_lean_spatial_closure(
        fuel="H2",
        injected_fuel_mass_flow_rate_kg_per_s=phi * fst,
        incoming_air_mass_flow_rate_kg_per_s=1.0,
        x_from_injector_m=np.array([Lm]),
        combustor_height_m=np.array([height]),
        C_m=30.0,
        injection_mode="normal",
        alpha=0.20,
        species=SPECIES,
    )
    assert closure.raw_mixing_efficiency[0] > 1.0
    assert closure.combustion_efficiency[0] == pytest.approx(1.0, abs=0.0)


def test_residual_fuel_reconstructs_same_eq_11_18_efficiency() -> None:
    fst = fuel_stoichiometric_ratio("C2H4")
    fuel_flow = 0.65 * fst * 1.5
    closure = build_teacher_lean_spatial_closure(
        fuel="C2H4",
        injected_fuel_mass_flow_rate_kg_per_s=fuel_flow,
        incoming_air_mass_flow_rate_kg_per_s=1.5,
        x_from_injector_m=np.array([0.0, 0.05, 0.10]),
        combustor_height_m=np.full(3, 0.035),
        C_m=32.0,
        injection_mode="parallel",
        species=SPECIES,
    )
    reconstructed = combustion_efficiency_from_fuel_mass_rates(
        np.full(3, fuel_flow), closure.residual_fuel_mass_flow_rate_kg_per_s
    )
    np.testing.assert_allclose(reconstructed, closure.combustion_efficiency, atol=2.0e-15)


def test_composition_rows_equal_direct_teacher_lean_equations() -> None:
    fst = fuel_stoichiometric_ratio("H2")
    phi = 0.55
    closure = build_teacher_lean_spatial_closure(
        fuel="H2",
        injected_fuel_mass_flow_rate_kg_per_s=phi * fst,
        incoming_air_mass_flow_rate_kg_per_s=1.0,
        x_from_injector_m=np.array([0.0, 0.04, 0.08]),
        combustor_height_m=np.full(3, 0.035),
        C_m=28.0,
        injection_mode="strut",
        A=2.4,
        species=SPECIES,
    )
    for index, eta in enumerate(closure.combustion_efficiency):
        expected = lean_reaction_mass_fractions("H2", phi, float(eta), SPECIES)
        actual = closure.composition.composition_at(index)
        assert actual.keys() == expected.keys()
        for name in actual:
            assert actual[name] == pytest.approx(expected[name], rel=0.0, abs=2.0e-15)


def test_lean_and_thermochemistry_gates_remain_explicit() -> None:
    with pytest.raises(ValueError, match="lean-only"):
        build_teacher_lean_spatial_closure(
            fuel="H2",
            injected_fuel_mass_flow_rate_kg_per_s=1.05 * fuel_stoichiometric_ratio("H2"),
            incoming_air_mass_flow_rate_kg_per_s=1.0,
            x_from_injector_m=np.array([0.01]),
            combustor_height_m=np.array([0.04]),
            C_m=30.0,
            injection_mode="parallel",
            species=SPECIES,
        )
    with pytest.raises(ValueError, match="C10H22 thermochemistry"):
        build_teacher_lean_spatial_closure(
            fuel="C10H22",
            injected_fuel_mass_flow_rate_kg_per_s=0.03,
            incoming_air_mass_flow_rate_kg_per_s=1.0,
            x_from_injector_m=np.array([0.01]),
            combustor_height_m=np.array([0.04]),
            C_m=30.0,
            injection_mode="parallel",
            species=SPECIES,
        )


def test_spatial_closure_field_runs_through_prescribed_composition_solver() -> None:
    num_cells = 6
    fst = fuel_stoichiometric_ratio("H2")
    closure = build_teacher_lean_spatial_closure(
        fuel="H2",
        injected_fuel_mass_flow_rate_kg_per_s=0.50 * fst,
        incoming_air_mass_flow_rate_kg_per_s=1.0,
        x_from_injector_m=np.linspace(0.0, 0.10, num_cells),
        combustor_height_m=np.full(num_cells, 0.04),
        C_m=30.0,
        injection_mode="parallel",
        species=SPECIES,
    )
    U0 = variable_composition_primitive_to_conservative(
        rho=np.linspace(0.55, 0.40, num_cells),
        u=np.linspace(900.0, 1250.0, num_cells),
        temperature_K=np.linspace(800.0, 1200.0, num_cells),
        field=closure.composition,
        species=SPECIES,
    )
    geometry = constant_area_profile(num_cells, area=0.02)
    numerical = NumericalConfig(cfl=0.25, tolerance=1.0e-6)
    dx = 0.02
    t_final = 0.05 * variable_composition_cfl_timestep(
        U0, dx, numerical, closure.composition, SPECIES
    )
    result = solve_prescribed_composition_quasi_1d(
        U0,
        closure.composition,
        geometry,
        dx,
        t_final,
        numerical,
        SPECIES,
        max_steps=5,
    )
    assert result.steps == 1
    assert np.all(np.isfinite(result.U))
