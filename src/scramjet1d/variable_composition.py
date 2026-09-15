"""Per-cell composition compatibility for the teacher variable-thermo model.

The teacher Chapter 11 formulation advances the three quasi-one-dimensional
conservative flow equations while closing local mixture composition
algebraically from equivalence ratio and combustion efficiency.  It does not
introduce a separate species-transport PDE system in the transcribed model.

This module is therefore a deliberately narrow bridge between the verified
teacher lean-composition closures and the already verified variable-
thermochemistry state conversion:

* build one source-backed mass-fraction vector per finite-volume cell;
* validate that every cell is a physical normalized mixture;
* convert primitive <-> conservative flow state using each cell's own
  composition.

No numerical flux, time integration, reaction source, fuel-injection source or
wall source is added here.  Those integrations remain separately gated.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .teacher_combustion import TeacherFuel, lean_reaction_mass_fractions
from .thermochemistry import SpeciesThermoModel, normalized_mass_fractions
from .variable_state import (
    VariableThermoPrimitiveVariables,
    common_temperature_bounds,
    variable_conservative_to_primitive,
    variable_primitive_to_conservative,
)


@dataclass(frozen=True)
class TeacherCompositionField:
    """Immutable cell-wise mass-fraction table.

    ``mass_fractions`` has shape ``(N, Ns)`` and each row corresponds to the
    species ordering in ``species_names``.  Rows must be finite, nonnegative and
    sum to one within ``1e-10``.  The array is copied and exposed read-only.
    """

    species_names: tuple[str, ...]
    mass_fractions: NDArray[np.float64]

    def __post_init__(self) -> None:
        names = tuple(str(name) for name in self.species_names)
        if not names or any(not name.strip() for name in names):
            raise ValueError("species_names must contain nonempty names")
        if len(set(names)) != len(names):
            raise ValueError("species_names must be unique")

        values = np.array(self.mass_fractions, dtype=float, copy=True)
        if values.ndim != 2 or values.shape[0] < 1:
            raise ValueError("mass_fractions must have shape (N, Ns) with N >= 1")
        if values.shape[1] != len(names):
            raise ValueError("mass_fractions species dimension must match species_names")
        if not np.all(np.isfinite(values)):
            raise ValueError("mass_fractions must be finite")
        if np.any(values < 0.0):
            raise ValueError("mass_fractions must be nonnegative")
        row_sums = np.sum(values, axis=1)
        if not np.all(np.abs(row_sums - 1.0) <= 1.0e-10):
            raise ValueError("each mass-fraction row must sum to one within 1e-10")

        values.setflags(write=False)
        object.__setattr__(self, "species_names", names)
        object.__setattr__(self, "mass_fractions", values)

    @property
    def num_cells(self) -> int:
        return int(self.mass_fractions.shape[0])

    @property
    def num_species(self) -> int:
        return int(self.mass_fractions.shape[1])

    def composition_at(self, cell_index: int) -> dict[str, float]:
        """Return one cell as a new ``{species: mass_fraction}`` mapping."""

        if isinstance(cell_index, bool) or not isinstance(cell_index, (int, np.integer)):
            raise TypeError("cell_index must be an integer")
        index = int(cell_index)
        if index < 0 or index >= self.num_cells:
            raise IndexError("cell_index is outside the composition field")
        return {
            name: float(self.mass_fractions[index, column])
            for column, name in enumerate(self.species_names)
        }


def _one_dimensional_profile(name: str, value: ArrayLike) -> NDArray[np.float64]:
    array = np.asarray(value, dtype=float)
    if array.ndim != 1 or array.size < 1:
        raise ValueError(f"{name} must be a nonempty one-dimensional cell profile")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must be finite")
    return array


def _broadcast_cell_value(name: str, value: ArrayLike, num_cells: int) -> NDArray[np.float64]:
    array = np.asarray(value, dtype=float)
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must be finite")
    try:
        broadcast = np.broadcast_to(array, (num_cells,))
    except ValueError as error:
        raise ValueError(f"{name} must be scalar or broadcast to ({num_cells},)") from error
    return np.asarray(broadcast, dtype=float)


def build_lean_teacher_composition_field(
    fuel: TeacherFuel,
    phi: ArrayLike,
    eta: ArrayLike,
    species: Mapping[str, SpeciesThermoModel],
) -> TeacherCompositionField:
    """Build a per-cell H2 or C2H4 lean-combustion mass-fraction field.

    ``phi`` and ``eta`` are one-dimensional cell profiles and must have the same
    shape after broadcasting.  Composition in each cell comes directly from
    teacher Eqs. (11.27) or (11.29) through
    :func:`lean_reaction_mass_fractions`.

    The pseudo-kerosene C10H22 equation is source-transcribed but intentionally
    excluded here until a source-backed C10H22 thermochemistry model is frozen.
    """

    if fuel not in ("H2", "C2H4"):
        raise ValueError(
            "per-cell thermochemical composition currently supports only H2 and C2H4; "
            "C10H22 thermochemistry remains source-gated"
        )
    phi_array = np.asarray(phi, dtype=float)
    eta_array = np.asarray(eta, dtype=float)
    try:
        phi_array, eta_array = np.broadcast_arrays(phi_array, eta_array)
    except ValueError as error:
        raise ValueError("phi and eta must broadcast together") from error
    if phi_array.ndim != 1 or phi_array.size < 1:
        raise ValueError("phi and eta must define nonempty one-dimensional cell profiles")
    if not np.all(np.isfinite(phi_array)) or not np.all(np.isfinite(eta_array)):
        raise ValueError("phi and eta must be finite")

    rows: list[dict[str, float]] = []
    for index in range(phi_array.size):
        row = lean_reaction_mass_fractions(
            fuel,
            float(phi_array[index]),
            float(eta_array[index]),
            species,
        )
        # Reuse the central thermochemistry validator so field construction and
        # state conversion share exactly the same normalization policy.
        rows.append(normalized_mass_fractions(row, species))

    names = tuple(rows[0].keys())
    if any(tuple(row.keys()) != names for row in rows[1:]):
        raise RuntimeError("teacher composition rows produced inconsistent species ordering")
    values = np.array(
        [[row[name] for name in names] for row in rows],
        dtype=float,
    )
    return TeacherCompositionField(species_names=names, mass_fractions=values)


def cell_temperature_bounds(
    field: TeacherCompositionField,
    species: Mapping[str, SpeciesThermoModel],
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Return source-valid thermo temperature bounds for every cell."""

    if not isinstance(field, TeacherCompositionField):
        raise TypeError("field must be a TeacherCompositionField")
    lower = np.empty(field.num_cells, dtype=float)
    upper = np.empty(field.num_cells, dtype=float)
    for index in range(field.num_cells):
        lower[index], upper[index] = common_temperature_bounds(
            field.composition_at(index), species
        )
    return lower, upper


