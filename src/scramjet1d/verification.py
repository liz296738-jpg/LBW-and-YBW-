"""Analytical references and scalar metrics for controlled solver validation."""

from typing import NamedTuple

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .config import GasProperties
from .state import PrimitiveVariables, conservative_to_primitive, primitive_to_conservative
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


class UniformWallSourceReference(NamedTuple):
    """Exact uniform-wall-source conservative and primitive states."""

    U: NDArray[np.float64]
    primitive: PrimitiveVariables


class ResidualConvergenceAssessment(NamedTuple):
    """Classification of a grid-refined, source-normalized residual series."""

    classification: str
    monotone: bool
    final_order: float | None
    normalized_finest_error: float


def assess_residual_convergence(
    errors: ArrayLike,
    reference_scale: object,
    *,
    roundoff_threshold: float = 1e-10,
) -> ResidualConvergenceAssessment:
    """Classify residual refinement, allowing nonmonotone floating-point roundoff."""
    values = np.asarray(errors, dtype=float)
    scale = require_positive_scalar("reference_scale", reference_scale)
    threshold = require_positive_scalar("roundoff_threshold", roundoff_threshold)
    if values.ndim != 1 or values.size == 0:
        raise ValueError("errors must be a nonempty one-dimensional array")
    normalized_finest = float(values[-1] / scale) if np.isfinite(values[-1]) else float("inf")
    monotone = bool(np.all(np.isfinite(values)) and np.all(values[1:] < values[:-1]))
    if normalized_finest <= threshold:
        return ResidualConvergenceAssessment("roundoff-limited", monotone, None, normalized_finest)
    if not np.all(np.isfinite(values) & (values > 0.0)):
        return ResidualConvergenceAssessment("failed", monotone, None, normalized_finest)
    final_order = observed_order(values[-2], values[-1]) if values.size >= 2 else None
    if monotone and final_order is not None and final_order >= 0.75:
        classification = "superconvergent" if final_order > 1.5 else "convergent"
        return ResidualConvergenceAssessment(classification, monotone, final_order, normalized_finest)
    return ResidualConvergenceAssessment("failed", monotone, final_order, normalized_finest)


def _branch_name(branch: object) -> str:
    if branch not in ("subsonic", "supersonic"):
        raise ValueError("branch must be 'subsonic' or 'supersonic'")
    return str(branch)


def uniform_wall_source_reference(
    rho0: object,
    u0: object,
    p0: object,
    time: object,
    hydraulic_diameter: object,
    darcy_friction_factor: object,
    wall_heat_flux: object,
    gas: GasProperties,
) -> UniformWallSourceReference:
    """Return the exact uniform constant-area wall-source state in SI units."""
    density = require_positive_scalar("rho0", rho0)
    velocity = _finite_scalar("u0", u0)
    pressure = require_positive_scalar("p0", p0)
    elapsed = _nonnegative_scalar("time", time)
    diameter = require_positive_scalar("hydraulic_diameter", hydraulic_diameter)
    friction = _nonnegative_scalar("darcy_friction_factor", darcy_friction_factor)
    heat_flux = _finite_scalar("wall_heat_flux", wall_heat_flux)
    initial_energy = pressure / (gas.gamma - 1.0) + 0.5 * density * velocity**2
    final_velocity = velocity / (1.0 + friction * abs(velocity) * elapsed / (2.0 * diameter))
    final_energy = initial_energy + 4.0 * heat_flux * elapsed / diameter
    conservative = np.array([density, density * final_velocity, final_energy], dtype=float)
    return UniformWallSourceReference(U=conservative, primitive=conservative_to_primitive(conservative, gas))


def fanno_parameter(mach: ArrayLike, gas: GasProperties) -> NDArray[np.float64]:
    """Return the Darcy-convention Fanno distance-to-sonic parameter [-]."""
    M = require_positive("mach", mach)
    gamma = gas.gamma
    return (1.0 - M**2) / (gamma * M**2) + (gamma + 1.0) / (2.0 * gamma) * np.log((gamma + 1.0) * M**2 / (2.0 + (gamma - 1.0) * M**2))


