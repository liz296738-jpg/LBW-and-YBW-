"""Teacher-compatible variable-composition inlet/outlet boundary adapters.

The teacher-reference alignment freezes prescribed inlet static ``p/T/u`` and
first-order/zero-gradient outlet semantics.  For the current scramjet
compatibility path the prescribed inlet is required to be a rightward
supersonic air state, so all inlet characteristics enter the domain and the
left boundary flux is the physical Euler flux of that prescribed state.  The
outlet uses the physical flux of the last interior cell, equivalent to a
first-order zero-gradient extrapolation for the current flux assembly.

Internal interfaces continue to use the verified variable-composition Rusanov
compatibility flux.  Variable-property Steger-Warming remains a separate gate.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Mapping

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .geometry import AreaProfile
from .teacher_single_injector import TeacherSingleInjectorMapping
from .thermochemistry import SpeciesThermoModel, mixture_thermo_state
from .variable_composition import variable_composition_conservative_to_primitive
from .variable_composition_euler import (
    variable_composition_geometric_area_source,
    variable_composition_internal_rusanov_fluxes,
)
from .variable_euler import variable_area_weighted_flux_residual, variable_euler_flux
from .variable_state import variable_primitive_to_conservative


@dataclass(frozen=True)
class TeacherStaticInletState:
    """Prescribed teacher inlet static pressure, temperature and axial velocity."""

    pressure_Pa: float
    temperature_K: float
    axial_velocity_m_per_s: float

    def __post_init__(self) -> None:
        values = np.asarray(
            (self.pressure_Pa, self.temperature_K, self.axial_velocity_m_per_s),
            dtype=float,
        )
        if not np.all(np.isfinite(values)):
            raise ValueError("teacher inlet p, T and u must be finite")
        if self.pressure_Pa <= 0.0 or self.temperature_K <= 0.0:
            raise ValueError("teacher inlet static pressure and temperature must be strictly positive")
        if self.axial_velocity_m_per_s <= 0.0:
            raise ValueError("teacher inlet axial velocity must be strictly positive")


def teacher_static_inlet_conservative_state(
    inlet: TeacherStaticInletState,
    mapping: TeacherSingleInjectorMapping,
    species: Mapping[str, SpeciesThermoModel],
) -> NDArray[np.float64]:
    """Return the conservative air-only inlet state implied by prescribed p/T/u."""

    if not isinstance(inlet, TeacherStaticInletState):
        raise TypeError("inlet must be a TeacherStaticInletState")
    if not isinstance(mapping, TeacherSingleInjectorMapping):
        raise TypeError("mapping must be a TeacherSingleInjectorMapping")
    # P11.3J guarantees an air-only first physical cell. Keep that invariant
    # explicit here so a future mapping change cannot silently feed fuel at the inlet.
    if mapping.equivalence_ratio[0] != 0.0 or mapping.combustion_efficiency[0] != 0.0:
        raise ValueError("teacher inlet composition must remain air-only with phi=eta=0")
    composition = mapping.composition.composition_at(0)
    thermo = mixture_thermo_state(inlet.temperature_K, composition, species)
    gas_constant = float(thermo.gas_constant_J_per_kg_K)
    density = inlet.pressure_Pa / (gas_constant * inlet.temperature_K)
    U = variable_primitive_to_conservative(
        density,
        inlet.axial_velocity_m_per_s,
        inlet.temperature_K,
        composition,
        species,
    )
    primitive = variable_composition_conservative_to_primitive(
        np.asarray(U, dtype=float).reshape(1, 3),
        type(mapping.composition)(
            mapping.composition.species_names,
            mapping.composition.mass_fractions[:1],
        ),
        species,
    )
    if float(primitive.Mach[0]) <= 1.0:
        raise ValueError("current teacher static inlet adapter requires a rightward supersonic inlet Mach > 1")
    return np.asarray(U, dtype=float)


def teacher_boundary_interface_fluxes(
    U: ArrayLike,
    mapping: TeacherSingleInjectorMapping,
    inlet: TeacherStaticInletState,
    species: Mapping[str, SpeciesThermoModel],
) -> NDArray[np.float64]:
    """Return N+1 fluxes with fixed teacher inlet and extrapolated outlet."""

    if not isinstance(mapping, TeacherSingleInjectorMapping):
        raise TypeError("mapping must be a TeacherSingleInjectorMapping")
    states = np.asarray(U, dtype=float)
    n = mapping.composition.num_cells
    if states.shape != (n, 3):
        raise ValueError(f"U must have shape ({n}, 3)")
    if not np.all(np.isfinite(states)):
        raise ValueError("U must be finite")

    inlet_U = teacher_static_inlet_conservative_state(inlet, mapping, species)
    fluxes = np.empty((n + 1, 3), dtype=float)
    fluxes[0] = variable_euler_flux(
        inlet_U,
        mapping.composition.composition_at(0),
        species,
    )
    if n > 1:
        fluxes[1:-1] = variable_composition_internal_rusanov_fluxes(
            states, mapping.composition, species
        )
    fluxes[-1] = variable_euler_flux(
        states[-1],
        mapping.composition.composition_at(n - 1),
        species,
    )
    return fluxes


def teacher_boundary_quasi_1d_euler_rhs(
    U: ArrayLike,
    mapping: TeacherSingleInjectorMapping,
    geometry: AreaProfile,
    dx_m: object,
    inlet: TeacherStaticInletState,
    species: Mapping[str, SpeciesThermoModel],
) -> NDArray[np.float64]:
    """Return Euler/area RHS with teacher inlet and first-order outlet semantics."""

    if not isinstance(geometry, AreaProfile):
        raise TypeError("geometry must be an AreaProfile")
    if geometry.num_cells != mapping.composition.num_cells:
        raise ValueError("geometry.num_cells must match the teacher mapping")
    spacing = float(dx_m)
    if not isfinite(spacing) or spacing <= 0.0:
        raise ValueError("dx_m must be finite and strictly positive")
    if not np.allclose(
        np.diff(mapping.x_cell_m),
        spacing,
        rtol=2.0e-12,
        atol=2.0e-14 * max(1.0, spacing),
    ):
        raise ValueError("dx_m must match the grid spacing frozen in the teacher mapping")
    fluxes = teacher_boundary_interface_fluxes(U, mapping, inlet, species)
    return variable_area_weighted_flux_residual(
        fluxes, geometry, spacing
    ) + variable_composition_geometric_area_source(
        U, mapping.composition, geometry, spacing, species
    )
