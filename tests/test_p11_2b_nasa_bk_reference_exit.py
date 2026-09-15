"""Regression tests for the NASA-BK conservative exit moment target."""

import pytest

from cases.studies.p11_2b_nasa_bk_reference_exit import (
    effective_exit_for_gas,
    load_reference_exit,
)
from cases.studies.p11_2b_nasa_bk_thermo import reference_effective_gas
from scramjet1d.config import GasProperties


def test_reference_exit_is_frozen_and_supersonic() -> None:
    record = load_reference_exit()
    thermo = reference_effective_gas()
    gas = GasProperties(gamma=thermo.gamma, R=thermo.R_J_per_kg_K)
    state = effective_exit_for_gas(gas)

    assert record["source_class"] == "NASA_REFERENCE_SOLUTION_DERIVED"
    assert record["status"] == "FROZEN_CONSERVATIVE_MOMENT_MATCHED_EXIT_TARGET"
    assert state.Mach > 1.0
    assert state.Mach == pytest.approx(2.4310586214846666)
    assert state.p_Pa == pytest.approx(87197.52084149444)
    assert state.T_K == pytest.approx(1263.229829138864)


def test_reference_exit_exactly_matches_frozen_integral_targets() -> None:
    record = load_reference_exit()
    thermo = reference_effective_gas()
    gas = GasProperties(gamma=thermo.gamma, R=thermo.R_J_per_kg_K)
    state = effective_exit_for_gas(gas)
    targets = record["source_integral_targets"]
    area = float(targets["area_exit_m2"])

    mdot = state.rho_kg_per_m3 * state.u_m_per_s * area
    momentum = (state.rho_kg_per_m3 * state.u_m_per_s**2 + state.p_Pa) * area
    h0 = gas.cp * state.T_K + 0.5 * state.u_m_per_s**2

    assert mdot == pytest.approx(float(targets["mass_flow_kg_s"]), abs=1.0e-12)
    assert momentum == pytest.approx(float(targets["axial_momentum_flux_N"]), abs=1.0e-9)
    assert h0 == pytest.approx(float(targets["specific_total_enthalpy_J_per_kg"]), abs=1.0e-7)


def test_lower_gamma_uses_same_conservative_exit_targets() -> None:
    record = load_reference_exit()
    thermo = reference_effective_gas()
    gas = GasProperties(gamma=1.246731797999899, R=thermo.R_J_per_kg_K)
    state = effective_exit_for_gas(gas)
    targets = record["source_integral_targets"]
    area = float(targets["area_exit_m2"])

    assert state.Mach > 1.0
    assert state.rho_kg_per_m3 * state.u_m_per_s * area == pytest.approx(
        float(targets["mass_flow_kg_s"]), abs=1.0e-12
    )
    assert (state.rho_kg_per_m3 * state.u_m_per_s**2 + state.p_Pa) * area == pytest.approx(
        float(targets["axial_momentum_flux_N"]), abs=1.0e-9
    )
