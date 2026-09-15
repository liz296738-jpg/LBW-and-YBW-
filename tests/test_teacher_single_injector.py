"""Verification for the source-consistent teacher single-injector mapping."""

from __future__ import annotations

import numpy as np
import pytest

from cases.studies.teacher_thermochemistry_database import build_species_database
from scramjet1d.geometry import constant_area_profile
from scramjet1d.teacher_combustion import equivalence_ratio
from scramjet1d.teacher_single_injector import build_teacher_single_injector_mapping
from scramjet1d.teacher_sources import teacher_eq_11_38_non_geometric_source
from scramjet1d.variable_composition import variable_composition_primitive_to_conservative


SPECIES = build_species_database()


def _mapping(*, fuel: str = "H2", mode: str = "parallel"):
    x = np.arange(8, dtype=float) * 0.02
    kwargs = {}
    if mode == "normal":
        kwargs["alpha"] = 0.2
    elif mode == "strut":
        kwargs["A"] = 2.2
    return build_teacher_single_injector_mapping(
        fuel=fuel,
        injected_fuel_mass_flow_rate_kg_per_s=0.012,
        incoming_air_mass_flow_rate_kg_per_s=1.0,
        x_cell_m=x,
        dx_m=0.02,
        injector_cell=2,
        combustor_height_m=np.linspace(0.03, 0.04, x.size),
        C_m=35.0,
        injection_mode=mode,
        injected_fuel_temperature_K=450.0,
        injected_fuel_axial_velocity_m_per_s=180.0,
        species=SPECIES,
        **kwargs,
    )


def test_upstream_cells_are_exact_air_only_and_inlet_contains_no_fuel_or_products() -> None:
    mapping = _mapping(fuel="H2")
    assert mapping.injector_cell == 2
    assert np.all(mapping.equivalence_ratio[:2] == 0.0)
    assert np.all(mapping.combustion_efficiency[:2] == 0.0)

    for index in range(mapping.injector_cell):
        composition = mapping.composition.composition_at(index)
        assert composition["H2"] == 0.0
        assert composition["H2O"] == 0.0
        assert composition["CO2"] == 0.0
        assert composition["O2"] > 0.0
        assert composition["N2"] > 0.0
        assert composition["AR"] > 0.0
        assert sum(composition.values()) == pytest.approx(1.0, abs=2.0e-15)


def test_downstream_phi_and_composition_are_exactly_the_verified_spatial_closure() -> None:
    mapping = _mapping(fuel="C2H4", mode="strut")
    target_phi = equivalence_ratio(0.012, 1.0, "C2H4")
    np.testing.assert_allclose(mapping.equivalence_ratio[:2], 0.0, atol=0.0)
    np.testing.assert_allclose(mapping.equivalence_ratio[2:], target_phi, rtol=0.0, atol=0.0)
    np.testing.assert_allclose(
        mapping.composition.mass_fractions[2:],
        mapping.downstream_closure.composition.mass_fractions,
        rtol=0.0,
        atol=0.0,
    )
    np.testing.assert_allclose(
        mapping.combustion_efficiency[2:],
        mapping.downstream_closure.combustion_efficiency,
        rtol=0.0,
        atol=0.0,
    )


def test_localized_source_is_applied_once_and_integrates_to_prescribed_fuel_flow() -> None:
    mapping = _mapping()
    gradient = mapping.fuel_mass_flow_gradient_kg_per_s_per_m
    assert np.count_nonzero(gradient) == 1
    assert np.flatnonzero(gradient).tolist() == [mapping.injector_cell]
    assert np.sum(gradient) * 0.02 == pytest.approx(0.012, rel=2.0e-16)

    assert np.count_nonzero(mapping.fuel_axial_velocity_m_per_s) == 1
    assert np.count_nonzero(mapping.fuel_specific_total_enthalpy_J_per_kg) == 1
    assert mapping.fuel_axial_velocity_m_per_s[mapping.injector_cell] == 180.0


