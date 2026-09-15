"""Signed prescribed net-energy source support for reduced-order studies.

This module deliberately sits beside the production combustion interfaces.  The
existing ``heat_release_rate_per_length`` path is chemical heat release and is
therefore nonnegative.  A reduced-order reference solution may instead imply a
*signed* net energy addition: positive values add energy to the gas and negative
values remove it.  No mass or axial momentum is added by this interface.

The wrapper is intentionally narrow so legacy solver behaviour is untouched.
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


def signed_net_energy_source(
    U: ArrayLike,
    geometry: AreaProfile,
    net_energy_rate_per_length: ArrayLike,
    gas: GasProperties,
) -> NDArray[np.float64]:
    """Return ``[0, 0, Qdot'_net/A]`` for a signed line-energy rate [W/m].

    ``net_energy_rate_per_length`` may be positive, zero, or negative and must
    be finite and broadcast to the state-cell shape.  Positive values add
    energy to the gas; negative values remove energy.  This is *not* labelled
    combustion heat release and must not be interpreted as a measured chemical
    heat-release distribution.
    """

    if not isinstance(geometry, AreaProfile):
        raise TypeError("geometry must be an AreaProfile")
    states = np.asarray(U, dtype=float)
    if states.ndim < 2 or states.shape[-1] != 3:
        raise ValueError("U must have shape (..., N, 3) for axial distribution")
    if states.shape[-2] != geometry.num_cells:
        raise ValueError("U cell count must match geometry.num_cells")

    primitive = conservative_to_primitive(states, gas)
    target_shape = primitive.rho.shape
    line_energy = np.asarray(net_energy_rate_per_length, dtype=float)
    try:
        line_energy = np.broadcast_to(line_energy, target_shape)
    except ValueError as error:
        raise ValueError("net_energy_rate_per_length must broadcast to the state shape") from error
    if not np.all(np.isfinite(line_energy)):
        raise ValueError("net_energy_rate_per_length must be finite")

    source = np.zeros_like(states, dtype=float)
    source[..., 2] = line_energy / geometry.cell_area
    return source


def quasi_1d_rhs_with_net_energy(
    U: ArrayLike,
    geometry: AreaProfile,
    dx: object,
    gas: GasProperties,
    *,
    net_energy_rate_per_length: ArrayLike,
    flux_scheme: object = "rusanov",
    boundary_conditions: BoundaryConditions | None = None,
) -> NDArray[np.float64]:
    """Compose the production quasi-1D RHS with a signed net-energy source."""

    base = quasi_1d_rhs(
        U,
        geometry,
        dx,
        gas,
        flux_scheme=flux_scheme,
        boundary_conditions=boundary_conditions,
    )
    return base + signed_net_energy_source(U, geometry, net_energy_rate_per_length, gas)


def solve_quasi_1d_steady_with_net_energy(
    U0: ArrayLike,
    geometry: AreaProfile,
    dx: object,
    max_time: object,
    gas: GasProperties,
    numerical: NumericalConfig,
    *,
    net_energy_rate_per_length: ArrayLike,
    max_steps: int = 100_000,
    flux_scheme: object = "rusanov",
    boundary_conditions: BoundaryConditions | None = None,
) -> SteadySolverResult:
    """Steady pseudo-time solve using only the signed net-energy extension.

    This reduced-order wrapper intentionally does not expose the combustion,
    fuel-injection, friction, or wall-heat arguments from the production
    solver.  A caller choosing a net reference-solution-derived energy closure
    therefore cannot silently double count those energy mechanisms here.
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
    reference = steady_residual_reference(state, spacing, gas)

    def rhs(stage_state: NDArray[np.float64]) -> NDArray[np.float64]:
        return quasi_1d_rhs_with_net_energy(
            stage_state,
            geometry,
            spacing,
            gas,
            net_energy_rate_per_length=net_energy_rate_per_length,
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
            f"steady net-energy solve failed during initial residual at step 0, time=0: {error}"
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
                f"steady net-energy solve failed during CFL/SSP-RK3/state validation at step {steps}, time={time}: {error}"
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
