"""Fixed-composition variable-thermodynamic conservative state conversion.

This is an isolated P11.3B compatibility path for the teacher/Cao thermochemical
model. It deliberately does not replace :mod:`scramjet1d.state`, which remains
the accepted calorically-perfect-gas baseline.

The current scope uses one fixed mass-fraction mapping for the supplied state
array. Cell-wise composition evolution belongs to the later teacher
mixing/reaction closure stage.
"""

from __future__ import annotations

from typing import Mapping, NamedTuple

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .thermochemistry import (
    PiecewiseSpeciesThermo,
    SpeciesThermoModel,
    mixture_thermo_state,
    normalized_mass_fractions,
    temperature_from_specific_internal_energy,
)


class VariableThermoPrimitiveVariables(NamedTuple):
    """Primitive fields for a fixed-composition variable-thermo state."""

    rho: NDArray[np.float64]
    u: NDArray[np.float64]
    p: NDArray[np.float64]
    T: NDArray[np.float64]
    Mach: NDArray[np.float64]
    gamma: NDArray[np.float64]
    R: NDArray[np.float64]
    cp: NDArray[np.float64]
    h: NDArray[np.float64]


def common_temperature_bounds(
    mass_fractions: Mapping[str, float],
    species: Mapping[str, SpeciesThermoModel],
) -> tuple[float, float]:
    """Return the common valid thermo interval for all active species.

    Species with zero mass fraction do not constrain the usable interval. No
    extension beyond any source-backed polynomial range is allowed.
    """

    fractions = normalized_mass_fractions(mass_fractions, species)
    active = [species[name] for name, value in fractions.items() if value > 0.0]
    lower = max(model.temperature_min_K for model in active)
    upper = min(model.temperature_max_K for model in active)
    if not np.isfinite(lower) or not np.isfinite(upper) or upper <= lower:
        raise ValueError("active species do not share a valid temperature interval")
    return float(lower), float(upper)


