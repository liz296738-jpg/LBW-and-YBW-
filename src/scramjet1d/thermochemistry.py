"""Teacher-reference variable thermochemistry primitives.

This module implements the temperature/composition-dependent ideal-gas mixture
relations used by the teacher-provided Chapter 11 and corroborated by Cao
Ruifeng's one-dimensional scramjet model. It remains independent of the
production Euler state conversion until the source-backed coefficient database
and state-recovery path are independently verified.

Conventions
-----------
* ``W`` is molecular weight [kg/kmol].
* ``R_u`` is the universal gas constant [J/(kmol K)].
* mass fractions ``Y_i`` are dimensionless and sum to one.
* the six stored polynomial coefficients correspond to the Chapter 11 / CHEMKIN
  form used for ``cp`` and ``h``; the seventh NASA/CHEMKIN entropy coefficient is
  not required by the current teacher equations.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isclose, isfinite
from typing import Mapping


UNIVERSAL_GAS_CONSTANT_J_PER_KMOL_K = 8314.46261815324


@dataclass(frozen=True)
class SpeciesThermoPolynomial:
    """Six-coefficient CHEMKIN/NASA-style ``cp``/``h`` interval for one species.

    ``coefficients`` stores ``(a1, a2, a3, a4, a5, a6)``. Over the declared
    temperature interval,

    ``cp = R_u/W * (a1 + a2*T + a3*T^2 + a4*T^3 + a5*T^4)``

    and

    ``h = R_u/W * (a1*T + a2*T^2/2 + a3*T^3/3 + a4*T^4/4
                    + a5*T^5/5 + a6)``.
    """

    name: str
    molecular_weight_kg_per_kmol: float
    temperature_min_K: float
    temperature_max_K: float
    coefficients: tuple[float, float, float, float, float, float]

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("species name must be nonempty")
        if (
            not isfinite(self.molecular_weight_kg_per_kmol)
            or self.molecular_weight_kg_per_kmol <= 0.0
        ):
            raise ValueError("molecular_weight_kg_per_kmol must be finite and positive")
        if not isfinite(self.temperature_min_K) or self.temperature_min_K <= 0.0:
            raise ValueError("temperature_min_K must be finite and positive")
        if (
            not isfinite(self.temperature_max_K)
            or self.temperature_max_K <= self.temperature_min_K
        ):
            raise ValueError("temperature_max_K must exceed temperature_min_K")
        if len(self.coefficients) != 6 or not all(
            isfinite(value) for value in self.coefficients
        ):
            raise ValueError("coefficients must contain six finite values")

    def _temperature(self, temperature_K: float) -> float:
        T = float(temperature_K)
        if not isfinite(T):
            raise ValueError("temperature_K must be finite")
        if not self.temperature_min_K <= T <= self.temperature_max_K:
            raise ValueError(
                f"temperature_K={T} is outside {self.name} validity range "
                f"[{self.temperature_min_K}, {self.temperature_max_K}]"
            )
        return T

    def gas_constant(
        self,
        universal_gas_constant: float = UNIVERSAL_GAS_CONSTANT_J_PER_KMOL_K,
    ) -> float:
        """Return species specific gas constant [J/(kg K)]."""

        R_u = _positive("universal_gas_constant", universal_gas_constant)
        return R_u / self.molecular_weight_kg_per_kmol

    def cp(
        self,
        temperature_K: float,
        universal_gas_constant: float = UNIVERSAL_GAS_CONSTANT_J_PER_KMOL_K,
    ) -> float:
        """Return species constant-pressure specific heat [J/(kg K)]."""

        T = self._temperature(temperature_K)
        a1, a2, a3, a4, a5, _ = self.coefficients
        polynomial = a1 + a2 * T + a3 * T**2 + a4 * T**3 + a5 * T**4
        cp = self.gas_constant(universal_gas_constant) * polynomial
        if not isfinite(cp) or cp <= 0.0:
            raise ValueError(f"derived cp for {self.name} must be finite and positive")
        return cp

    def h(
        self,
        temperature_K: float,
        universal_gas_constant: float = UNIVERSAL_GAS_CONSTANT_J_PER_KMOL_K,
    ) -> float:
        """Return species absolute specific enthalpy [J/kg]."""

        T = self._temperature(temperature_K)
        a1, a2, a3, a4, a5, a6 = self.coefficients
        polynomial = (
            a1 * T
            + 0.5 * a2 * T**2
            + (a3 / 3.0) * T**3
            + 0.25 * a4 * T**4
            + 0.2 * a5 * T**5
            + a6
        )
        enthalpy = self.gas_constant(universal_gas_constant) * polynomial
        if not isfinite(enthalpy):
            raise ValueError(f"derived h for {self.name} must be finite")
        return enthalpy


@dataclass(frozen=True)
class PiecewiseSpeciesThermo:
    """Two-interval CHEMKIN/NASA thermo model with one explicit switch temperature.

    The classic CHEMKIN NASA7 records used by the teacher-lineage data provide a
    low- and high-temperature polynomial. Only the first six coefficients from
    each interval are needed for Chapter 11 ``cp`` and absolute ``h``. No
    extrapolation outside the two source intervals is permitted.
    """

    low: SpeciesThermoPolynomial
    high: SpeciesThermoPolynomial
    switch_temperature_K: float

    def __post_init__(self) -> None:
        if self.low.name != self.high.name:
            raise ValueError("piecewise thermo intervals must describe the same species")
        if not isclose(
            self.low.molecular_weight_kg_per_kmol,
            self.high.molecular_weight_kg_per_kmol,
            rel_tol=0.0,
            abs_tol=1.0e-12,
        ):
            raise ValueError("piecewise thermo intervals must use the same molecular weight")
        switch = _positive("switch_temperature_K", self.switch_temperature_K)
        if not isclose(self.low.temperature_max_K, switch, rel_tol=0.0, abs_tol=1.0e-12):
            raise ValueError("low interval must end at switch_temperature_K")
        if not isclose(self.high.temperature_min_K, switch, rel_tol=0.0, abs_tol=1.0e-12):
            raise ValueError("high interval must begin at switch_temperature_K")
        if self.high.temperature_max_K <= self.low.temperature_min_K:
            raise ValueError("piecewise thermo temperature range is invalid")

    @property
    def name(self) -> str:
        return self.low.name

    @property
    def molecular_weight_kg_per_kmol(self) -> float:
        return self.low.molecular_weight_kg_per_kmol

    @property
    def temperature_min_K(self) -> float:
        return self.low.temperature_min_K

    @property
    def temperature_max_K(self) -> float:
        return self.high.temperature_max_K

    def _interval(self, temperature_K: float) -> SpeciesThermoPolynomial:
        T = float(temperature_K)
        if not isfinite(T):
            raise ValueError("temperature_K must be finite")
        if not self.temperature_min_K <= T <= self.temperature_max_K:
            raise ValueError(
                f"temperature_K={T} is outside {self.name} validity range "
                f"[{self.temperature_min_K}, {self.temperature_max_K}]"
            )
        return self.low if T <= self.switch_temperature_K else self.high

    def gas_constant(
        self,
        universal_gas_constant: float = UNIVERSAL_GAS_CONSTANT_J_PER_KMOL_K,
    ) -> float:
        return self.low.gas_constant(universal_gas_constant)

    def cp(
        self,
        temperature_K: float,
        universal_gas_constant: float = UNIVERSAL_GAS_CONSTANT_J_PER_KMOL_K,
    ) -> float:
        return self._interval(temperature_K).cp(
            temperature_K, universal_gas_constant
        )

    def h(
        self,
        temperature_K: float,
        universal_gas_constant: float = UNIVERSAL_GAS_CONSTANT_J_PER_KMOL_K,
    ) -> float:
        return self._interval(temperature_K).h(
            temperature_K, universal_gas_constant
        )


SpeciesThermoModel = SpeciesThermoPolynomial | PiecewiseSpeciesThermo


@dataclass(frozen=True)
class MixtureThermoState:
    """Temperature/composition-dependent ideal-gas mixture state."""

    temperature_K: float
    molecular_weight_kg_per_kmol: float
    gas_constant_J_per_kg_K: float
    cp_J_per_kg_K: float
    cv_J_per_kg_K: float
    gamma: float
    specific_enthalpy_J_per_kg: float
    specific_internal_energy_J_per_kg: float


def _positive(name: str, value: object) -> float:
    scalar = float(value)
    if not isfinite(scalar) or scalar <= 0.0:
        raise ValueError(f"{name} must be finite and positive")
    return scalar


def normalized_mass_fractions(
    mass_fractions: Mapping[str, float],
    species: Mapping[str, SpeciesThermoModel],
    *,
    sum_tolerance: float = 1.0e-10,
) -> dict[str, float]:
    """Validate mass fractions without silently renormalizing them."""

    if not mass_fractions:
        raise ValueError("mass_fractions must not be empty")
    if not species:
        raise ValueError("species database must not be empty")
    unknown = set(mass_fractions) - set(species)
    if unknown:
        raise ValueError(f"mass_fractions contains unknown species: {sorted(unknown)}")

    fractions: dict[str, float] = {}
    for name, raw_value in mass_fractions.items():
        value = float(raw_value)
        if not isfinite(value) or value < 0.0:
            raise ValueError(f"mass fraction for {name} must be finite and nonnegative")
        fractions[name] = value

    total = sum(fractions.values())
    if abs(total - 1.0) > sum_tolerance:
        raise ValueError(
            f"mass fractions must sum to one within {sum_tolerance:g}; got {total:.16g}"
        )
    if not any(value > 0.0 for value in fractions.values()):
        raise ValueError("at least one mass fraction must be positive")
    return fractions


def mixture_molecular_weight(
    mass_fractions: Mapping[str, float],
    species: Mapping[str, SpeciesThermoModel],
) -> float:
    """Return mixture molecular weight [kg/kmol] from ``1/W=sum(Y_i/W_i)``."""

    fractions = normalized_mass_fractions(mass_fractions, species)
    inverse_weight = sum(
        value / species[name].molecular_weight_kg_per_kmol
        for name, value in fractions.items()
    )
    if not isfinite(inverse_weight) or inverse_weight <= 0.0:
        raise ValueError("derived reciprocal mixture molecular weight must be positive")
    return 1.0 / inverse_weight


def mixture_thermo_state(
    temperature_K: float,
    mass_fractions: Mapping[str, float],
    species: Mapping[str, SpeciesThermoModel],
    *,
    universal_gas_constant: float = UNIVERSAL_GAS_CONSTANT_J_PER_KMOL_K,
) -> MixtureThermoState:
    """Evaluate teacher-reference mixture ``R, cp, cv, gamma, h, e`` at ``T``."""

    T = _positive("temperature_K", temperature_K)
    R_u = _positive("universal_gas_constant", universal_gas_constant)
    fractions = normalized_mass_fractions(mass_fractions, species)

    W_mix = mixture_molecular_weight(fractions, species)
    R_mix = R_u / W_mix
    cp_mix = 0.0
    h_mix = 0.0
    for name, fraction in fractions.items():
        model = species[name]
        cp_mix += fraction * model.cp(T, R_u)
        h_mix += fraction * model.h(T, R_u)

    cv_mix = cp_mix - R_mix
    if not isfinite(cv_mix) or cv_mix <= 0.0:
        raise ValueError("derived mixture cv must be finite and positive")
    gamma = cp_mix / cv_mix
    if not isfinite(gamma) or gamma <= 1.0:
        raise ValueError("derived mixture gamma must be finite and greater than one")
    internal_energy = h_mix - R_mix * T
    if not isfinite(internal_energy):
        raise ValueError("derived mixture internal energy must be finite")

    return MixtureThermoState(
        temperature_K=T,
        molecular_weight_kg_per_kmol=W_mix,
        gas_constant_J_per_kg_K=R_mix,
        cp_J_per_kg_K=cp_mix,
        cv_J_per_kg_K=cv_mix,
        gamma=gamma,
        specific_enthalpy_J_per_kg=h_mix,
        specific_internal_energy_J_per_kg=internal_energy,
    )


def mixture_pressure(
    density_kg_per_m3: float,
    temperature_K: float,
    mass_fractions: Mapping[str, float],
    species: Mapping[str, SpeciesThermoModel],
    *,
    universal_gas_constant: float = UNIVERSAL_GAS_CONSTANT_J_PER_KMOL_K,
) -> float:
    """Return ideal-mixture pressure [Pa] using the teacher-reference Dalton form."""

    rho = _positive("density_kg_per_m3", density_kg_per_m3)
    state = mixture_thermo_state(
        temperature_K,
        mass_fractions,
        species,
        universal_gas_constant=universal_gas_constant,
    )
    return rho * state.gas_constant_J_per_kg_K * state.temperature_K


def temperature_from_specific_internal_energy(
    target_internal_energy_J_per_kg: float,
    mass_fractions: Mapping[str, float],
    species: Mapping[str, SpeciesThermoModel],
    *,
    temperature_min_K: float,
    temperature_max_K: float,
    universal_gas_constant: float = UNIVERSAL_GAS_CONSTANT_J_PER_KMOL_K,
    temperature_tolerance_K: float = 1.0e-9,
    max_iterations: int = 200,
) -> float:
    """Invert ``e(T,Y)`` by bounded bisection for future conservative-state use.

    The composition is fixed during the inversion. The caller must provide a
    bracket contained within every active species model validity interval. No
    extrapolation or clipping is performed.
    """

    target = float(target_internal_energy_J_per_kg)
    if not isfinite(target):
        raise ValueError("target_internal_energy_J_per_kg must be finite")
    lo = _positive("temperature_min_K", temperature_min_K)
    hi = _positive("temperature_max_K", temperature_max_K)
    if hi <= lo:
        raise ValueError("temperature_max_K must exceed temperature_min_K")
    tolerance = _positive("temperature_tolerance_K", temperature_tolerance_K)
    if (
        not isinstance(max_iterations, int)
        or isinstance(max_iterations, bool)
        or max_iterations < 1
    ):
        raise ValueError("max_iterations must be a positive integer")

    def energy(T: float) -> float:
        return mixture_thermo_state(
            T,
            mass_fractions,
            species,
            universal_gas_constant=universal_gas_constant,
        ).specific_internal_energy_J_per_kg

    e_lo = energy(lo)
    e_hi = energy(hi)
    if e_hi <= e_lo:
        raise ValueError("internal energy must increase across the supplied temperature bracket")
    if not e_lo <= target <= e_hi:
        raise ValueError("target internal energy is outside the supplied temperature bracket")

    for _ in range(max_iterations):
        mid = 0.5 * (lo + hi)
        e_mid = energy(mid)
        if hi - lo <= tolerance:
            return mid
        if e_mid < target:
            lo = mid
        else:
            hi = mid
    raise RuntimeError("temperature inversion did not converge within max_iterations")
