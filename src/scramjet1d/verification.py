"""Analytical references and scalar metrics for controlled solver validation."""

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .config import GasProperties
from .state import PrimitiveVariables
from .validation import require_finite, require_positive, require_positive_scalar


def _nonnegative_scalar(name: str, value: object) -> float:
    scalar = np.asarray(value, dtype=float)
    if scalar.ndim != 0 or not np.isfinite(scalar) or scalar < 0.0:
        raise ValueError(f"{name} must be a finite nonnegative scalar")
    return float(scalar)


def _finite_scalar(name: str, value: object) -> float:
    scalar = np.asarray(value, dtype=float)
    if scalar.ndim != 0 or not np.isfinite(scalar):
        raise ValueError(f"{name} must be a finite scalar")
    return float(scalar)


def _positions(x: ArrayLike) -> NDArray[np.float64]:
    positions = require_finite("x", x)
    if positions.ndim != 1:
        raise ValueError("x must be one-dimensional")
    return positions


def smooth_entropy_wave_reference(
    x: ArrayLike,
    time: object,
    rho0: object,
    velocity: object,
    pressure: object,
    amplitude: object,
    center: object,
    sigma: object,
    gas: GasProperties,
) -> PrimitiveVariables:
    """Return the exact right-going smooth entropy-wave state in SI units."""
    positions = _positions(x)
    elapsed = _nonnegative_scalar("time", time)
    base_density = require_positive_scalar("rho0", rho0)
    base_pressure = require_positive_scalar("pressure", pressure)
    speed = _finite_scalar("velocity", velocity)
    wave_amplitude = _finite_scalar("amplitude", amplitude)
    wave_center = _finite_scalar("center", center)
    width = require_positive_scalar("sigma", sigma)
    density = base_density * (1.0 + wave_amplitude * np.exp(-((positions - wave_center - speed * elapsed) / width) ** 2))
    require_positive("density", density)
    temperature = base_pressure / (density * gas.R)
    sound_speed = np.sqrt(gas.gamma * gas.R * temperature)
    return PrimitiveVariables(rho=density, u=np.full_like(density, speed), p=np.full_like(density, base_pressure), T=temperature, Mach=speed / sound_speed)


def advected_contact_reference(
    x: ArrayLike,
    time: object,
    rho_left: object,
    rho_right: object,
    velocity: object,
    pressure: object,
    contact_position: object,
    gas: GasProperties,
) -> PrimitiveVariables:
    """Return the exact constant-pressure contact discontinuity translated by velocity."""
    positions = _positions(x)
    elapsed = _nonnegative_scalar("time", time)
    left_density = require_positive_scalar("rho_left", rho_left)
    right_density = require_positive_scalar("rho_right", rho_right)
    speed = _finite_scalar("velocity", velocity)
    static_pressure = require_positive_scalar("pressure", pressure)
    initial_position = _finite_scalar("contact_position", contact_position)
    density = np.where(positions < initial_position + speed * elapsed, left_density, right_density)
    temperature = static_pressure / (density * gas.R)
    sound_speed = np.sqrt(gas.gamma * gas.R * temperature)
    return PrimitiveVariables(rho=density, u=np.full_like(density, speed), p=np.full_like(density, static_pressure), T=temperature, Mach=speed / sound_speed)


def l1_error(numerical: ArrayLike, reference: ArrayLike) -> float:
    """Return the mean absolute error between equally shaped finite arrays."""
    numerical_values = require_finite("numerical", numerical)
    reference_values = require_finite("reference", reference)
    if numerical_values.shape != reference_values.shape:
        raise ValueError("numerical and reference must have identical shapes")
    if numerical_values.size == 0:
        raise ValueError("numerical and reference must not be empty")
    return float(np.mean(np.abs(numerical_values - reference_values)))


def observed_order(coarse_error: object, fine_error: object) -> float:
    """Return the two-grid refinement order for a factor-of-two grid refinement."""
    coarse = require_positive_scalar("coarse_error", coarse_error)
    fine = require_positive_scalar("fine_error", fine_error)
    return float(np.log(coarse / fine) / np.log(2.0))


def transition_width_cells(density: ArrayLike, rho_left: object, rho_right: object) -> int:
    """Count cells whose normalized contact state lies strictly between 0.1 and 0.9."""
    values = require_finite("density", density)
    if values.ndim != 1 or values.size == 0:
        raise ValueError("density must be a nonempty one-dimensional array")
    left = require_positive_scalar("rho_left", rho_left)
    right = require_positive_scalar("rho_right", rho_right)
    if left == right:
        raise ValueError("rho_left and rho_right must differ")
    theta = (values - right) / (left - right)
    return int(np.count_nonzero((theta > 0.1) & (theta < 0.9)))
