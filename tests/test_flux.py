"""Tests for the one-dimensional Euler physical flux."""

import numpy as np
import pytest

from scramjet1d.config import GasProperties
import scramjet1d.flux as flux_module
from scramjet1d.state import primitive_to_conservative


GAS = GasProperties()


def test_static_gas_has_pressure_only_momentum_flux() -> None:
    """A stationary state has zero mass/energy flux but retains pressure flux."""
    flux = flux_module.euler_flux(primitive_to_conservative(1.0, 0.0, 100_000.0, GAS), GAS)

    np.testing.assert_allclose(flux, [0.0, 100_000.0, 0.0], rtol=1e-12, atol=1e-12)


def test_positive_flow_matches_euler_flux_definition() -> None:
    """A forward-flow flux agrees with the independently evaluated Euler formula."""
    rho, u, p = 1.2, 500.0, 120_000.0
    U = primitive_to_conservative(rho, u, p, GAS)
    expected = np.array([rho * u, rho * u**2 + p, u * (U[2] + p)])

    np.testing.assert_allclose(flux_module.euler_flux(U, GAS), expected, rtol=1e-12)


def test_negative_velocity_retains_signed_mass_and_energy_flux() -> None:
    """Reverse flow keeps signed transport terms while momentum flux remains positive."""
    rho, u, p = 1.0, -300.0, 100_000.0
    U = primitive_to_conservative(rho, u, p, GAS)
    flux = flux_module.euler_flux(U, GAS)
    expected = np.array([rho * u, rho * u**2 + p, u * (U[2] + p)])

    np.testing.assert_allclose(flux, expected, rtol=1e-12)
    assert flux[0] < 0.0
    assert flux[1] > 0.0
    assert flux[2] < 0.0


def test_vectorized_flux_matches_euler_flux_definition() -> None:
    """Flux evaluation preserves vector-state shape and values."""
    rho = np.array([0.5, 1.0, 2.0])
    u = np.array([300.0, 800.0, 1500.0])
    p = np.array([50_000.0, 100_000.0, 300_000.0])
    U = primitive_to_conservative(rho, u, p, GAS)

    flux = flux_module.euler_flux(U, GAS)

    assert flux.shape == (3, 3)
    np.testing.assert_allclose(flux[:, 0], rho * u, rtol=1e-12)
    np.testing.assert_allclose(flux[:, 1], rho * u**2 + p, rtol=1e-12)
    np.testing.assert_allclose(flux[:, 2], u * (U[:, 2] + p), rtol=1e-12)


def test_broadcast_derived_states_produce_correct_flux() -> None:
    """Flux supports states built from scalar/vector primitive broadcasting."""
    u = np.array([100.0, 200.0, 300.0])
    U = primitive_to_conservative(1.0, u, 100_000.0, GAS)
    flux = flux_module.euler_flux(U, GAS)

    assert flux.shape == (3, 3)
    np.testing.assert_allclose(flux[:, 0], u, rtol=1e-12)
    np.testing.assert_allclose(flux[:, 1], u**2 + 100_000.0, rtol=1e-12)
    np.testing.assert_allclose(flux[:, 2], u * (U[:, 2] + 100_000.0), rtol=1e-12)


@pytest.mark.parametrize("U", [np.array([0.0, 0.0, 1.0]), np.array([-1.0, 0.0, 1.0])])
def test_flux_rejects_invalid_density(U: np.ndarray) -> None:
    """Flux evaluation rejects nonpositive conservative density."""
    with pytest.raises(ValueError, match="rho"):
        flux_module.euler_flux(U, GAS)


def test_flux_rejects_nonpositive_pressure() -> None:
    """Flux evaluation rejects states with nonpositive recovered pressure."""
    with pytest.raises(ValueError, match="p"):
        flux_module.euler_flux(np.array([1.0, 10.0, 49.0]), GAS)


@pytest.mark.parametrize("U", [np.array([np.nan, 0.0, 1.0]), np.array([1.0, np.inf, 1.0])])
def test_flux_rejects_nonfinite_conservative_values(U: np.ndarray) -> None:
    """Flux evaluation rejects NaN and infinity states."""
    with pytest.raises(ValueError):
        flux_module.euler_flux(U, GAS)


def test_flux_rejects_invalid_conservative_shape() -> None:
    """Flux evaluation requires exactly three values on the final axis."""
    with pytest.raises(ValueError, match="last dimension"):
        flux_module.euler_flux(np.zeros((10, 4)), GAS)


def test_mass_flux_equals_conservative_momentum() -> None:
    """The Euler mass-flux component always equals rho*u in U[..., 1]."""
    U = primitive_to_conservative(
        np.array([0.5, 1.0, 2.0]), np.array([300.0, 800.0, 1500.0]), np.array([50_000.0, 100_000.0, 300_000.0]), GAS
    )

    np.testing.assert_allclose(flux_module.euler_flux(U, GAS)[..., 0], U[..., 1], rtol=1e-12)