def mach_from_fanno_parameter(value: ArrayLike, gas: GasProperties, branch: str) -> NDArray[np.float64]:
    """Invert the Darcy Fanno parameter on the requested non-sonic branch."""
    selected_branch = _branch_name(branch)
    values = np.asarray(value, dtype=float)
    if not np.all(np.isfinite(values) & (values >= 0.0)):
        raise ValueError("value must be finite and nonnegative")
    result = np.empty_like(values, dtype=float)
    for index, target in np.ndenumerate(values):
        if target == 0.0:
            result[index] = 1.0
            continue
        if selected_branch == "subsonic":
            low, high = np.finfo(float).eps, 1.0
        else:
            supersonic_limit = -1.0 / gas.gamma + (gas.gamma + 1.0) / (2.0 * gas.gamma) * np.log((gas.gamma + 1.0) / (gas.gamma - 1.0))
            if target >= supersonic_limit:
                raise ValueError("target Fanno parameter exceeds the supersonic branch limit")
            low, high = 1.0, 2.0
            while float(fanno_parameter(high, gas)) < target:
                high *= 2.0
                if high > 1e12:
                    raise RuntimeError("could not bracket supersonic Fanno Mach number")
        for _ in range(100):
            mid = 0.5 * (low + high)
            if selected_branch == "subsonic":
                if float(fanno_parameter(mid, gas)) > target:
                    low = mid
                else:
                    high = mid
            else:
                if float(fanno_parameter(mid, gas)) < target:
                    low = mid
                else:
                    high = mid
        result[index] = 0.5 * (low + high)
    return result


def rayleigh_t0_ratio(mach: ArrayLike, gas: GasProperties) -> NDArray[np.float64]:
    """Return the Rayleigh stagnation-temperature ratio T0/T0_star [-]."""
    M = require_positive("mach", mach)
    gamma = gas.gamma
    return (gamma + 1.0) * M**2 * (2.0 + (gamma - 1.0) * M**2) / (1.0 + gamma * M**2) ** 2


def mach_from_rayleigh_t0_ratio(value: ArrayLike, gas: GasProperties, branch: str) -> NDArray[np.float64]:
    """Invert the Rayleigh T0/T0_star ratio on the requested branch."""
    selected_branch = _branch_name(branch)
    values = np.asarray(value, dtype=float)
    if not np.all(np.isfinite(values) & (values > 0.0) & (values <= 1.0)):
        raise ValueError("value must be finite, positive, and no greater than one")
    result = np.empty_like(values, dtype=float)
    lower_limit = (gas.gamma**2 - 1.0) / gas.gamma**2
    for index, target in np.ndenumerate(values):
        if target == 1.0:
            result[index] = 1.0
            continue
        if selected_branch == "subsonic":
            low, high = np.finfo(float).eps, 1.0
        else:
            if target <= lower_limit:
                raise ValueError("supersonic Rayleigh ratio is below the branch limit")
            low, high = 1.0, 2.0
            while float(rayleigh_t0_ratio(high, gas)) > target:
                high *= 2.0
                if high > 1e12:
                    raise RuntimeError("could not bracket supersonic Rayleigh Mach number")
        for _ in range(100):
            mid = 0.5 * (low + high)
            if selected_branch == "subsonic":
                if float(rayleigh_t0_ratio(mid, gas)) < target:
                    low = mid
                else:
                    high = mid
            else:
                if float(rayleigh_t0_ratio(mid, gas)) > target:
                    low = mid
                else:
                    high = mid
        result[index] = 0.5 * (low + high)
    return result


def _reference_positions(x: ArrayLike) -> NDArray[np.float64]:
    positions = _positions(x)
    if not np.all(positions >= 0.0):
        raise ValueError("x must be nonnegative for downstream reference profiles")
    return positions


