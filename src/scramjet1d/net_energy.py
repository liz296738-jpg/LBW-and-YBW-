"""Signed reference-derived source support for reduced-order studies.

This module deliberately sits beside the production combustion and wall-source
interfaces.  The existing ``heat_release_rate_per_length`` path is chemical
heat release and therefore remains nonnegative.  A reduced-order computational
reference may instead imply signed *net* energy and axial-momentum additions.
Positive values add the corresponding conserved quantity to the gas; negative
values remove it.  Neither source adds mass.

The wrapper is intentionally narrow so legacy production-solver behaviour and
combustion semantics are untouched.
"""

from __future__ import annotations

from typing import Literal

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .boundary import BoundaryConditions, validate_boundary_conditions
from .config import GasProperties, NumericalConfig
from .convergence import normalized_steady_residual, steady_residual_reference
from .geometry import AreaProfile
from .solver import SteadySolverResult, cfl_timestep, quasi_1d_rhs
from .state import conservative_to_primitive
from .time_integration import ssp_rk3_step


def _broadcast_signed_line_quantity(
    name: str,
    U: ArrayLike,
    geometry: AreaProfile,
    values: ArrayLike,
    gas: GasProperties,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    if not isinstance(geometry, AreaProfile):
        raise TypeError("geometry must be an AreaProfile")
    states = np.asarray(U, dtype=float)
    if states.ndim < 2 or states.shape[-1] != 3:
        raise ValueError("U must have shape (..., N, 3) for axial distribution")
    if states.shape[-2] != geometry.num_cells:
        raise ValueError("U cell count must match geometry.num_cells")
    primitive = conservative_to_primitive(states, gas)
    line_values = np.asarray(values, dtype=float)
    try:
        line_values = np.broadcast_to(line_values, primitive.rho.shape)
    except ValueError as error:
        raise ValueError(f"{name} must broadcast to the state shape") from error
    if not np.all(np.isfinite(line_values)):
        raise ValueError(f"{name} must be finite")
    return states, line_values


def signed_net_energy_source(
    U: ArrayLike,
    geometry: AreaProfile,
    net_energy_rate_per_length: ArrayLike,
    gas: GasProperties,
) -> NDArray[np.float64]:
    """Return ``[0, 0, Qdot'_net/A]`` for a signed line-energy rate [W/m].

    This is not labelled combustion heat release and must not be interpreted as
    a measured chemical heat-release distribution.
    """

    states, line_energy = _broadcast_signed_line_quantity(
        "net_energy_rate_per_length", U, geometry, net_energy_rate_per_length, gas
    )
    source = np.zeros_like(states, dtype=float)
    source[..., 2] = line_energy / geometry.cell_area
    return source


def signed_net_momentum_source(
    U: ArrayLike,
    geometry: AreaProfile,
    net_momentum_rate_per_length: ArrayLike,
    gas: GasProperties,
) -> NDArray[np.float64]:
    """Return ``[0, F'_net/A, 0]`` for a signed axial line force [N/m].

    The source represents a reference-derived residual streamwise force after
    the quasi-1D pressure-area term has already been accounted for.  It is not
    relabelled as Darcy friction, wall shear, or an experimental measurement.
    """

    states, line_force = _broadcast_signed_line_quantity(
        "net_momentum_rate_per_length", U, geometry, net_momentum_rate_per_length, gas
    )
    source = np.zeros_like(states, dtype=float)
    source[..., 1] = line_force / geometry.cell_area
    return source


def quasi_1d_rhs_with_net_energy(
    U: ArrayLike,
    geometry: AreaProfile,
    dx: object,
    gas: GasProperties,
    *,
    net_energy_rate_per_length: ArrayLike,
    net_momentum_rate_per_length: ArrayLike = 0.0,
    flux_scheme: object = "rusanov",
    boundary_conditions: BoundaryConditions | None = None,
) -> NDArray[np.float64]:
    """Compose production quasi-1D RHS with signed reference-derived sources."""

    base = quasi_1d_rhs(
        U,
        geometry,
        dx,
        gas,
        flux_scheme=flux_scheme,
        boundary_conditions=boundary_conditions,
    )
    return (
        base
        + signed_net_energy_source(U, geometry, net_energy_rate_per_length, gas)
        + signed_net_momentum_source(U, geometry, net_momentum_rate_per_length, gas)
    )


def solve_quasi_1d_steady_with_net_energy(
    U0: ArrayLike,
    geometry: AreaProfile,
    dx: object,
    max_time: object,
    gas: GasProperties,
    numerical: NumericalConfig,
    *,
    net_energy_rate_per_length: ArrayLike,
    net_momentum_rate_per_length: ArrayLike = 0.0,
    max_steps: int = 100_000,
    flux_scheme: object = "rusanov",
    boundary_conditions: BoundaryConditions | None = None,
) -> SteadySolverResult:
    """Steady pseudo-time solve with isolated signed reference-derived sources.

    The legacy name is retained for compatibility.  The optional signed
    momentum source is zero by default, so every pre-existing energy-only call
    remains numerically identical.  This wrapper intentionally does not expose
    combustion, fuel-injection, friction, or wall-heat arguments; a caller
    using computational-reference-derived net sources therefore cannot silently
    double count those mechanisms here.
    """

    state = np.asarray(U0, dtype=float)
    if state.ndim != 2 or state.shape[-1] != 3 or state.shape[0] < 2:
        raise ValueError("U0 must have shape (N, 3) with N >= 2")
    if not isinstance(geometry, AreaProfile) or geometry.num_cells != state.shape[0]:
        raise ValueError("geometry.num_cells must match U0 cell count")
    conservative_to_primitive(state, gas)

    spacing_array = np.asarray(dx, dtype=float)
    if spacing_array.ndim != 0 or not np.isfinite(spacing_array) or spacing_array <= 0.0:
        raise ValueError("dx must be a finite and strictly positive scalar")
    spacing = float(spacing_array)
    time_array = np.asarray(max_time, dtype=float)
    if time_array.ndim != 0 or not np.isfinite(time_array) or time_array <= 0.0:
        raise ValueError("max_time must be a finite and strictly positive scalar")
    final_time = float(time_array)
    if isinstance(max_steps, (bool, np.bool_)) or not isinstance(max_steps, (int, np.integer)) or max_steps <= 0:
        raise ValueError("max_steps must be a positive integer")
    if flux_scheme not in ("rusanov", "steger-warming"):
        raise ValueError("supported schemes are 'rusanov' and 'steger-warming'")

    conditions = validate_boundary_conditions(boundary_conditions, state, gas)
    signed_net_energy_source(state, geometry, net_energy_rate_per_length, gas)
    signed_net_momentum_source(state, geometry, net_momentum_rate_per_length, gas)
    reference = steady_residual_reference(state, spacing, gas)

    def rhs(stage_state: NDArray[np.float64]) -> NDArray[np.float64]:
        return quasi_1d_rhs_with_net_energy(
            stage_state,
            geometry,
            spacing,
            gas,
            net_energy_rate_per_length=net_energy_rate_per_length,
            net_momentum_rate_per_length=net_momentum_rate_per_length,
            flux_scheme=flux_scheme,
            boundary_conditions=conditions,
        )

    state = np.array(state, dtype=float, copy=True)
    time = 0.0
    steps = 0
    try:
        residual = normalized_steady_residual(rhs(state), reference)
    except (ValueError, FloatingPointError) as error:
        raise RuntimeError(
            f"steady reference-source solve failed during initial residual at step 0, time=0: {error}"
        ) from error
    residuals, times = [residual], [time]

    while residual > numerical.tolerance and time < final_time and steps < max_steps:
        try:
            dt = min(cfl_timestep(state, spacing, gas, numerical), final_time - time)
            state = ssp_rk3_step(state, dt, rhs)
            conservative_to_primitive(state, gas)
            time += dt
            steps += 1
            residual = normalized_steady_residual(rhs(state), reference)
        except (ValueError, FloatingPointError) as error:
            raise RuntimeError(
                f"steady reference-source solve failed during CFL/SSP-RK3/state validation at step {steps}, time={time}: {error}"
            ) from error
        residuals.append(residual)
        times.append(time)

    converged = residual <= numerical.tolerance
    reason: Literal["converged", "max-time", "max-steps"] = (
        "converged" if converged else ("max-time" if time >= final_time else "max-steps")
    )
    result_state = state.copy()
    residual_history = np.asarray(residuals)
    time_history = np.asarray(times)
    result_state.setflags(write=False)
    residual_history.setflags(write=False)
    time_history.setflags(write=False)
    return SteadySolverResult(
        result_state,
        time,
        steps,
        converged,
        reason,
        residual,
        residual_history,
        time_history,
    )
