"""Tests for the source-backed Jin/Shapiro-to-Darcy friction convention."""

import importlib.util
from pathlib import Path

import numpy as np
import pytest
from numpy.testing import assert_allclose

from scramjet1d.config import GasProperties
from scramjet1d.source_terms import wall_friction_source
from scramjet1d.state import primitive_to_conservative


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "cases" / "studies" / "p11_2b_friction_convention.py"
SPEC = importlib.util.spec_from_file_location("p11_2b_friction_convention", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

GAS = GasProperties()


def test_source_record_preserves_shapiro_definition_and_mapping() -> None:
    record = MODULE.load_friction_convention_source()
    assert record["source_convention"]["jin_equation_term"] == "4 Cf dx / D"
    assert record["source_convention"]["shapiro_definition"] == "Cf = tau_w / (0.5 rho u^2)"
    assert record["derived_mapping"]["result"] == "f_D = 4 Cf"
    assert record["derived_mapping"]["classification"] == "DERIVED_CONVENTION_MAPPING"
    assert record["formal_case_effect"]["fig14_numeric_cf"] == "STILL_NOT_FROZEN"


def test_jin_cf_to_repository_darcy_is_exact_factor_four() -> None:
    cf = np.array([0.0, 0.001, 0.0025, 0.005])
    darcy = MODULE.jin_cf_to_repository_darcy(cf)
    assert_allclose(darcy, [0.0, 0.004, 0.01, 0.02], rtol=0.0, atol=0.0)
    assert_allclose(MODULE.repository_darcy_to_jin_cf(darcy), cf, rtol=0.0, atol=0.0)


def test_converted_darcy_source_equals_wall_shear_force_identity() -> None:
    rho = 1.2
    velocity = 300.0
    diameter = 0.1
    cf = 0.0025
    pressure = 100_000.0

    state = primitive_to_conservative(rho, velocity, pressure, GAS)
    darcy = float(MODULE.jin_cf_to_repository_darcy(cf))
    source = wall_friction_source(state, diameter, darcy, GAS)

    tau_w = cf * 0.5 * rho * velocity**2
    expected_momentum_source = -4.0 * tau_w / diameter

    assert source[0] == 0.0
    assert source[2] == 0.0
    assert source[1] == pytest.approx(expected_momentum_source, rel=1e-14, abs=0.0)


def test_conversion_preserves_reverse_flow_drag_direction() -> None:
    rho = 1.2
    velocity = -300.0
    diameter = 0.1
    cf = 0.0025
    state = primitive_to_conservative(rho, velocity, 100_000.0, GAS)
    darcy = float(MODULE.jin_cf_to_repository_darcy(cf))
    source = wall_friction_source(state, diameter, darcy, GAS)

    assert source[1] > 0.0
    assert source[1] * velocity < 0.0


@pytest.mark.parametrize("value", [-1e-3, np.nan, np.inf])
def test_conversion_rejects_invalid_jin_cf(value: float) -> None:
    with pytest.raises(ValueError):
        MODULE.jin_cf_to_repository_darcy(value)


@pytest.mark.parametrize("value", [-1e-3, np.nan, np.inf])
def test_inverse_conversion_rejects_invalid_darcy(value: float) -> None:
    with pytest.raises(ValueError):
        MODULE.repository_darcy_to_jin_cf(value)
