"""Tests for primitive and conservative state conversions."""

import numpy as np
import pytest

from scramjet1d.config import GasProperties
import scramjet1d.state as state_module


GAS = GasProperties()


def test_scalar_primitive_to_conservative_matches_definition() -> None:
    """A scalar primitive state maps to the three defined conserved values."""
    rho, u, p = 1.0, 1000.0, 100_000.0

    U = state_module.primitive_to_conservative(rho, u, p, GAS)
    expected_energy = p / (rho * (GAS.gamma - 1.0)) + u**2 / 2.0

    assert U.shape == (3,)
    np.testing.assert_allclose(U, [rho, rho * u, rho * expected_energy], rtol=1e-12)


def test_scalar_round_trip_preserves_primitive_variables() -> None:
    """A scalar primitive state survives conservative conversion at float precision."""
    rho, u, p = 1.2, 750.0, 150_000.0

    primitive = state_module.conservative_to_primitive(
        state_module.primitive_to_conservative(rho, u, p, GAS), GAS
    )

    np.testing.assert_allclose([primitive.rho, primitive.u, primitive.p], [rho, u, p], rtol=1e-12)
    assert primitive.T == pytest.approx(p / (rho * GAS.R), rel=1e-12)
    assert primitive.Mach == pytest.approx(u / np.sqrt(GAS.gamma * GAS.R * primitive.T), rel=1e-12)


def test_vector_round_trip_preserves_primitive_variables() -> None:
    """Vectorized conversion preserves each primitive field and output shape."""
    rho = np.array([0.5, 1.0, 2.0])
    u = np.array([300.0, 1000.0, 1800.0])
    p = np.array([50_000.0, 100_000.0, 300_000.0])

    U = state_module.primitive_to_conservative(rho, u, p, GAS)
    primitive = state_module.conservative_to_primitive(U, GAS)

    assert U.shape == (3, 3)
    np.testing.assert_allclose(primitive.rho, rho, rtol=1e-12)
    np.testing.assert_allclose(primitive.u, u, rtol=1e-12)
    np.testing.assert_allclose(primitive.p, p, rtol=1e-12)


def test_negative_velocity_is_preserved() -> None:
    """Reverse flow remains mathematically valid and retains its sign."""
    U = state_module.primitive_to_conservative(1.0, -100.0, 100_000.0, GAS)
    primitive = state_module.conservative_to_primitive(U, GAS)

    assert primitive.u == pytest.approx(-100.0)
    assert primitive.Mach < 0.0


@pytest.mark.parametrize(
    "U",
    [np.array([0.0, 0.0, 1.0]), np.array([-1.0, 0.0, 1.0]), np.array([np.nan, 0.0, 1.0])],
)
def test_conservative_to_primitive_rejects_invalid_density(U: np.ndarray) -> None:
    """Conservative density must be finite and strictly positive."""
    with pytest.raises(ValueError, match="rho"):
        state_module.conservative_to_primitive(U, GAS)


def test_conservative_to_primitive_rejects_nonpositive_pressure() -> None:
    """A state with no positive internal energy is rejected without clipping."""
    U = np.array([1.0, 10.0, 49.0])

    with pytest.raises(ValueError, match="p"):
        state_module.conservative_to_primitive(U, GAS)


def test_conservative_to_primitive_rejects_invalid_shape() -> None:
    """The last conservative-state dimension must contain exactly three values."""
    with pytest.raises(ValueError, match="last dimension"):
        state_module.conservative_to_primitive(np.zeros((10, 4)), GAS)


@pytest.mark.parametrize("u", [np.nan, np.inf])
def test_primitive_to_conservative_rejects_nonfinite_velocity(u: float) -> None:
    """Velocity must be finite but may have either sign."""
    with pytest.raises(ValueError, match="u"):
        state_module.primitive_to_conservative(1.0, u, 100_000.0, GAS)