def variable_composition_primitive_to_conservative(
    rho: ArrayLike,
    u: ArrayLike,
    temperature_K: ArrayLike,
    field: TeacherCompositionField,
    species: Mapping[str, SpeciesThermoModel],
) -> NDArray[np.float64]:
    """Convert cell primitives to ``U=[rho,rho*u,rho*E]`` using local composition."""

    if not isinstance(field, TeacherCompositionField):
        raise TypeError("field must be a TeacherCompositionField")
    density = _broadcast_cell_value("rho", rho, field.num_cells)
    velocity = _broadcast_cell_value("u", u, field.num_cells)
    temperature = _broadcast_cell_value("temperature_K", temperature_K, field.num_cells)

    result = np.empty((field.num_cells, 3), dtype=float)
    for index in range(field.num_cells):
        result[index] = variable_primitive_to_conservative(
            float(density[index]),
            float(velocity[index]),
            float(temperature[index]),
            field.composition_at(index),
            species,
        )
    return result


def variable_composition_conservative_to_primitive(
    U: ArrayLike,
    field: TeacherCompositionField,
    species: Mapping[str, SpeciesThermoModel],
    *,
    temperature_tolerance_K: float = 1.0e-8,
    max_iterations: int = 200,
) -> VariableThermoPrimitiveVariables:
    """Recover primitives from ``U`` using the corresponding composition row."""

    if not isinstance(field, TeacherCompositionField):
        raise TypeError("field must be a TeacherCompositionField")
    conservative = np.asarray(U, dtype=float)
    if conservative.ndim != 2 or conservative.shape != (field.num_cells, 3):
        raise ValueError(
            f"U must have shape ({field.num_cells}, 3) matching the composition field"
        )
    if not np.all(np.isfinite(conservative)):
        raise ValueError("U must be finite")

    rho = np.empty(field.num_cells, dtype=float)
    velocity = np.empty(field.num_cells, dtype=float)
    pressure = np.empty(field.num_cells, dtype=float)
    temperature = np.empty(field.num_cells, dtype=float)
    mach = np.empty(field.num_cells, dtype=float)
    gamma = np.empty(field.num_cells, dtype=float)
    gas_constant = np.empty(field.num_cells, dtype=float)
    cp = np.empty(field.num_cells, dtype=float)
    enthalpy = np.empty(field.num_cells, dtype=float)

    for index in range(field.num_cells):
        primitive = variable_conservative_to_primitive(
            conservative[index],
            field.composition_at(index),
            species,
            temperature_tolerance_K=temperature_tolerance_K,
            max_iterations=max_iterations,
        )
        rho[index] = float(primitive.rho)
        velocity[index] = float(primitive.u)
        pressure[index] = float(primitive.p)
        temperature[index] = float(primitive.T)
        mach[index] = float(primitive.Mach)
        gamma[index] = float(primitive.gamma)
        gas_constant[index] = float(primitive.R)
        cp[index] = float(primitive.cp)
        enthalpy[index] = float(primitive.h)

    return VariableThermoPrimitiveVariables(
        rho=rho,
        u=velocity,
        p=pressure,
        T=temperature,
        Mach=mach,
        gamma=gamma,
        R=gas_constant,
        cp=cp,
        h=enthalpy,
    )
