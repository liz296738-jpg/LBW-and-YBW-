"""Teacher Chapter 11 Eq. (11.38) source-vector adapters.

The teacher governing equation is written for ``q = A*u_conservative`` as

``d(Au)/dt + d(Af)/dx = S``.

The existing quasi-one-dimensional operator already contains the geometric
``p*dA/dx`` term.  This module therefore supplies only the remaining Eq. (11.38)
terms after division by local cell area:

* injected mass ``(d mdot_s/dx)/A``;
* injected axial momentum ``u_sx (d mdot_s/dx)/A``;
* teacher wall friction ``-0.5 rho u^2 (4 f / D_e)``;
* wall heat ``rho u d(delta q)/dx`` when an explicit dimensional gradient is
  supplied;
* injected total enthalpy ``h_ts (d mdot_s/dx)/A``.

The empirical Eq. (11.26) wall-heat coefficient is **not** converted here to
``d(delta q)/dx`` because that dimensional adapter is not frozen by the current
source evidence.  Chemical reaction heat is also not added separately: the
teacher variable-composition path carries reaction energy through absolute
species energy.
"""

from __future__ import annotations

from math import isfinite
from typing import Mapping

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .geometry import AreaProfile
from .teacher_combustion import TeacherFuel
from .teacher_wall import (
    darcy_friction_factor_from_teacher_f,
    friction_coefficient_raw,
)
from .thermochemistry import SpeciesThermoModel
from .variable_composition import (
    TeacherCompositionField,
    variable_composition_conservative_to_primitive,
)


def _positive_scalar(name: str, value: object) -> float:
    scalar = float(value)
    if not isfinite(scalar) or scalar <= 0.0:
        raise ValueError(f"{name} must be finite and strictly positive")
    return scalar


def _finite_cell_profile(name: str, value: ArrayLike, num_cells: int) -> NDArray[np.float64]:
    array = np.asarray(value, dtype=float)
    try:
        profile = np.broadcast_to(array, (num_cells,))
    except ValueError as error:
        raise ValueError(f"{name} must be scalar or broadcast to ({num_cells},)") from error
    if not np.all(np.isfinite(profile)):
        raise ValueError(f"{name} must be finite")
    return np.asarray(profile, dtype=float)


def _nonnegative_cell_profile(
    name: str,
    value: ArrayLike,
    num_cells: int,
) -> NDArray[np.float64]:
    profile = _finite_cell_profile(name, value, num_cells)
    if np.any(profile < 0.0):
        raise ValueError(f"{name} must be nonnegative")
    return profile


def localized_injector_mass_flow_gradient(
    num_cells: int,
    injector_cell: int,
    injected_fuel_mass_flow_rate_kg_per_s: object,
    dx_m: object,
) -> NDArray[np.float64]:
    """Return finite-volume ``d(mdot_s)/dx`` for one localized injector cell.

    The teacher source describes the discrete addition as ``Delta mdot_s / Delta
    x``.  This adapter places the prescribed total mass-flow addition in exactly
    one finite-volume cell, so

    ``sum((dmdot/dx)_i * dx) == injected_fuel_mass_flow_rate``.

    No sub-cell injection-position model or distributed cumulative-flow rule is
    implied.
    """

    if isinstance(num_cells, bool) or not isinstance(num_cells, (int, np.integer)) or num_cells < 1:
        raise ValueError("num_cells must be a positive integer")
    if isinstance(injector_cell, bool) or not isinstance(injector_cell, (int, np.integer)):
        raise TypeError("injector_cell must be an integer")
    index = int(injector_cell)
    if index < 0 or index >= int(num_cells):
        raise IndexError("injector_cell is outside the finite-volume domain")
    fuel_flow = _positive_scalar(
        "injected_fuel_mass_flow_rate_kg_per_s",
        injected_fuel_mass_flow_rate_kg_per_s,
    )
    dx = _positive_scalar("dx_m", dx_m)
    gradient = np.zeros(int(num_cells), dtype=float)
    gradient[index] = fuel_flow / dx
    return gradient


