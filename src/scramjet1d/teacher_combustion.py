"""Teacher Chapter 11 mixing and lean-combustion closure primitives.

This module transcribes the teacher-provided one-dimensional scramjet model
relations on textbook pages 256--258, Eqs. (11.19)--(11.24) and
(11.27)--(11.29).  The functions are deliberately isolated from the production
solver so the empirical closures can be verified before composition is allowed
to evolve inside the CFD time-marching path.

Scientific boundaries
---------------------
* :func:`mixing_efficiency_raw` returns the empirical Eq. (11.19) value exactly;
  it does **not** clip the value into ``[0, 1]``.  In particular, the normal-
  injection correlation may be slightly greater than one near ``x/L_m = 1``.
* The textbook composition relations on pp. 257--258 are stated for
  ``phi <= 1``.  :func:`lean_reaction_mole_amounts` therefore rejects rich
  mixtures rather than inventing a rich-combustion branch.
* Combustion efficiency ``eta`` is an explicit input and must already lie in
  ``[0, 1]``.  The future solver adapter must make an explicit, documented
  decision about how the raw mixing correlation is mapped to this physical
  reaction-efficiency interval.
* No reaction heat source is added here.  Future variable-composition coupling
  must account for chemical energy through species enthalpy without also adding
  the same energy through the independent prescribed ``Qdot'(x)`` path.

All lengths are SI metres; ratios and efficiencies are dimensionless.
"""

from __future__ import annotations

from math import exp, isfinite
from typing import Literal, Mapping

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .thermochemistry import SpeciesThermoModel


InjectionMode = Literal["parallel", "normal", "strut"]
TeacherFuel = Literal["H2", "C2H4", "C10H22"]

# Teacher source: p. 256 below Eq. (11.19).
NORMAL_INJECTION_ALPHA_RANGE = (0.17, 0.25)
STRUT_INJECTION_A_RANGE = (1.77, 3.4)
# Teacher source: p. 256 below Eq. (11.20).
MIXING_LENGTH_C_M_RANGE = (25.0, 60.0)

# Teacher source: pp. 257--258, Eqs. (11.27)--(11.29), dry-air basis per O2.
TEACHER_AIR_N2_PER_O2 = 3.7274
TEACHER_AIR_AR_PER_O2 = 0.04592

_FUEL_ATOMS: dict[TeacherFuel, tuple[int, int]] = {
    "H2": (0, 2),
    "C2H4": (2, 4),
    "C10H22": (10, 22),
}


def _finite_scalar(name: str, value: object) -> float:
    scalar = float(value)
    if not isfinite(scalar):
        raise ValueError(f"{name} must be finite")
    return scalar


def _positive_scalar(name: str, value: object) -> float:
    scalar = _finite_scalar(name, value)
    if scalar <= 0.0:
        raise ValueError(f"{name} must be strictly positive")
    return scalar


def _unit_interval(name: str, value: object) -> float:
    scalar = _finite_scalar(name, value)
    if scalar < 0.0 or scalar > 1.0:
        raise ValueError(f"{name} must lie in [0, 1]")
    return scalar


def _source_range(name: str, value: object, limits: tuple[float, float]) -> float:
    scalar = _finite_scalar(name, value)
    lower, upper = limits
    if scalar < lower or scalar > upper:
        raise ValueError(
            f"{name}={scalar:g} is outside the teacher-source range [{lower:g}, {upper:g}]"
        )
    return scalar


def _nonnegative_array(name: str, value: ArrayLike) -> NDArray[np.float64]:
    array = np.asarray(value, dtype=float)
    if not np.all(np.isfinite(array)) or np.any(array < 0.0):
        raise ValueError(f"{name} must be finite and nonnegative")
    return array


def mixing_length(
    phi0: object,
    combustor_height_m: object,
    C_m: object,
) -> float:
    """Return teacher Eq. (11.20) complete-mixing length ``L_m`` [m].

    Parameters
    ----------
    phi0:
        Local equivalence ratio used by the empirical correlation.
    combustor_height_m:
        Combustor cross-section height ``b`` at the calculation station [m].
    C_m:
        Teacher mixing-length constant.  The source range is 25--60.

    The two source branches are

    ``L_m = 0.179 C_m exp(1.72 phi0) b`` for ``phi0 <= 1`` and
    ``L_m = 3.333 C_m exp(-1.204 phi0) b`` for ``phi0 > 1``.
    """

    phi = _finite_scalar("phi0", phi0)
    if phi < 0.0:
        raise ValueError("phi0 must be nonnegative")
    height = _positive_scalar("combustor_height_m", combustor_height_m)
    coefficient = _source_range("C_m", C_m, MIXING_LENGTH_C_M_RANGE)
    if phi <= 1.0:
        return 0.179 * coefficient * exp(1.72 * phi) * height
    return 3.333 * coefficient * exp(-1.204 * phi) * height