def _broadcast_primitive_inputs(
    rho: ArrayLike,
    u: ArrayLike,
    temperature_K: ArrayLike,
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    density, velocity, temperature = np.broadcast_arrays(
        np.asarray(rho, dtype=float),
        np.asarray(u, dtype=float),
        np.asarray(temperature_K, dtype=float),
    )
    if not np.all(np.isfinite(density) & (density > 0.0)):
        raise ValueError("rho must be finite and strictly positive")
    if not np.all(np.isfinite(velocity)):
        raise ValueError("u must be finite")
    if not np.all(np.isfinite(temperature)):
        raise ValueError("temperature_K must be finite")
    return density, velocity, temperature


def _recover_temperature(
    target_internal_energy_J_per_kg: float,
    mass_fractions: Mapping[str, float],
    species: Mapping[str, SpeciesThermoModel],
    *,
    temperature_min_K: float,
    temperature_max_K: float,
    temperature_tolerance_K: float,
    max_iterations: int,
) -> float:
    """Invert mixture internal energy with deterministic source-switch handling.

    CHEMKIN/NASA low/high polynomial records are fitted independently and are
    only continuous to finite tabulation precision at their switch temperature.
    A state generated *exactly* at a source switch can therefore otherwise be
    inverted to a temperature a tiny distance on the high-temperature branch.

    Before the generic bounded inversion, this helper checks whether the target
    energy is the round-off-equivalent of the mixture energy evaluated exactly
    at any active piecewise switch. If so, it returns that source switch
    temperature. This is not clipping: only machine-roundoff-equivalent values
    are locked, and no finite energy gap is interpolated or hidden.
    """

    target = float(target_internal_energy_J_per_kg)
    active_switches = sorted(
        {
            float(model.switch_temperature_K)
            for name, fraction in mass_fractions.items()
            if fraction > 0.0
            for model in (species[name],)
            if isinstance(model, PiecewiseSpeciesThermo)
            and temperature_min_K <= model.switch_temperature_K <= temperature_max_K
        }
    )
    for switch in active_switches:
        switch_energy = mixture_thermo_state(
            switch, mass_fractions, species
        ).specific_internal_energy_J_per_kg
        scale = max(abs(target), abs(switch_energy), 1.0)
        roundoff_tolerance = 64.0 * np.finfo(float).eps * scale
        if abs(target - switch_energy) <= roundoff_tolerance:
            return switch

    return temperature_from_specific_internal_energy(
        target,
        mass_fractions,
        species,
        temperature_min_K=temperature_min_K,
        temperature_max_K=temperature_max_K,
        temperature_tolerance_K=temperature_tolerance_K,
        max_iterations=max_iterations,
    )


def variable_primitive_to_conservative(
    rho: ArrayLike,
    u: ArrayLike,
    temperature_K: ArrayLike,
    mass_fractions: Mapping[str, float],
    species: Mapping[str, SpeciesThermoModel],
) -> NDArray[np.float64]:
    """Return ``U=[rho, rho*u, rho*E]`` using teacher variable thermochemistry.

    ``E = e(T,Y) + u^2/2`` uses absolute mixture internal energy. Consequently
    the conservative energy component is not required to be positive: species
    formation/zero-point enthalpy may make the absolute chemical-energy datum
    negative. Physical admissibility is enforced by source-valid temperature,
    positive density, finite velocity, and the thermochemical inversion itself.
    """

    fractions = normalized_mass_fractions(mass_fractions, species)
    lower, upper = common_temperature_bounds(fractions, species)
    density, velocity, temperature = _broadcast_primitive_inputs(rho, u, temperature_K)
    if np.any(temperature < lower) or np.any(temperature > upper):
        raise ValueError(
            f"temperature_K must remain inside active-species common range [{lower}, {upper}]"
        )

    internal_energy = np.empty_like(temperature, dtype=float)
    for index in np.ndindex(temperature.shape):
        internal_energy[index] = mixture_thermo_state(
            float(temperature[index]), fractions, species
        ).specific_internal_energy_J_per_kg

    total_energy = internal_energy + 0.5 * velocity**2
    return np.stack(
        (density, density * velocity, density * total_energy), axis=-1
    )


def variable_conservative_to_primitive(
    U: ArrayLike,
    mass_fractions: Mapping[str, float],
    species: Mapping[str, SpeciesThermoModel],
    *,
    temperature_tolerance_K: float = 1.0e-8,
    max_iterations: int = 200,
) -> VariableThermoPrimitiveVariables:
    """Recover fixed-composition primitives from variable-thermo conservative state.

    Temperature is obtained by bounded inversion of ``e(T,Y)`` over the common
    source-valid interval of the active species. Pressure and sound speed are
    then computed from the recovered local ``R(Y)`` and ``gamma(T,Y)``.
    """

    conservative = np.asarray(U, dtype=float)
    if conservative.ndim == 0 or conservative.shape[-1] != 3:
        raise ValueError("U last dimension must have length 3")
    if not np.all(np.isfinite(conservative)):
        raise ValueError("U must be finite")
    rho = conservative[..., 0]
    if not np.all(rho > 0.0):
        raise ValueError("rho must be strictly positive")

    fractions = normalized_mass_fractions(mass_fractions, species)
    lower, upper = common_temperature_bounds(fractions, species)
    momentum = conservative[..., 1]
    rho_total_energy = conservative[..., 2]
    u = momentum / rho
    target_internal_energy = rho_total_energy / rho - 0.5 * u**2

    T = np.empty_like(rho, dtype=float)
    p = np.empty_like(rho, dtype=float)
    gamma = np.empty_like(rho, dtype=float)
    gas_constant = np.empty_like(rho, dtype=float)
    cp = np.empty_like(rho, dtype=float)
    h = np.empty_like(rho, dtype=float)

    for index in np.ndindex(rho.shape):
        recovered_temperature = _recover_temperature(
            float(target_internal_energy[index]),
            fractions,
            species,
            temperature_min_K=lower,
            temperature_max_K=upper,
            temperature_tolerance_K=temperature_tolerance_K,
            max_iterations=max_iterations,
        )
        thermo = mixture_thermo_state(recovered_temperature, fractions, species)
        T[index] = recovered_temperature
        gamma[index] = thermo.gamma
        gas_constant[index] = thermo.gas_constant_J_per_kg_K
        cp[index] = thermo.cp_J_per_kg_K
        h[index] = thermo.specific_enthalpy_J_per_kg
        p[index] = rho[index] * thermo.gas_constant_J_per_kg_K * recovered_temperature

    if not np.all(np.isfinite(p) & (p > 0.0)):
        raise ValueError("recovered pressure must be finite and strictly positive")
    sound_speed = np.sqrt(gamma * gas_constant * T)
    if not np.all(np.isfinite(sound_speed) & (sound_speed > 0.0)):
        raise ValueError("recovered sound speed must be finite and strictly positive")
    Mach = u / sound_speed

    return VariableThermoPrimitiveVariables(
        rho=np.asarray(rho, dtype=float),
        u=np.asarray(u, dtype=float),
        p=p,
        T=T,
        Mach=Mach,
        gamma=gamma,
        R=gas_constant,
        cp=cp,
        h=h,
    )
