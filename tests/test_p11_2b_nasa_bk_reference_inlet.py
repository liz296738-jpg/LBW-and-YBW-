"""Regression tests for the NASA-BK reduced-domain effective inlet."""

import math

import pytest

from cases.studies.p11_2b_nasa_bk_reference_inlet import (
    effective_inlet_for_gas,
    load_reference_inlet,
    reference_effective_inlet,
)
from scramjet1d.config import GasProperties


def test_reference_inlet_is_frozen_and_supersonic() -> None:
    record = load_reference_inlet()
    state = reference_effective_inlet()

    assert record["source_class"] == "NASA_REFERENCE_SOLUTION_DERIVED"
    assert record["status"] == "FROZEN_CONSERVATIVE_MOMENT_MATCHED_INLET"
    assert state.Mach > 1.0
    assert state.Mach == pytest.approx(2.422759005781948)
    assert state.mass_flow_kg_s == pytest.approx(1.9853071417940482)


def test_reference_inlet_matches_mass_momentum_and_h0_targets() -> None:
    record = load_reference_inlet()
    state = reference_effective_inlet()
    section = record["x0_reference_section"]
    gas = record["effective_gas_policy"]
    targets = record["matched_integral_targets"]
    area = float(section["source_backed_quasi_1d_area_m2"])

    mdot = state.rho_kg_per_m3 * state.u_m_per_s * area
    momentum = (state.rho_kg_per_m3 * state.u_m_per_s**2 + state.p_Pa) * area
    h0 = float(gas["cp_J_per_kg_K"]) * state.T_K + 0.5 * state.u_m_per_s**2

    assert mdot == pytest.approx(float(targets["mass_flow_kg_s"]), abs=1.0e-12)
    assert momentum == pytest.approx(float(targets["axial_momentum_flux_N"]), abs=1.0e-9)
    assert h0 == pytest.approx(float(targets["effective_specific_total_enthalpy_J_per_kg"]), abs=1.0e-7)
    assert state.p_Pa == pytest.approx(
        state.rho_kg_per_m3 * float(gas["R_J_per_kg_K"]) * state.T_K,
        abs=1.0e-8,
    )


def test_gamma_sensitivity_preserves_same_integral_targets() -> None:
    record = load_reference_inlet()
    targets = record["matched_integral_targets"]
    area = float(record["x0_reference_section"]["source_backed_quasi_1d_area_m2"])
    gas = GasProperties(gamma=1.246731797999899, R=329.4821420180208)
    state = effective_inlet_for_gas(gas)

    mdot = state.rho_kg_per_m3 * state.u_m_per_s * area
    momentum = (state.rho_kg_per_m3 * state.u_m_per_s**2 + state.p_Pa) * area
    h0 = gas.cp * state.T_K + 0.5 * state.u_m_per_s**2

    assert state.Mach > 1.0
    assert mdot == pytest.approx(float(targets["mass_flow_kg_s"]), abs=1.0e-12)
    assert momentum == pytest.approx(float(targets["axial_momentum_flux_N"]), abs=1.0e-9)
    assert h0 == pytest.approx(float(targets["effective_specific_total_enthalpy_J_per_kg"]), abs=1.0e-7)


def test_subsonic_alternate_root_is_explicitly_not_selected() -> None:
    record = load_reference_inlet()
    state = reference_effective_inlet()
    alternate = float(record["derivation"]["alternate_subsonic_root_u_m_per_s"])

    assert alternate > 0.0
    assert alternate < state.u_m_per_s
    assert math.isfinite(alternate)
