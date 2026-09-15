"""Regression tests for the explicit teacher combustion-efficiency policy."""

from __future__ import annotations

import numpy as np
import pytest

from scramjet1d.teacher_combustion import mixing_efficiency_raw
from scramjet1d.teacher_efficiency import (
    combustion_efficiency_from_fuel_mass_rates,
    combustion_efficiency_from_raw_mixing,
)


def test_eq_11_18_fractional_efficiency_limits_and_partial_burn() -> None:
    injected = np.array([2.0, 2.0, 2.0])
    residual = np.array([2.0, 0.7, 0.0])
    expected = np.array([0.0, 0.65, 1.0])
    np.testing.assert_allclose(
        combustion_efficiency_from_fuel_mass_rates(injected, residual),
        expected,
        rtol=0.0,
        atol=1.0e-15,
    )


def test_eq_11_18_broadcasts_and_rejects_unphysical_mass_rates() -> None:
    result = combustion_efficiency_from_fuel_mass_rates(4.0, np.array([4.0, 2.0, 0.0]))
    np.testing.assert_allclose(result, [0.0, 0.5, 1.0], rtol=0.0, atol=0.0)

    with pytest.raises(ValueError, match="strictly positive"):
        combustion_efficiency_from_fuel_mass_rates(0.0, 0.0)
    with pytest.raises(ValueError, match="nonnegative"):
        combustion_efficiency_from_fuel_mass_rates(1.0, -0.1)
    with pytest.raises(ValueError, match="must not exceed"):
        combustion_efficiency_from_fuel_mass_rates(1.0, 1.1)


def test_raw_mixing_adapter_is_identity_inside_physical_interval() -> None:
    raw = np.array([0.0, 0.2, 0.75, 1.0])
    np.testing.assert_allclose(
        combustion_efficiency_from_raw_mixing(raw),
        raw,
        rtol=0.0,
        atol=0.0,
    )


def test_raw_mixing_adapter_saturates_above_one_explicitly() -> None:
    raw = np.array([1.0001, 1.2, 3.0])
    np.testing.assert_allclose(
        combustion_efficiency_from_raw_mixing(raw),
        np.ones_like(raw),
        rtol=0.0,
        atol=0.0,
    )


def test_normal_injection_raw_value_remains_unmodified_but_policy_eta_is_bounded() -> None:
    raw = float(mixing_efficiency_raw(1.0, 1.0, "normal", alpha=0.20))
    assert raw > 1.0
    eta = float(combustion_efficiency_from_raw_mixing(raw))
    assert eta == pytest.approx(1.0, abs=0.0)
    # Calling the raw closure again still returns the source correlation > 1.
    assert float(mixing_efficiency_raw(1.0, 1.0, "normal", alpha=0.20)) == pytest.approx(raw)


def test_raw_mixing_adapter_rejects_negative_or_nonfinite_values() -> None:
    with pytest.raises(ValueError, match="nonnegative"):
        combustion_efficiency_from_raw_mixing(-1.0e-6)
    with pytest.raises(ValueError, match="finite"):
        combustion_efficiency_from_raw_mixing(np.nan)
