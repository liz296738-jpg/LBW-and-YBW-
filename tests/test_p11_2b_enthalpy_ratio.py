"""Tests for dimensionless total-enthalpy validation constraints in P11.2B."""

import importlib.util
from pathlib import Path

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "cases" / "studies" / "p11_2b_heat_release_closure.py"
SPEC = importlib.util.spec_from_file_location("p11_2b_heat_release_closure_ratio", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_enthalpy_ratio_and_total_power_are_inverse_diagnostics() -> None:
    mass_flow = 0.2
    inlet_enthalpy = 2.5e6
    measured_ratio = 1.16

    power = MODULE.total_power_from_enthalpy_ratio(
        mass_flow, inlet_enthalpy, measured_ratio
    )
    assert power == pytest.approx(80_000.0)

    line_heat = np.array([1.0, 3.0, 4.0])
    dx = 0.02
    scaled = MODULE.scale_shape_to_total_power(line_heat, dx, power)
    recovered = MODULE.total_enthalpy_ratio_from_line_heat(
        scaled, dx, mass_flow, inlet_enthalpy
    )
    assert recovered == pytest.approx(measured_ratio, rel=2.0e-15)


def test_ratio_one_maps_to_zero_heat_addition() -> None:
    assert MODULE.total_power_from_enthalpy_ratio(0.5, 2.0e6, 1.0) == 0.0
    assert MODULE.total_enthalpy_ratio_from_line_heat(
        np.zeros(4), 0.01, 0.5, 2.0e6
    ) == 1.0


@pytest.mark.parametrize(
    ("mass_flow", "inlet_enthalpy", "ratio"),
    [
        (0.0, 2.0e6, 1.16),
        (-1.0, 2.0e6, 1.16),
        (0.5, 0.0, 1.16),
        (0.5, -1.0, 1.16),
        (0.5, 2.0e6, 0.99),
        (np.nan, 2.0e6, 1.16),
    ],
)
def test_total_power_from_enthalpy_ratio_rejects_unusable_scale(
    mass_flow, inlet_enthalpy, ratio
) -> None:
    with pytest.raises(ValueError):
        MODULE.total_power_from_enthalpy_ratio(mass_flow, inlet_enthalpy, ratio)


def test_liu_ratio_is_not_an_absolute_power_without_two_independent_scales() -> None:
    # The source-backed Liu model-B value Ht4/Ht3=1.16 is dimensionless.
    # This test deliberately documents that changing either independent scale
    # changes total power while the measured ratio remains unchanged.
    ratio = 1.16
    power_a = MODULE.total_power_from_enthalpy_ratio(0.2, 2.5e6, ratio)
    power_b = MODULE.total_power_from_enthalpy_ratio(0.4, 2.5e6, ratio)
    power_c = MODULE.total_power_from_enthalpy_ratio(0.2, 3.0e6, ratio)

    assert power_b == pytest.approx(2.0 * power_a)
    assert power_c == pytest.approx(1.2 * power_a)
