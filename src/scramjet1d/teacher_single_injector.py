"""Single-injector domain mapping for the teacher Chapter 11 model.

This module freezes the spatial contract needed before coupling the verified
teacher composition closure to the verified Eq. (11.38) source vector:

* cells upstream of the injector are air-only;
* the injector cell receives the prescribed fuel mass/momentum/enthalpy source
  exactly once;
* the injector cell and downstream cells use the source-backed algebraic
  ``phi -> L_m -> eta_m -> eta -> Y_i`` closure;
* composition is a thermodynamic/algebraic closure and does not itself add
  conservative mass, momentum, or energy.

The purpose of this layer is to prevent the specific double-counting error of
feeding a fuel-containing inlet while also injecting the same fuel inside the
finite-volume domain.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Mapping

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .teacher_combustion import InjectionMode, TeacherFuel
from .teacher_sources import (
    injected_fuel_specific_total_enthalpy,
    localized_injector_mass_flow_gradient,
)
from .teacher_spatial_closure import TeacherSpatialClosure, build_teacher_lean_spatial_closure
from .thermochemistry import SpeciesThermoModel
from .variable_composition import (
    TeacherCompositionField,
    build_lean_teacher_composition_field,
)


@dataclass(frozen=True)
class TeacherSingleInjectorMapping:
    """Frozen full-domain mapping for one finite-volume fuel injector."""

    fuel: TeacherFuel
    injector_cell: int
    x_cell_m: NDArray[np.float64]
    equivalence_ratio: NDArray[np.float64]
    raw_mixing_efficiency: NDArray[np.float64]
    combustion_efficiency: NDArray[np.float64]
    residual_fuel_mass_flow_rate_kg_per_s: NDArray[np.float64]
    composition: TeacherCompositionField
    fuel_mass_flow_gradient_kg_per_s_per_m: NDArray[np.float64]
    fuel_axial_velocity_m_per_s: NDArray[np.float64]
    fuel_specific_total_enthalpy_J_per_kg: NDArray[np.float64]
    downstream_closure: TeacherSpatialClosure

    def __post_init__(self) -> None:
        n = self.composition.num_cells
        if self.injector_cell < 0 or self.injector_cell >= n:
            raise ValueError("injector_cell must lie inside the composition field")
        arrays = (
            self.x_cell_m,
            self.equivalence_ratio,
            self.raw_mixing_efficiency,
            self.combustion_efficiency,
            self.residual_fuel_mass_flow_rate_kg_per_s,
            self.fuel_mass_flow_gradient_kg_per_s_per_m,
            self.fuel_axial_velocity_m_per_s,
            self.fuel_specific_total_enthalpy_J_per_kg,
        )
        for value in arrays:
            array = np.asarray(value, dtype=float)
            if array.shape != (n,) or not np.all(np.isfinite(array)):
                raise ValueError("all full-domain mapping profiles must be finite and have shape (N,)")
        if self.downstream_closure.composition.num_cells != n - self.injector_cell:
            raise ValueError("downstream_closure length must start at injector_cell and end at the domain exit")


def _positive_scalar(name: str, value: object) -> float:
    scalar = float(value)
    if not isfinite(scalar) or scalar <= 0.0:
        raise ValueError(f"{name} must be finite and strictly positive")
    return scalar


def _cell_profile(name: str, value: ArrayLike, num_cells: int, *, positive: bool = False) -> NDArray[np.float64]:
    array = np.asarray(value, dtype=float)
    try:
        profile = np.broadcast_to(array, (num_cells,))
    except ValueError as error:
        raise ValueError(f"{name} must be scalar or broadcast to ({num_cells},)") from error
    if not np.all(np.isfinite(profile)):
        raise ValueError(f"{name} must be finite")
    if positive and np.any(profile <= 0.0):
        raise ValueError(f"{name} must be strictly positive")
    return np.asarray(profile, dtype=float)


def _immutable_profile(value: ArrayLike) -> NDArray[np.float64]:
    array = np.array(value, dtype=float, copy=True)
    array.setflags(write=False)
    return array


def build_teacher_single_injector_mapping(
    *,
    fuel: TeacherFuel,
    injected_fuel_mass_flow_rate_kg_per_s: object,
    incoming_air_mass_flow_rate_kg_per_s: object,
    x_cell_m: ArrayLike,
    dx_m: object,
    injector_cell: int,
    combustor_height_m: ArrayLike,
    C_m: object,
    injection_mode: InjectionMode,
    injected_fuel_temperature_K: object,
    injected_fuel_axial_velocity_m_per_s: object,
    species: Mapping[str, SpeciesThermoModel],
    alpha: object | None = None,
    A: object | None = None,
) -> TeacherSingleInjectorMapping:
    """Build a source-consistent full-domain single-injector mapping.

    The cell-centre grid must be uniformly spaced by ``dx_m`` because the
    current finite-volume compatibility solver uses one scalar spacing.  The
    injector is located at the centre of ``injector_cell``.  Upstream cells are
    assigned the exact ``phi=eta=0`` air-only composition from the same teacher
    species basis.  From the injector cell downstream, the existing verified
    spatial closure is evaluated with ``x_from_injector = x - x_injector``.

    The localized conservative source is nonzero only at the injector cell.
    The composition field is *not* another source term.
    """

    if fuel not in ("H2", "C2H4"):
        raise ValueError(
            "single-injector thermochemical mapping currently supports only H2 and C2H4; "
            "C10H22 thermochemistry remains source-gated"
        )
    x = np.asarray(x_cell_m, dtype=float)
    if x.ndim != 1 or x.size < 2 or not np.all(np.isfinite(x)):
        raise ValueError("x_cell_m must be a finite one-dimensional profile with at least two cells")
    if np.any(np.diff(x) <= 0.0):
        raise ValueError("x_cell_m must be strictly increasing")
    dx = _positive_scalar("dx_m", dx_m)
    if not np.allclose(np.diff(x), dx, rtol=2.0e-12, atol=2.0e-14 * max(1.0, dx)):
        raise ValueError("x_cell_m spacing must match the scalar dx_m used by the solver")
    if isinstance(injector_cell, bool) or not isinstance(injector_cell, (int, np.integer)):
        raise TypeError("injector_cell must be an integer")
    injector = int(injector_cell)
    if injector < 0 or injector >= x.size:
        raise IndexError("injector_cell is outside x_cell_m")

    fuel_flow = _positive_scalar(
        "injected_fuel_mass_flow_rate_kg_per_s", injected_fuel_mass_flow_rate_kg_per_s
    )
    air_flow = _positive_scalar(
        "incoming_air_mass_flow_rate_kg_per_s", incoming_air_mass_flow_rate_kg_per_s
    )
    height = _cell_profile("combustor_height_m", combustor_height_m, x.size, positive=True)
    injection_velocity = float(injected_fuel_axial_velocity_m_per_s)
    if not isfinite(injection_velocity):
        raise ValueError("injected_fuel_axial_velocity_m_per_s must be finite")

    downstream_x = x[injector:] - x[injector]
    downstream = build_teacher_lean_spatial_closure(
        fuel=fuel,
        injected_fuel_mass_flow_rate_kg_per_s=fuel_flow,
        incoming_air_mass_flow_rate_kg_per_s=air_flow,
        x_from_injector_m=downstream_x,
        combustor_height_m=height[injector:],
        C_m=C_m,
        injection_mode=injection_mode,
        species=species,
        alpha=alpha,
        A=A,
    )

    if injector > 0:
        upstream = build_lean_teacher_composition_field(
            fuel,
            np.zeros(injector, dtype=float),
            np.zeros(injector, dtype=float),
            species,
        )
        if upstream.species_names != downstream.composition.species_names:
            raise RuntimeError("upstream/downstream teacher composition species ordering differs")
        mass_fractions = np.vstack(
            (upstream.mass_fractions, downstream.composition.mass_fractions)
        )
    else:
        mass_fractions = np.array(downstream.composition.mass_fractions, copy=True)

    full_composition = TeacherCompositionField(
        downstream.composition.species_names,
        mass_fractions,
    )

    phi = np.zeros(x.size, dtype=float)
    raw_eta = np.zeros(x.size, dtype=float)
    eta = np.zeros(x.size, dtype=float)
    residual = np.zeros(x.size, dtype=float)
    phi[injector:] = downstream.equivalence_ratio
    raw_eta[injector:] = downstream.raw_mixing_efficiency
    eta[injector:] = downstream.combustion_efficiency
    residual[injector:] = downstream.residual_fuel_mass_flow_rate_kg_per_s

    mass_gradient = localized_injector_mass_flow_gradient(
        x.size,
        injector,
        fuel_flow,
        dx,
    )
    h_ts = injected_fuel_specific_total_enthalpy(
        fuel,
        injected_fuel_temperature_K,
        injection_velocity,
        species,
    )
    velocity_profile = np.zeros(x.size, dtype=float)
    enthalpy_profile = np.zeros(x.size, dtype=float)
    velocity_profile[injector] = injection_velocity
    enthalpy_profile[injector] = h_ts

    return TeacherSingleInjectorMapping(
        fuel=fuel,
        injector_cell=injector,
        x_cell_m=_immutable_profile(x),
        equivalence_ratio=_immutable_profile(phi),
        raw_mixing_efficiency=_immutable_profile(raw_eta),
        combustion_efficiency=_immutable_profile(eta),
        residual_fuel_mass_flow_rate_kg_per_s=_immutable_profile(residual),
        composition=full_composition,
        fuel_mass_flow_gradient_kg_per_s_per_m=_immutable_profile(mass_gradient),
        fuel_axial_velocity_m_per_s=_immutable_profile(velocity_profile),
        fuel_specific_total_enthalpy_J_per_kg=_immutable_profile(enthalpy_profile),
        downstream_closure=downstream,
    )
