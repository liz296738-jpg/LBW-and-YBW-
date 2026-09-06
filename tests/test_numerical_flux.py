"""Tests for Rusanov numerical interface fluxes."""

import numpy as np
import pytest

from scramjet1d.config import GasProperties
from scramjet1d.flux import euler_flux
import scramjet1d.flux as flux_module
from scramjet1d.state import primitive_to_conservative


GAS = GasProperties()


def _expected_rusanov(U_left: np.ndarray, U_right: np.ndarray) -> np.ndarray:
    """Evaluate the Rusanov definition independently of production flux code."""
    rho_left, momentum_left, rho_E_left = np.moveaxis(U_left, -1, 0)
    rho_right, momentum_right, rho_E_right = np.moveaxis(U_right, -1, 0)
    u_left = momentum_left / rho_left
    u_right = momentum_right / rho_right
    p_left = (GAS.gamma - 1.0) * (rho_E_left - momentum_left**2 / (2.0 * rho_left))
    p_right = (GAS.gamma - 1.0) * (rho_E_right - momentum_right**2 / (2.0 * rho_right))
    a_left = np.sqrt(GAS.gamma * p_left / rho_left)
    a_right = np.sqrt(GAS.gamma * p_right / rho_right)
    alpha = np.maximum(np.abs(u_left) + a_left, np.abs(u_right) + a_right)
    F_left = np.stack(
        (momentum_left, momentum_left * u_left + p_left, u_left * (rho_E_left + p_left)),
        axis=-1,
    )
    F_right = np.stack(
        (momentum_right, momentum_right * u_right + p_right, u_right * (rho_E_right + p_right)),
        axis=-1,
    )
    return 0.5 * (F_left + F_right) - 0.5 * alpha[..., np.newaxis] * (U_right - U_left)


def test_identical_states_reduce_to_physical_flux() -> None:
    """A consistent numerical flux equals F(U) for equal left and right states."""
    U = primitive_to_conservative(1.2, 500.0, 120_000.0, GAS)

    np.testing.assert_allclose(flux_module.rusanov_flux(U, U, GAS), euler_flux(U, GAS), rtol=1e-12)


def test_static_identical_state_returns_pressure_momentum_flux() -> None:
    """A stationary equal interface keeps only the pressure momentum flux."""
    U = primitive_to_conservative(1.0, 0.0, 100_000.0, GAS)

    np.testing.assert_allclose(flux_module.rusanov_flux(U, U, GAS), [0.0, 100_000.0, 0.0], rtol=1e-12)


def test_static_pressure_jump_matches_rusanov_definition() -> None:
    """A pressure discontinuity includes the independently computed dissipative term."""
    U_left = primitive_to_conservative(1.0, 0.0, 120_000.0, GAS)
    U_right = primitive_to_conservative(1.0, 0.0, 100_000.0, GAS)

    expected = _expected_rusanov(U_left, U_right)
    np.testing.assert_allclose(flux_module.rusanov_flux(U_left, U_right, GAS), expected, rtol=1e-12)


def test_different_forward_states_match_rusanov_definition() -> None:
    """A forward-flow interface follows the full Rusanov formula."""
    U_left = primitive_to_conservative(1.2, 600.0, 120_000.0, GAS)
    U_right = primitive_to_conservative(0.9, 400.0, 90_000.0, GAS)

    np.testing.assert_allclose(
        flux_module.rusanov_flux(U_left, U_right, GAS),
        _expected_rusanov(U_left, U_right),
        rtol=1e-12,
    )


def test_reverse_flow_uses_absolute_velocity_in_wave_speed() -> None:
    """Reverse-flow interfaces retain the absolute velocity in alpha."""
    U_left = primitive_to_conservative(1.0, -300.0, 100_000.0, GAS)
    U_right = primitive_to_conservative(0.8, -200.0, 80_000.0, GAS)

    np.testing.assert_allclose(
        flux_module.rusanov_flux(U_left, U_right, GAS),
        _expected_rusanov(U_left, U_right),
        rtol=1e-12,
    )


