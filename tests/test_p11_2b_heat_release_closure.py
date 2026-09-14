"""Tests for source-backed P11.2B prescribed heat-release utilities."""

import importlib.util
from pathlib import Path

import numpy as np
import pytest
from numpy.testing import assert_allclose, assert_array_equal


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "cases" / "studies" / "p11_2b_heat_release_closure.py"
SPEC = importlib.util.spec_from_file_location("p11_2b_heat_release_closure", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_source_ledger_loads_and_remains_parameter_gated() -> None:
    data = MODULE.load_heat_release_source_ledger()

    assert data["schema_version"] == 1
    assert {source["source_id"] for source in data["sources"]} == {"SRC07", "SRC08"}
    assert (
        data["project_decision"]["formal_case_status"]
        == "BLOCKED_PENDING_SOURCE_BACKED_ABSOLUTE_POWER_AND_SHAPE_PARAMETERS"
    )
    assert data["project_decision"]["mass_added"] is False
    assert data["project_decision"]["momentum_added"] is False


def test_eq7_quasi_gaussian_matches_published_functional_form() -> None:
    x = np.array([0.0, 1.0, 2.0, 3.0])
    actual = MODULE.quasi_gaussian_eq7_normalized(
        x, q_peak=0.8, x_peak=1.0, x_core_end=3.0
    )
    expected = 0.8 * np.exp(-((x - 1.0) ** 2) / ((3.0 - 1.0) ** 2))

    assert_allclose(actual, expected, rtol=0.0, atol=1.0e-15)
    assert actual[1] == pytest.approx(0.8)
    assert actual.flags.writeable is False


def test_eq7_is_unit_invariant_when_all_positions_are_scaled_together() -> None:
    x_m = np.linspace(0.0, 0.2, 11)
    x_mm = x_m * 1000.0

    metres = MODULE.quasi_gaussian_eq7_normalized(
        x_m, q_peak=1.0, x_peak=0.05, x_core_end=0.15
    )
    millimetres = MODULE.quasi_gaussian_eq7_normalized(
        x_mm, q_peak=1.0, x_peak=50.0, x_core_end=150.0
    )

    assert_allclose(metres, millimetres, rtol=0.0, atol=2.0e-15)


@pytest.mark.parametrize(
    ("x", "q_peak", "x_peak", "x_core_end"),
    [
        ([], 1.0, 0.0, 1.0),
        ([0.0, np.nan], 1.0, 0.0, 1.0),
        ([0.0, 1.0], -1.0, 0.0, 1.0),
        ([0.0, 1.0], 1.0, 0.0, 0.0),
        ([0.0, 1.0], np.inf, 0.0, 1.0),
    ],
)
def test_eq7_rejects_invalid_inputs(x, q_peak, x_peak, x_core_end) -> None:
    with pytest.raises(ValueError):
        MODULE.quasi_gaussian_eq7_normalized(x, q_peak, x_peak, x_core_end)


def test_shape_scaling_preserves_requested_total_power_exactly() -> None:
    shape = np.array([0.1, 0.3, 1.0, 0.5, 0.2])
    dx = 0.02
    power = 250_000.0

    line_heat = MODULE.scale_shape_to_total_power(shape, dx, power)

    assert np.sum(line_heat) * dx == pytest.approx(power, rel=2.0e-15)
    assert line_heat.flags.writeable is False


def test_zero_power_returns_zero_without_inventing_heat_release() -> None:
    actual = MODULE.scale_shape_to_total_power(np.zeros(4), 0.01, 0.0)
    assert_array_equal(actual, np.zeros(4))


def test_positive_power_requires_positive_shape_integral() -> None:
    with pytest.raises(ValueError):
        MODULE.scale_shape_to_total_power(np.zeros(4), 0.01, 1.0)


def test_eq11_discrete_energy_relation_matches_total_power_temperature_rise() -> None:
    dx = 0.01
    mass_flow = 0.6
    cp = 1004.5
    inlet_T0 = 1650.0
    line_heat = np.array([10_000.0, 20_000.0, 30_000.0, 40_000.0])

    total_temperature = MODULE.cumulative_total_temperature_from_line_heat(
        line_heat, dx, mass_flow, cp, inlet_T0
    )
    expected_final = inlet_T0 + np.sum(line_heat) * dx / (mass_flow * cp)

    assert total_temperature[-1] == pytest.approx(expected_final, rel=2.0e-15)
    assert np.all(np.diff(total_temperature) >= 0.0)
    assert total_temperature.flags.writeable is False


@pytest.mark.parametrize(
    ("dx", "mass_flow", "cp", "temperature"),
    [
        (0.0, 0.6, 1004.5, 1650.0),
        (-0.1, 0.6, 1004.5, 1650.0),
        (0.01, 0.0, 1004.5, 1650.0),
        (0.01, 0.6, 0.0, 1650.0),
        (0.01, 0.6, 1004.5, 0.0),
    ],
)
def test_eq11_rejects_nonphysical_scalar_inputs(dx, mass_flow, cp, temperature) -> None:
    with pytest.raises(ValueError):
        MODULE.cumulative_total_temperature_from_line_heat(
            np.ones(4), dx, mass_flow, cp, temperature
        )
