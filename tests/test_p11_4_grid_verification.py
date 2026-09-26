"""Tests for the evidence-gated P11.4 grid-verification helpers."""
from __future__ import annotations

import pytest

from cases.studies.p11_4_grid_convergence import (
    conservative_fine_grid_gci,
    observed_order_diagnostic,
    quantity_verification,
)


def test_observed_order_is_one_for_linear_grid_error() -> None:
    result = observed_order_diagnostic(1.20, 1.10, 1.05)
    assert result["behavior"] == "MONOTONIC"
    assert result["eligible_for_observed_order"] is True
    assert result["observed_order"] == pytest.approx(1.0)


def test_oscillatory_sequence_is_not_forced_into_observed_order() -> None:
    result = observed_order_diagnostic(1.20, 1.00, 1.10)
    assert result["behavior"] == "OSCILLATORY"
    assert result["eligible_for_observed_order"] is False
    assert result["observed_order"] is None


def test_conservative_gci_uses_nominal_first_order_and_fs_three() -> None:
    expected = 3.0 * (0.05 / 1.05)
    assert conservative_fine_grid_gci(1.10, 1.05) == pytest.approx(expected)


def test_quantity_verification_never_auto_claims_grid_independence() -> None:
    result = quantity_verification(1.20, 1.10, 1.05)
    assert result["formal_asymptotic_grid_independence_claim"] is False
    assert result["nominal_spatial_order"] == 1.0
    assert result["gci_safety_factor"] == 3.0