def mixing_efficiency_raw(
    x_from_injector_m: ArrayLike,
    mixing_length_m: object,
    mode: InjectionMode,
    *,
    alpha: object | None = None,
    A: object | None = None,
) -> NDArray[np.float64]:
    """Return the unmodified teacher Eq. (11.19) mixing correlation.

    ``x_from_injector_m`` is the distance from the injection point [m].  The
    returned value is the empirical correlation itself and is intentionally not
    saturated at one.

    Modes
    -----
    ``parallel``
        ``eta_m = x / L_m``.
    ``normal``
        ``eta_m = [x/L_m + 1/(50 + 1000 alpha)]**alpha`` with teacher-source
        ``alpha`` range 0.17--0.25.
    ``strut``
        ``eta_m = (1 - exp(-A x/L_m)) / (1 - exp(-A))`` with teacher-source
        ``A`` range 1.77--3.4.
    """

    x = _nonnegative_array("x_from_injector_m", x_from_injector_m)
    length = _positive_scalar("mixing_length_m", mixing_length_m)
    xi = x / length

    if mode == "parallel":
        if alpha is not None or A is not None:
            raise ValueError("parallel injection does not use alpha or A")
        return np.asarray(xi, dtype=float)

    if mode == "normal":
        if A is not None:
            raise ValueError("normal injection does not use A")
        if alpha is None:
            raise ValueError("normal injection requires alpha")
        exponent = _source_range("alpha", alpha, NORMAL_INJECTION_ALPHA_RANGE)
        offset = 1.0 / (50.0 + 1000.0 * exponent)
        return np.asarray((xi + offset) ** exponent, dtype=float)

    if mode == "strut":
        if alpha is not None:
            raise ValueError("strut injection does not use alpha")
        if A is None:
            raise ValueError("strut injection requires A")
        shape = _source_range("A", A, STRUT_INJECTION_A_RANGE)
        numerator = 1.0 - np.exp(-shape * xi)
        denominator = 1.0 - exp(-shape)
        return np.asarray(numerator / denominator, dtype=float)

    raise ValueError("mode must be 'parallel', 'normal', or 'strut'")


def stoichiometric_fuel_air_ratio(carbon_atoms: object, hydrogen_atoms: object) -> float:
    """Return teacher Eq. (11.22) stoichiometric fuel/air mass ratio ``f_st``.

    The textbook closed form is

    ``f_st = (36 x + 3 y) / [103 (4 x + y)]``

    for hydrocarbon formula ``C_x H_y``.  Hydrogen is represented by ``x=0,
    y=2`` exactly as used by Eq. (11.24).
    """

    if isinstance(carbon_atoms, bool) or isinstance(hydrogen_atoms, bool):
        raise ValueError("atom counts must be nonnegative integers")
    try:
        x = int(carbon_atoms)
        y = int(hydrogen_atoms)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("atom counts must be nonnegative integers") from error
    if float(x) != float(carbon_atoms) or float(y) != float(hydrogen_atoms):
        raise ValueError("atom counts must be nonnegative integers")
    if x < 0 or y < 0 or (x == 0 and y == 0):
        raise ValueError("atom counts must be nonnegative and not both zero")
    denominator = 103.0 * (4.0 * x + y)
    return (36.0 * x + 3.0 * y) / denominator


def fuel_stoichiometric_ratio(fuel: TeacherFuel) -> float:
    """Return Eq. (11.22)/(11.24) ``f_st`` for a teacher fuel branch."""

    try:
        x, y = _FUEL_ATOMS[fuel]
    except KeyError as error:
        raise ValueError("fuel must be 'H2', 'C2H4', or 'C10H22'") from error
    return stoichiometric_fuel_air_ratio(x, y)


def equivalence_ratio(
    fuel_mass_flow_rate_kg_per_s: object,
    air_mass_flow_rate_kg_per_s: object,
    fuel: TeacherFuel,
) -> float:
    """Return teacher Eq. (11.23) equivalence ratio ``phi``.

    ``phi = (m_f / m_air) / f_st``.
    """

    fuel_flow = _finite_scalar("fuel_mass_flow_rate_kg_per_s", fuel_mass_flow_rate_kg_per_s)
    if fuel_flow < 0.0:
        raise ValueError("fuel_mass_flow_rate_kg_per_s must be nonnegative")
    air_flow = _positive_scalar("air_mass_flow_rate_kg_per_s", air_mass_flow_rate_kg_per_s)
    return (fuel_flow / air_flow) / fuel_stoichiometric_ratio(fuel)


