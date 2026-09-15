"""Regression tests for teacher Chapter 11 wall empirical closures."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from scramjet1d.config import GasProperties
from scramjet1d.source_terms import wall_friction_source
from scramjet1d.state import primitive_to_conservative
from scramjet1d.teacher_wall import (
    darcy_friction_factor_from_teacher_f,
    friction_coefficient_raw,
    wall_heat_coefficient_raw,
)


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "cases" / "studies" / "data" / "teacher_wall_closure.json"


def test_eq_11_25_friction_polynomial_reference_values() -> None:
    assert float(friction_coefficient_raw(0.0, 1.0)) == pytest.approx(0.0018)
    expected_at_one = 0.0018 + 0.001958 + 0.00927 - 0.0088525
    assert float(friction_coefficient_raw(1.0, 1.0)) == pytest.approx(expected_at_one)


def test_eq_11_26_wall_heat_polynomial_reference_values() -> None:
    assert float(wall_heat_coefficient_raw(0.0, 1.0)) == pytest.approx(0.0009)
    expected_at_one = 0.0009 + 0.001125 + 0.00594 - 0.00469
    assert float(wall_heat_coefficient_raw(1.0, 1.0)) == pytest.approx(expected_at_one)


def test_correlations_depend_only_on_product_phi_eta_and_vectorize() -> None:
    phi = np.array([0.2, 0.5, 1.0])
    eta = np.array([1.0, 0.8, 0.6])
    z = phi * eta
    np.testing.assert_allclose(
        friction_coefficient_raw(phi, eta),
        friction_coefficient_raw(z, np.ones_like(z)),
        rtol=0.0,
        atol=2.0e-18,
    )
    np.testing.assert_allclose(
        wall_heat_coefficient_raw(phi, eta),
        wall_heat_coefficient_raw(z, np.ones_like(z)),
        rtol=0.0,
        atol=2.0e-18,
    )


def test_raw_empirical_polynomial_is_not_silently_clipped() -> None:
    # The source polynomial becomes negative if pushed far beyond the practical
    # lean-ish range.  Preserve that diagnostic instead of hiding it.
    assert float(friction_coefficient_raw(2.0, 1.0)) < 0.0
    assert float(wall_heat_coefficient_raw(2.0, 1.0)) < 0.0


def test_darcy_mapping_is_exactly_four_times_teacher_f() -> None:
    teacher_f = np.array([0.0018, 0.003, 0.0042])
    np.testing.assert_allclose(
        darcy_friction_factor_from_teacher_f(teacher_f),
        4.0 * teacher_f,
        rtol=0.0,
        atol=0.0,
    )


def test_teacher_eq_11_38_matches_existing_darcy_wall_source_for_forward_flow() -> None:
    gas = GasProperties(gamma=1.4, R=287.0)
    rho = 0.42
    u = 1350.0
    p = 78000.0
    diameter = 0.035
    teacher_f = float(friction_coefficient_raw(0.75, 0.8))
    darcy_f = float(darcy_friction_factor_from_teacher_f(teacher_f))
    U = primitive_to_conservative(rho, u, p, gas)

    source = wall_friction_source(U, diameter, darcy_f, gas)
    expected_momentum = -0.5 * rho * u**2 * (4.0 * teacher_f / diameter)
    assert source[0] == pytest.approx(0.0, abs=0.0)
    assert source[1] == pytest.approx(expected_momentum, rel=2.0e-15)
    assert source[2] == pytest.approx(0.0, abs=0.0)


def test_negative_teacher_f_is_rejected_before_darcy_mapping() -> None:
    with pytest.raises(ValueError, match="nonnegative"):
        darcy_friction_factor_from_teacher_f(-1.0e-4)


def test_invalid_phi_eta_inputs_are_rejected() -> None:
    with pytest.raises(ValueError, match="phi"):
        friction_coefficient_raw(-0.1, 0.8)
    with pytest.raises(ValueError, match="eta"):
        wall_heat_coefficient_raw(0.8, 1.1)
    with pytest.raises(ValueError, match="broadcast-compatible"):
        friction_coefficient_raw(np.ones(2), np.ones(3))


def test_teacher_wall_ledger_keeps_heat_adapter_gated() -> None:
    with LEDGER.open("r", encoding="utf-8") as stream:
        record = json.load(stream)
    assert record["schema_version"] == 1
    assert record["stage"] == "P11.3D"
    assert record["equations"]["11.38_friction_term"]["forward_flow_mapping"] == (
        "f_D = 4*f when D_h = D_e and u >= 0"
    )
    assert record["readiness"]["teacher_to_repo_friction_convention_mapping_ready"] is True
    assert record["readiness"]["wall_heat_dimensional_adapter_ready"] is False
    assert record["scientific_boundaries"]["heat_coefficient_is_not_assumed_to_be_wall_heat_flux_W_per_m2"] is True