def test_vectorized_interfaces_match_rusanov_definition() -> None:
    """Multiple interfaces are evaluated independently along the final state axis."""
    U_left = primitive_to_conservative(
        np.array([1.0, 0.8, 0.6]),
        np.array([300.0, 500.0, 800.0]),
        np.array([100_000.0, 90_000.0, 80_000.0]),
        GAS,
    )
    U_right = primitive_to_conservative(
        np.array([0.9, 0.7, 0.5]),
        np.array([250.0, 450.0, 700.0]),
        np.array([95_000.0, 85_000.0, 70_000.0]),
        GAS,
    )

    flux = flux_module.rusanov_flux(U_left, U_right, GAS)

    assert flux.shape == (3, 3)
    np.testing.assert_allclose(flux, _expected_rusanov(U_left, U_right), rtol=1e-12)


def test_scalar_left_state_broadcasts_over_right_interfaces() -> None:
    """A scalar left state broadcasts over a vector of right interface states."""
    U_left = primitive_to_conservative(1.0, 300.0, 100_000.0, GAS)
    U_right = primitive_to_conservative(
        np.array([0.9, 0.8, 0.7]),
        np.array([250.0, 200.0, 150.0]),
        np.array([90_000.0, 80_000.0, 70_000.0]),
        GAS,
    )
    U_left_broadcast = np.broadcast_to(U_left, U_right.shape)

    flux = flux_module.rusanov_flux(U_left, U_right, GAS)

    assert flux.shape == (3, 3)
    np.testing.assert_allclose(flux, _expected_rusanov(U_left_broadcast, U_right), rtol=1e-12)


def test_swapped_states_stay_finite_with_correct_shape() -> None:
    """Swapping valid states yields another valid numerical interface flux."""
    U_left = primitive_to_conservative(1.2, 600.0, 120_000.0, GAS)
    U_right = primitive_to_conservative(0.9, 400.0, 90_000.0, GAS)

    swapped = flux_module.rusanov_flux(U_right, U_left, GAS)

    assert swapped.shape == (3,)
    assert np.isfinite(swapped).all()


def test_rusanov_flux_rejects_invalid_left_density() -> None:
    """The left conservative state must have positive density."""
    with pytest.raises(ValueError, match="rho"):
        flux_module.rusanov_flux(np.array([0.0, 0.0, 1.0]), np.array([1.0, 0.0, 1.0]), GAS)


def test_rusanov_flux_rejects_invalid_right_pressure() -> None:
    """The right conservative state must recover positive pressure."""
    U_left = primitive_to_conservative(1.0, 0.0, 100_000.0, GAS)

    with pytest.raises(ValueError, match="p"):
        flux_module.rusanov_flux(U_left, np.array([1.0, 10.0, 49.0]), GAS)


@pytest.mark.parametrize(
    "U_left, U_right",
    [
        (np.array([np.nan, 0.0, 1.0]), np.array([1.0, 0.0, 1.0])),
        (np.array([1.0, 0.0, 1.0]), np.array([1.0, np.inf, 1.0])),
    ],
)
def test_rusanov_flux_rejects_nonfinite_states(U_left: np.ndarray, U_right: np.ndarray) -> None:
    """NaN or infinity on either side of an interface is rejected."""
    with pytest.raises(ValueError):
        flux_module.rusanov_flux(U_left, U_right, GAS)


@pytest.mark.parametrize("U_left, U_right", [(np.zeros(4), np.zeros(3)), (np.zeros(3), np.zeros((2, 4)))])
def test_rusanov_flux_rejects_invalid_final_dimension(U_left: np.ndarray, U_right: np.ndarray) -> None:
    """Both states must have exactly three conservative components on the final axis."""
    with pytest.raises(ValueError, match="last dimension"):
        flux_module.rusanov_flux(U_left, U_right, GAS)