def injected_fuel_specific_total_enthalpy(
    fuel: TeacherFuel,
    temperature_K: object,
    axial_velocity_m_per_s: object,
    species: Mapping[str, SpeciesThermoModel],
) -> float:
    """Return teacher ``h_ts`` [J/kg] for a pure H2/C2H4 injected stream.

    ``h_ts = h_s(T_s) + u_sx^2/2`` uses the same absolute source-backed species
    enthalpy convention as the variable-composition flow model.  Only axial
    injection kinetic energy is represented because Eq. (11.38) supplies the
    axial velocity component ``u_sx``.
    """

    if fuel not in ("H2", "C2H4"):
        raise ValueError(
            "injected-fuel total enthalpy currently supports only H2 and C2H4; "
            "C10H22 thermochemistry remains source-gated"
        )
    if fuel not in species:
        raise ValueError(f"species database does not contain {fuel}")
    temperature = _positive_scalar("temperature_K", temperature_K)
    velocity = float(axial_velocity_m_per_s)
    if not isfinite(velocity):
        raise ValueError("axial_velocity_m_per_s must be finite")
    sensible_and_chemical_enthalpy = float(species[fuel].h(temperature))
    return sensible_and_chemical_enthalpy + 0.5 * velocity**2


def teacher_eq_11_38_non_geometric_source(
    U: ArrayLike,
    field: TeacherCompositionField,
    geometry: AreaProfile,
    species: Mapping[str, SpeciesThermoModel],
    *,
    phi: ArrayLike,
    eta: ArrayLike,
    hydraulic_diameter_m: ArrayLike,
    fuel_mass_flow_gradient_kg_per_s_per_m: ArrayLike = 0.0,
    fuel_axial_velocity_m_per_s: ArrayLike = 0.0,
    fuel_specific_total_enthalpy_J_per_kg: ArrayLike = 0.0,
    wall_specific_heat_gain_gradient_J_per_kg_per_m: ArrayLike = 0.0,
) -> NDArray[np.float64]:
    """Return Eq. (11.38) non-geometric contribution to ``dU/dt``.

    The returned array has shape ``(N,3)`` and units matching the conservative
    flow RHS after the teacher source vector is divided by local area.

    ``wall_specific_heat_gain_gradient_J_per_kg_per_m`` is the *dimensional*
    ``d(delta q)/dx`` appearing in Eq. (11.38).  This function does not derive it
    from the empirical Eq. (11.26) coefficient.
    """

    if not isinstance(field, TeacherCompositionField):
        raise TypeError("field must be a TeacherCompositionField")
    if not isinstance(geometry, AreaProfile):
        raise TypeError("geometry must be an AreaProfile")
    if geometry.num_cells != field.num_cells:
        raise ValueError("geometry.num_cells must match the composition field cell count")
    states = np.asarray(U, dtype=float)
    if states.shape != (field.num_cells, 3):
        raise ValueError(f"U must have shape ({field.num_cells}, 3)")
    if not np.all(np.isfinite(states)):
        raise ValueError("U must be finite")

    primitive = variable_composition_conservative_to_primitive(states, field, species)
    if np.any(primitive.u < 0.0):
        raise ValueError(
            "teacher Eq.11.38 friction adapter currently supports forward axial flow u >= 0 only"
        )

    num_cells = field.num_cells
    phi_profile = _nonnegative_cell_profile("phi", phi, num_cells)
    eta_profile = _finite_cell_profile("eta", eta, num_cells)
    if np.any((eta_profile < 0.0) | (eta_profile > 1.0)):
        raise ValueError("eta must lie in [0, 1]")
    diameter = _finite_cell_profile("hydraulic_diameter_m", hydraulic_diameter_m, num_cells)
    if np.any(diameter <= 0.0):
        raise ValueError("hydraulic_diameter_m must be strictly positive")

    mass_gradient = _nonnegative_cell_profile(
        "fuel_mass_flow_gradient_kg_per_s_per_m",
        fuel_mass_flow_gradient_kg_per_s_per_m,
        num_cells,
    )
    injection_velocity = _finite_cell_profile(
        "fuel_axial_velocity_m_per_s",
        fuel_axial_velocity_m_per_s,
        num_cells,
    )
    injection_total_enthalpy = _finite_cell_profile(
        "fuel_specific_total_enthalpy_J_per_kg",
        fuel_specific_total_enthalpy_J_per_kg,
        num_cells,
    )
    wall_heat_gradient = _finite_cell_profile(
        "wall_specific_heat_gain_gradient_J_per_kg_per_m",
        wall_specific_heat_gain_gradient_J_per_kg_per_m,
        num_cells,
    )

    teacher_f = friction_coefficient_raw(phi_profile, eta_profile)
    darcy_factor = darcy_friction_factor_from_teacher_f(teacher_f)
    area = geometry.cell_area

    source = np.zeros_like(states, dtype=float)
    source[:, 0] = mass_gradient / area
    source[:, 1] = (
        -0.5 * darcy_factor * primitive.rho * primitive.u**2 / diameter
        + injection_velocity * mass_gradient / area
    )
    source[:, 2] = (
        primitive.rho * primitive.u * wall_heat_gradient
        + injection_total_enthalpy * mass_gradient / area
    )
    return source