def _branch_mach(mach: object, branch: str) -> float:
    value = require_positive_scalar("mach_in", mach)
    if (branch == "subsonic" and value >= 1.0) or (branch == "supersonic" and value <= 1.0):
        raise ValueError("mach_in must lie strictly on the requested branch")
    return value


def fanno_flow_reference(
    x: ArrayLike,
    rho_in: object,
    p_in: object,
    mach_in: object,
    hydraulic_diameter: object,
    darcy_friction_factor: object,
    gas: GasProperties,
    branch: str,
) -> PrimitiveVariables:
    """Return a constant-area Darcy-Fanno profile before the sonic point."""
    positions = _reference_positions(x)
    selected_branch = _branch_name(branch)
    density_in = require_positive_scalar("rho_in", rho_in)
    pressure_in = require_positive_scalar("p_in", p_in)
    inlet_mach = _branch_mach(mach_in, selected_branch)
    diameter = require_positive_scalar("hydraulic_diameter", hydraulic_diameter)
    friction = _nonnegative_scalar("darcy_friction_factor", darcy_friction_factor)
    target_parameter = fanno_parameter(inlet_mach, gas) - friction * positions / diameter
    if not np.all(target_parameter > 0.0):
        raise ValueError("Fanno profile reaches or crosses the sonic point")
    mach = mach_from_fanno_parameter(target_parameter, gas, selected_branch)
    temperature_in = pressure_in / (density_in * gas.R)
    t0 = temperature_in * (1.0 + (gas.gamma - 1.0) * inlet_mach**2 / 2.0)
    temperature = t0 / (1.0 + (gas.gamma - 1.0) * mach**2 / 2.0)
    velocity = mach * np.sqrt(gas.gamma * gas.R * temperature)
    mass_flux = density_in * inlet_mach * np.sqrt(gas.gamma * gas.R * temperature_in)
    density = mass_flux / velocity
    pressure = density * gas.R * temperature
    return conservative_to_primitive(primitive_to_conservative(density, velocity, pressure, gas), gas)


def rayleigh_flow_reference(
    x: ArrayLike,
    rho_in: object,
    p_in: object,
    mach_in: object,
    hydraulic_diameter: object,
    wall_heat_flux: object,
    gas: GasProperties,
    branch: str,
) -> PrimitiveVariables:
    """Return a constant-area prescribed-heat Rayleigh profile before sonic flow."""
    positions = _reference_positions(x)
    selected_branch = _branch_name(branch)
    density_in = require_positive_scalar("rho_in", rho_in)
    pressure_in = require_positive_scalar("p_in", p_in)
    inlet_mach = _branch_mach(mach_in, selected_branch)
    diameter = require_positive_scalar("hydraulic_diameter", hydraulic_diameter)
    heat_flux = _finite_scalar("wall_heat_flux", wall_heat_flux)
    temperature_in = pressure_in / (density_in * gas.R)
    inlet_velocity = inlet_mach * np.sqrt(gas.gamma * gas.R * temperature_in)
    mass_flux = density_in * inlet_velocity
    cp = gas.gamma * gas.R / (gas.gamma - 1.0)
    t0_in = temperature_in * (1.0 + (gas.gamma - 1.0) * inlet_mach**2 / 2.0)
    t0_star = t0_in / rayleigh_t0_ratio(inlet_mach, gas)
    t0 = t0_in + 4.0 * heat_flux * positions / (diameter * mass_flux * cp)
    ratio = t0 / t0_star
    mach = mach_from_rayleigh_t0_ratio(ratio, gas, selected_branch)
    temperature = t0 / (1.0 + (gas.gamma - 1.0) * mach**2 / 2.0)
    velocity = mach * np.sqrt(gas.gamma * gas.R * temperature)
    density = mass_flux / velocity
    pressure = density * gas.R * temperature
    return conservative_to_primitive(primitive_to_conservative(density, velocity, pressure, gas), gas)