def test_mapping_and_eq_11_38_source_do_not_duplicate_mass_or_injected_enthalpy() -> None:
    mapping = _mapping()
    n = mapping.composition.num_cells
    area = 0.02
    dx = 0.02
    geometry = constant_area_profile(n, area=area)
    # Zero bulk velocity removes friction work/momentum from this integral identity.
    U = variable_composition_primitive_to_conservative(
        rho=0.5,
        u=0.0,
        temperature_K=900.0,
        field=mapping.composition,
        species=SPECIES,
    )
    source = teacher_eq_11_38_non_geometric_source(
        U,
        mapping.composition,
        geometry,
        SPECIES,
        phi=mapping.equivalence_ratio,
        eta=mapping.combustion_efficiency,
        hydraulic_diameter_m=0.04,
        fuel_mass_flow_gradient_kg_per_s_per_m=mapping.fuel_mass_flow_gradient_kg_per_s_per_m,
        fuel_axial_velocity_m_per_s=mapping.fuel_axial_velocity_m_per_s,
        fuel_specific_total_enthalpy_J_per_kg=mapping.fuel_specific_total_enthalpy_J_per_kg,
        wall_specific_heat_gain_gradient_J_per_kg_per_m=0.0,
    )
    integrated = np.sum(source * geometry.cell_area[:, None], axis=0) * dx
    injector = mapping.injector_cell
    mdot = 0.012
    expected_momentum = mapping.fuel_axial_velocity_m_per_s[injector] * mdot
    expected_energy = mapping.fuel_specific_total_enthalpy_J_per_kg[injector] * mdot
    np.testing.assert_allclose(
        integrated,
        np.array([mdot, expected_momentum, expected_energy]),
        rtol=3.0e-14,
        atol=1.0e-9,
    )


def test_raw_mixing_remains_diagnostic_while_physical_eta_is_saturated() -> None:
    # Use a long domain so the normal-injection raw correlation crosses unity.
    x = np.arange(30, dtype=float) * 0.05
    mapping = build_teacher_single_injector_mapping(
        fuel="H2",
        injected_fuel_mass_flow_rate_kg_per_s=0.01,
        incoming_air_mass_flow_rate_kg_per_s=1.0,
        x_cell_m=x,
        dx_m=0.05,
        injector_cell=1,
        combustor_height_m=0.02,
        C_m=25.0,
        injection_mode="normal",
        alpha=0.2,
        injected_fuel_temperature_K=400.0,
        injected_fuel_axial_velocity_m_per_s=100.0,
        species=SPECIES,
    )
    assert np.max(mapping.raw_mixing_efficiency) > 1.0
    assert np.max(mapping.combustion_efficiency) == pytest.approx(1.0, abs=0.0)
    assert np.all(mapping.combustion_efficiency <= 1.0)


def test_mapping_profiles_are_immutable() -> None:
    mapping = _mapping()
    for profile in (
        mapping.x_cell_m,
        mapping.equivalence_ratio,
        mapping.raw_mixing_efficiency,
        mapping.combustion_efficiency,
        mapping.fuel_mass_flow_gradient_kg_per_s_per_m,
        mapping.fuel_axial_velocity_m_per_s,
        mapping.fuel_specific_total_enthalpy_J_per_kg,
    ):
        assert profile.flags.writeable is False
    with pytest.raises(ValueError):
        mapping.equivalence_ratio[0] = 1.0


def test_mapping_rejects_injector_at_inlet_nonuniform_grid_rich_case_and_c10h22() -> None:
    x = np.arange(5, dtype=float) * 0.02
    common = dict(
        fuel="H2",
        injected_fuel_mass_flow_rate_kg_per_s=0.01,
        incoming_air_mass_flow_rate_kg_per_s=1.0,
        x_cell_m=x,
        dx_m=0.02,
        combustor_height_m=0.03,
        C_m=35.0,
        injection_mode="parallel",
        injected_fuel_temperature_K=450.0,
        injected_fuel_axial_velocity_m_per_s=100.0,
        species=SPECIES,
    )
    with pytest.raises(IndexError, match="air-only upstream"):
        build_teacher_single_injector_mapping(injector_cell=0, **common)

    nonuniform = dict(common)
    nonuniform["x_cell_m"] = np.array([0.0, 0.02, 0.041, 0.06, 0.08])
    with pytest.raises(ValueError, match="spacing"):
        build_teacher_single_injector_mapping(injector_cell=1, **nonuniform)

    rich = dict(common)
    rich["injected_fuel_mass_flow_rate_kg_per_s"] = 0.1
    rich["incoming_air_mass_flow_rate_kg_per_s"] = 0.1
    with pytest.raises(ValueError, match="lean-only"):
        build_teacher_single_injector_mapping(injector_cell=1, **rich)

    kerosene = dict(common)
    kerosene["fuel"] = "C10H22"
    with pytest.raises(ValueError, match="C10H22 thermochemistry"):
        build_teacher_single_injector_mapping(injector_cell=1, **kerosene)
