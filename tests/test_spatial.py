"""Tests for finite-volume spatial assembly and residuals."""

import numpy as np
import pytest

from scramjet1d.config import GasProperties
from scramjet1d.flux import euler_flux, rusanov_flux
from scramjet1d.state import primitive_to_conservative
import scramjet1d.spatial as spatial


GAS = GasProperties()


def test_uniform_grid_states_produce_physical_internal_fluxes() -> None:
    """Equal neighboring cells have internal flux equal to the physical flux."""
    state = primitive_to_conservative(1.2, 500.0, 120_000.0, GAS)
    U = np.broadcast_to(state, (5, 3)).copy()

    fluxes = spatial.internal_rusanov_fluxes(U, GAS)

    assert fluxes.shape == (4, 3)
    np.testing.assert_allclose(fluxes, np.broadcast_to(euler_flux(state, GAS), (4, 3)), rtol=1e-12)


def test_internal_fluxes_join_adjacent_cells() -> None:
    """Internal interface j is evaluated from cells j and j+1."""
    U = primitive_to_conservative(
        np.array([1.0, 0.8, 0.6]), np.array([300.0, 500.0, 800.0]), np.array([100_000.0, 90_000.0, 80_000.0]), GAS
    )

    fluxes = spatial.internal_rusanov_fluxes(U, GAS)

    np.testing.assert_allclose(fluxes[0], rusanov_flux(U[0], U[1], GAS), rtol=1e-12)
    np.testing.assert_allclose(fluxes[1], rusanov_flux(U[1], U[2], GAS), rtol=1e-12)


def test_internal_fluxes_treat_penultimate_axis_as_cells() -> None:
    """Batch dimensions remain separate while the penultimate axis indexes cells."""
    U = primitive_to_conservative(
        np.array([[1.0, 0.9, 0.8, 0.7], [0.8, 0.7, 0.6, 0.5]]),
        np.array([[200.0, 300.0, 400.0, 500.0], [150.0, 250.0, 350.0, 450.0]]),
        np.array([[100_000.0, 95_000.0, 90_000.0, 85_000.0], [80_000.0, 75_000.0, 70_000.0, 65_000.0]]),
        GAS,
    )

    fluxes = spatial.internal_rusanov_fluxes(U, GAS)

    assert fluxes.shape == (2, 3, 3)
    np.testing.assert_allclose(fluxes[0], rusanov_flux(U[0, :-1], U[0, 1:], GAS), rtol=1e-12)
    np.testing.assert_allclose(fluxes[1], rusanov_flux(U[1, :-1], U[1, 1:], GAS), rtol=1e-12)


@pytest.mark.parametrize("U", [np.zeros((1, 3)), np.zeros(3), np.zeros((3, 4))])
def test_internal_fluxes_reject_invalid_grid_shape(U: np.ndarray) -> None:
    """A spatial grid needs at least two cells and three conservative components."""
    with pytest.raises(ValueError):
        spatial.internal_rusanov_fluxes(U, GAS)


@pytest.mark.parametrize("U", [np.array([[np.nan, 0.0, 1.0], [1.0, 0.0, 1.0]]), np.array([[1.0, 10.0, 49.0], [1.0, 0.0, 1.0]])])
def test_internal_fluxes_reject_invalid_states(U: np.ndarray) -> None:
    """Internal assembly propagates invalid conservative-state errors."""
    with pytest.raises(ValueError):
        spatial.internal_rusanov_fluxes(U, GAS)


def test_constant_interface_flux_has_zero_residual() -> None:
    """Constant complete interface fluxes have zero finite-volume divergence."""
    interface_fluxes = np.broadcast_to(np.array([10.0, 20.0, 30.0]), (5, 3)).copy()

    residual = spatial.finite_volume_residual(interface_fluxes, 0.1)

    assert residual.shape == (4, 3)
    np.testing.assert_allclose(residual, 0.0, atol=1e-14)


def test_residual_matches_hand_computed_flux_differences() -> None:
    """Residual uses negative right-minus-left flux differences divided by dx."""
    interface_fluxes = np.array([[0.0, 0.0, 0.0], [1.0, 10.0, 100.0], [3.0, 30.0, 300.0], [6.0, 60.0, 600.0]])

    residual = spatial.finite_volume_residual(interface_fluxes, 0.5)

    np.testing.assert_allclose(residual, np.array([[-2.0, -20.0, -200.0], [-4.0, -40.0, -400.0], [-6.0, -60.0, -600.0]]), rtol=1e-12)


def test_residual_satisfies_telescoping_conservation_identity() -> None:
    """Summed residual times dx equals left boundary flux minus right boundary flux."""
    interface_fluxes = np.array([[0.0, 0.0, 0.0], [1.0, 10.0, 100.0], [3.0, 30.0, 300.0], [6.0, 60.0, 600.0]])
    dx = 0.5

    residual = spatial.finite_volume_residual(interface_fluxes, dx)

    np.testing.assert_allclose(np.sum(residual, axis=-2) * dx, interface_fluxes[0] - interface_fluxes[-1], rtol=1e-12)


def test_batched_residual_satisfies_telescoping_conservation_identity() -> None:
    """The conservative telescoping relation holds independently for each batch."""
    interface_fluxes = np.array([[[0.0, 0.0, 0.0], [1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [8.0, 9.0, 10.0], [11.0, 12.0, 13.0]], [[-2.0, -3.0, -4.0], [-1.0, -1.0, -1.0], [1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]]])
    dx = 0.25

    residual = spatial.finite_volume_residual(interface_fluxes, dx)

    assert residual.shape == (2, 4, 3)
    np.testing.assert_allclose(np.sum(residual, axis=-2) * dx, interface_fluxes[:, 0] - interface_fluxes[:, -1], rtol=1e-12)


def test_negative_interface_flux_is_legal() -> None:
    """Fluxes may be negative because they are not conservative states."""
    interface_fluxes = np.array([[-3.0, 1.0, -5.0], [-2.0, 2.0, -4.0]])

    np.testing.assert_allclose(spatial.finite_volume_residual(interface_fluxes, 1.0), [[-1.0, -1.0, -1.0]])


@pytest.mark.parametrize("dx", [0.0, -0.1, np.nan, np.inf, np.array([0.1, 0.1])])
def test_residual_rejects_invalid_uniform_grid_spacing(dx: object) -> None:
    """P3.3 accepts only finite, strictly positive scalar dx."""
    with pytest.raises(ValueError):
        spatial.finite_volume_residual(np.zeros((2, 3)), dx)


@pytest.mark.parametrize("interface_fluxes", [np.zeros((1, 3)), np.zeros((3, 4)), np.array([[np.nan, 0.0, 0.0], [0.0, 0.0, 0.0]])])
def test_residual_rejects_invalid_interface_fluxes(interface_fluxes: np.ndarray) -> None:
    """Residual accepts only finite arrays with at least two three-component interfaces."""
    with pytest.raises(ValueError):
        spatial.finite_volume_residual(interface_fluxes, 0.1)
