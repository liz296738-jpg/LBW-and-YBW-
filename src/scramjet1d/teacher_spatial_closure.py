"""Source-aligned spatial teacher mixing/combustion closure.

The transcribed Chapter 11 model closes composition algebraically in space:

* Eq. (11.23) sets the fuel/air equivalence ratio from fuel and incoming-air
  mass flow rates;
* Eq. (11.20) sets the complete-mixing length using local combustor height;
* Eq. (11.19) gives the raw mixing-efficiency correlation versus distance from
  one injection point;
* the teacher text approximates combustion efficiency by mixing efficiency;
* Eqs. (11.27)/(11.29) convert ``phi`` and physical combustion efficiency to
  H2/C2H4 mixture composition.

This module therefore builds a *static spatial closure field* for one prescribed
injection station.  It does not introduce species-transport PDEs or a dynamic
reaction update in pseudo-time.  Chemical energy remains represented through
composition-dependent absolute species energy; no reaction ``Qdot`` is added.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Mapping

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .teacher_combustion import (
    InjectionMode,
    TeacherFuel,
    equivalence_ratio,
    mixing_efficiency_raw,
    mixing_length,
)
from .teacher_efficiency import (
    combustion_efficiency_from_fuel_mass_rates,
    combustion_efficiency_from_raw_mixing,
)
from .thermochemistry import SpeciesThermoModel
from .variable_composition import (
    TeacherCompositionField,
    build_lean_teacher_composition_field,
)


@dataclass(frozen=True)
class TeacherSpatialClosure:
    """Frozen profiles produced by the Chapter 11 spatial closure."""

    fuel: TeacherFuel
    equivalence_ratio: NDArray[np.float64]
    mixing_length_m: NDArray[np.float64]
    raw_mixing_efficiency: NDArray[np.float64]
    combustion_efficiency: NDArray[np.float64]
    residual_fuel_mass_flow_rate_kg_per_s: NDArray[np.float64]
    composition: TeacherCompositionField

    def __post_init__(self) -> None:
        arrays = (
            self.equivalence_ratio,
            self.mixing_length_m,
            self.raw_mixing_efficiency,
            self.combustion_efficiency,
            self.residual_fuel_mass_flow_rate_kg_per_s,
        )
        lengths = {np.asarray(value).shape for value in arrays}
        if len(lengths) != 1 or next(iter(lengths)) != (self.composition.num_cells,):
            raise ValueError("all closure profiles must match the composition field")
        for value in arrays:
            if not np.all(np.isfinite(value)):
                raise ValueError("closure profiles must be finite")


def _positive_scalar(name: str, value: object) -> float:
    scalar = float(value)
    if not isfinite(scalar) or scalar <= 0.0:
        raise ValueError(f"{name} must be finite and strictly positive")
    return scalar


def _positive_profile(name: str, value: ArrayLike) -> NDArray[np.float64]:
    profile = np.asarray(value, dtype=float)
    if profile.ndim != 1 or profile.size < 1:
        raise ValueError(f"{name} must be a nonempty one-dimensional profile")
    if not np.all(np.isfinite(profile) & (profile > 0.0)):
        raise ValueError(f"{name} must be finite and strictly positive")
    return profile


def _nonnegative_profile(name: str, value: ArrayLike) -> NDArray[np.float64]:
    profile = np.asarray(value, dtype=float)
    if profile.ndim != 1 or profile.size < 1:
        raise ValueError(f"{name} must be a nonempty one-dimensional profile")
    if not np.all(np.isfinite(profile) & (profile >= 0.0)):
        raise ValueError(f"{name} must be finite and nonnegative")
    return profile


def build_teacher_lean_spatial_closure(
    *,
    fuel: TeacherFuel,
    injected_fuel_mass_flow_rate_kg_per_s: object,
    incoming_air_mass_flow_rate_kg_per_s: object,
    x_from_injector_m: ArrayLike,
    combustor_height_m: ArrayLike,
    C_m: object,
    injection_mode: InjectionMode,
    species: Mapping[str, SpeciesThermoModel],
    alpha: object | None = None,
    A: object | None = None,
) -> TeacherSpatialClosure:
    """Build the teacher lean-combustion spatial closure downstream of one injector.

    ``injected_fuel_mass_flow_rate_kg_per_s`` and
    ``incoming_air_mass_flow_rate_kg_per_s`` are scalar prescribed stream mass
    flows.  This is intentionally a single-injection-station model: no
    discretization of distributed ``d(mdot_f)/dx`` into a cumulative mass-flow
    profile is invented here.

    ``x_from_injector_m`` is the nonnegative distance of each calculation cell
    from that injection station.  ``combustor_height_m`` is the local section
    height ``b`` used by Eq. (11.20), so it may vary by cell.

    Current thermochemical coupling is limited to the source-transcribed lean
    branch ``phi <= 1`` for H2 or C2H4.  C10H22 remains thermochemistry-gated.
    """

    if fuel not in ("H2", "C2H4"):
        raise ValueError(
            "teacher spatial thermochemical closure currently supports only H2 and C2H4; "
            "C10H22 thermochemistry remains source-gated"
        )
    fuel_flow = _positive_scalar(
        "injected_fuel_mass_flow_rate_kg_per_s",
        injected_fuel_mass_flow_rate_kg_per_s,
    )
    air_flow = _positive_scalar(
        "incoming_air_mass_flow_rate_kg_per_s",
        incoming_air_mass_flow_rate_kg_per_s,
    )
    x = _nonnegative_profile("x_from_injector_m", x_from_injector_m)
    height = _positive_profile("combustor_height_m", combustor_height_m)
    try:
        x, height = np.broadcast_arrays(x, height)
    except ValueError as error:
        raise ValueError("x_from_injector_m and combustor_height_m must have matching profiles") from error
    if x.ndim != 1:
        raise ValueError("x_from_injector_m and combustor_height_m must be one-dimensional")

    phi_scalar = equivalence_ratio(fuel_flow, air_flow, fuel)
    if phi_scalar > 1.0:
        raise ValueError(
            "current teacher composition closure is lean-only and requires equivalence ratio phi <= 1"
        )
    phi = np.full(x.shape, phi_scalar, dtype=float)

    lengths = np.empty_like(x, dtype=float)
    raw_eta = np.empty_like(x, dtype=float)
    for index in range(x.size):
        lengths[index] = mixing_length(
            phi_scalar,
            float(height[index]),
            C_m,
        )
        raw_eta[index] = float(
            mixing_efficiency_raw(
                float(x[index]),
                float(lengths[index]),
                injection_mode,
                alpha=alpha,
                A=A,
            )
        )

    eta = combustion_efficiency_from_raw_mixing(raw_eta)
    residual = fuel_flow * (1.0 - eta)

    # Eq. (11.18) is used as an internal consistency identity for the explicit
    # project adapter.  It must reconstruct the same physical efficiency.
    eta_from_mass_rates = combustion_efficiency_from_fuel_mass_rates(
        np.full(x.shape, fuel_flow, dtype=float),
        residual,
    )
    if not np.allclose(eta_from_mass_rates, eta, rtol=0.0, atol=2.0e-15):
        raise RuntimeError("teacher Eq.11.18 efficiency identity failed")

    composition = build_lean_teacher_composition_field(
        fuel,
        phi,
        eta,
        species,
    )
    return TeacherSpatialClosure(
        fuel=fuel,
        equivalence_ratio=np.asarray(phi, dtype=float),
        mixing_length_m=np.asarray(lengths, dtype=float),
        raw_mixing_efficiency=np.asarray(raw_eta, dtype=float),
        combustion_efficiency=np.asarray(eta, dtype=float),
        residual_fuel_mass_flow_rate_kg_per_s=np.asarray(residual, dtype=float),
        composition=composition,
    )