def lean_reaction_mole_amounts(
    fuel: TeacherFuel,
    phi: object,
    eta: object,
) -> dict[str, float]:
    """Return unnormalised species mole amounts from Eqs. (11.27)--(11.29).

    The source section explicitly treats ``phi <= 1``.  ``eta`` is combustion
    efficiency and must lie in ``[0, 1]``.  The returned dictionary uses the
    textbook air basis ``O2 + 3.7274 N2 + 0.04592 Ar`` multiplied by the fuel-
    specific stoichiometric oxygen coefficient.

    No thermodynamic property is evaluated here.  Consequently the ``C10H22``
    reaction equation can be transcribed and verified even while its CHEMKIN
    thermochemistry remains unavailable elsewhere in the project.
    """

    mixture_ratio = _unit_interval("phi", phi)
    efficiency = _unit_interval("eta", eta)
    try:
        x, y = _FUEL_ATOMS[fuel]
    except KeyError as error:
        raise ValueError("fuel must be 'H2', 'C2H4', or 'C10H22'") from error

    nu_o2 = x + 0.25 * y
    reacted_fuel = efficiency * mixture_ratio
    amounts: dict[str, float] = {
        fuel: (1.0 - efficiency) * mixture_ratio,
        "O2": nu_o2 * (1.0 - efficiency * mixture_ratio),
        "N2": nu_o2 * TEACHER_AIR_N2_PER_O2,
        "AR": nu_o2 * TEACHER_AIR_AR_PER_O2,
        "H2O": 0.5 * y * reacted_fuel,
        "CO2": x * reacted_fuel,
    }
    # Avoid negative signed zero/noise while preserving exact source algebra.
    return {name: 0.0 if amount == 0.0 else float(amount) for name, amount in amounts.items()}


def mole_fractions(mole_amounts: Mapping[str, object]) -> dict[str, float]:
    """Normalize nonnegative species mole amounts to mole fractions."""

    if not mole_amounts:
        raise ValueError("mole_amounts must not be empty")
    validated: dict[str, float] = {}
    for name, value in mole_amounts.items():
        if not str(name).strip():
            raise ValueError("species names must be nonempty")
        amount = _finite_scalar(f"mole amount for {name}", value)
        if amount < 0.0:
            raise ValueError(f"mole amount for {name} must be nonnegative")
        validated[str(name)] = amount
    total = sum(validated.values())
    if not isfinite(total) or total <= 0.0:
        raise ValueError("total mole amount must be finite and positive")
    return {name: amount / total for name, amount in validated.items()}


def mass_fractions_from_mole_amounts(
    mole_amounts: Mapping[str, object],
    species: Mapping[str, SpeciesThermoModel],
) -> dict[str, float]:
    """Convert mole amounts to mass fractions using supplied species molecular weights.

    Molecular weights are intentionally taken from the caller's source-backed
    species database rather than duplicated here.  A molecular-weight model is
    required for every species with a positive mole amount; zero-amount species
    may remain absent from the database and are returned with zero mass fraction.
    """

    fractions = mole_fractions(mole_amounts)
    masses: dict[str, float] = {}
    for name, mole_fraction in fractions.items():
        if mole_fraction == 0.0:
            masses[name] = 0.0
            continue
        if name not in species:
            raise ValueError(f"missing molecular-weight model for positive-amount species {name}")
        molecular_weight = float(species[name].molecular_weight_kg_per_kmol)
        if not isfinite(molecular_weight) or molecular_weight <= 0.0:
            raise ValueError(f"molecular weight for {name} must be finite and positive")
        masses[name] = mole_fraction * molecular_weight

    total_mass = sum(masses.values())
    if not isfinite(total_mass) or total_mass <= 0.0:
        raise ValueError("derived total mass must be finite and positive")
    return {name: mass / total_mass for name, mass in masses.items()}


def lean_reaction_mass_fractions(
    fuel: TeacherFuel,
    phi: object,
    eta: object,
    species: Mapping[str, SpeciesThermoModel],
) -> dict[str, float]:
    """Return Eqs. (11.27)--(11.29) product/reactant mass fractions.

    This is only a composition conversion.  It does not evolve a conservative
    CFD state and does not add reaction heat.
    """

    return mass_fractions_from_mole_amounts(
        lean_reaction_mole_amounts(fuel, phi, eta), species
    )
