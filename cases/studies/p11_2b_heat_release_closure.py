"""P11.2B prescribed heat-release closure utilities.

This module implements only source-backed mathematical transformations needed
for a future reactive/heat-addition surrogate. It deliberately does not choose
an absolute heat-release power or a formal shape parameter set: those remain
evidence-gated in ``p11_2b_heat_release_model_source.json``.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from numpy.typing import ArrayLike, NDArray


ROOT = Path(__file__).resolve().parents[2]
SOURCE_LEDGER = ROOT / "cases" / "studies" / "data" / "p11_2b_heat_release_model_source.json"


def load_heat_release_source_ledger(path: Path = SOURCE_LEDGER) -> dict:
    """Load and minimally validate the tracked P11.2B evidence ledger."""
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if data.get("schema_version") != 1:
        raise ValueError("unsupported P11.2B source-ledger schema_version")
    if data.get("case_family") != "P11.2B_HEAT_RELEASE_CLOSURE_SOURCE":
        raise ValueError("unexpected P11.2B source-ledger case_family")
    source_ids = {entry.get("source_id") for entry in data.get("sources", [])}
    required = {"SRC07", "SRC08", "SRC09", "SRC10"}
    if not required.issubset(source_ids):
        raise ValueError("P11.2B source ledger must retain SRC07 through SRC10")
    return data


def _validated_coordinate_and_peak(
    x: ArrayLike, q_peak: object
) -> tuple[NDArray[np.float64], float]:
    """Return a finite 1-D coordinate and nonnegative normalized peak."""
    coordinate = np.asarray(x, dtype=float)
    if coordinate.ndim != 1 or coordinate.size == 0 or not np.all(np.isfinite(coordinate)):
        raise ValueError("x must be a nonempty finite one-dimensional array")
    peak = np.asarray(q_peak, dtype=float)
    if peak.ndim != 0 or not np.isfinite(peak) or peak < 0.0:
        raise ValueError("q_peak must be a finite nonnegative scalar")
    return coordinate, float(peak)


def quasi_gaussian_eq7_normalized(
    x: ArrayLike,
    q_peak: object,
    x_peak: object,
    x_core_end: object,
) -> NDArray[np.float64]:
    """Return Jin et al. (2026) Eq. 7 normalized quasi-Gaussian heat release.

    ``Q*(x) = Q*_m exp(-(x-x_m)^2 / (x_c-x_m)^2)``.

    All position arguments must use the same length unit. This helper does not
    assign operating-condition values to the shape parameters; a formal case
    must obtain them from traceable evidence rather than guessing them.
    """
    coordinate, peak = _validated_coordinate_and_peak(x, q_peak)
    x_m = np.asarray(x_peak, dtype=float)
    x_c = np.asarray(x_core_end, dtype=float)
    for name, value in (("x_peak", x_m), ("x_core_end", x_c)):
        if value.ndim != 0 or not np.isfinite(value):
            raise ValueError(f"{name} must be a finite scalar")
    width = float(x_c - x_m)
    if width == 0.0:
        raise ValueError("x_core_end must differ from x_peak")

    exponent = -((coordinate - float(x_m)) ** 2) / (width**2)
    result = peak * np.exp(exponent)
    result.setflags(write=False)
    return result


def asymmetric_quasi_gaussian_eq8_normalized(
    x: ArrayLike,
    q_peak: object,
    x_initiation: object,
    x_peak: object,
    x_core_end: object,
    asymmetry_length: object,
) -> NDArray[np.float64]:
    """Return Jin et al. (2026) Eq. 8 normalized asymmetric heat release.

    For ``x > x_i`` the published relation is

    ``Q*(x) = Q*_m exp(-[((x-x_m)(x-x_i+k)) /
                         ((x_c-x_m)(x-x_i))]^2)``.

    ``x_i`` is the heat-release initiation coordinate. The model is therefore
    defined as zero at and upstream of ``x_i``. The position parameters and
    ``k`` must all use the same length unit. This helper implements the exact
    functional form only; it does not freeze case-specific values or units.
    """
    coordinate, peak = _validated_coordinate_and_peak(x, q_peak)
    parameters = {
        "x_initiation": np.asarray(x_initiation, dtype=float),
        "x_peak": np.asarray(x_peak, dtype=float),
        "x_core_end": np.asarray(x_core_end, dtype=float),
        "asymmetry_length": np.asarray(asymmetry_length, dtype=float),
    }
    for name, value in parameters.items():
        if value.ndim != 0 or not np.isfinite(value):
            raise ValueError(f"{name} must be a finite scalar")

    x_i = float(parameters["x_initiation"])
    x_m = float(parameters["x_peak"])
    x_c = float(parameters["x_core_end"])
    k = float(parameters["asymmetry_length"])
    if not x_i < x_m < x_c:
        raise ValueError("physical Eq. 8 ordering requires x_initiation < x_peak < x_core_end")
    if k < 0.0:
        raise ValueError("asymmetry_length must be nonnegative")

    result = np.zeros_like(coordinate, dtype=float)
    active = coordinate > x_i
    if np.any(active):
        x_active = coordinate[active]
        ratio = (
            (x_active - x_m) * (x_active - x_i + k)
            / ((x_c - x_m) * (x_active - x_i))
        )
        result[active] = peak * np.exp(-(ratio**2))
    result.setflags(write=False)
    return result


def scale_shape_to_total_power(
    shape: ArrayLike,
    dx: object,
    total_power: object,
) -> NDArray[np.float64]:
    """Scale a nonnegative cell-centred shape to line heat release [W/m].

    The finite-volume normalization is exact for the solver convention:
    ``sum(Qdot_prime_i * dx) == total_power``. ``total_power`` [W] is an
    externally supplied physical input; this helper does not infer it from fuel
    flow, LHV, efficiency, or equivalence ratio.
    """
    values = np.asarray(shape, dtype=float)
    if values.ndim != 1 or values.size == 0:
        raise ValueError("shape must be a nonempty one-dimensional array")
    if not np.all(np.isfinite(values) & (values >= 0.0)):
        raise ValueError("shape must be finite and nonnegative")

    spacing = np.asarray(dx, dtype=float)
    power = np.asarray(total_power, dtype=float)
    if spacing.ndim != 0 or not np.isfinite(spacing) or spacing <= 0.0:
        raise ValueError("dx must be a finite strictly positive scalar")
    if power.ndim != 0 or not np.isfinite(power) or power < 0.0:
        raise ValueError("total_power must be a finite nonnegative scalar")

    discrete_integral = float(np.sum(values) * float(spacing))
    if float(power) == 0.0:
        result = np.zeros_like(values, dtype=float)
    else:
        if discrete_integral <= 0.0:
            raise ValueError("a positive total_power requires a shape with positive integral")
        result = values * (float(power) / discrete_integral)
    result.setflags(write=False)
    return result


def cumulative_total_temperature_from_line_heat(
    heat_release_rate_per_length: ArrayLike,
    dx: object,
    mass_flow_rate: object,
    cp: object,
    inlet_total_temperature: object,
) -> NDArray[np.float64]:
    """Discretize the Jin et al. Eq. 11 total-temperature energy relation.

    For cell-centred ``Qdot_prime`` [W/m], the returned values are the total
    temperature after each successive cell:

    ``Tt_j = Tt0 + sum_{i<=j}(Qdot_prime_i dx)/(mdot cp)``.

    This is a diagnostic energy integral, not a replacement for the CFD solver.
    """
    line_heat = np.asarray(heat_release_rate_per_length, dtype=float)
    if line_heat.ndim != 1 or line_heat.size == 0:
        raise ValueError("heat_release_rate_per_length must be a nonempty 1-D array")
    if not np.all(np.isfinite(line_heat) & (line_heat >= 0.0)):
        raise ValueError("heat_release_rate_per_length must be finite and nonnegative")

    scalars = {
        "dx": np.asarray(dx, dtype=float),
        "mass_flow_rate": np.asarray(mass_flow_rate, dtype=float),
        "cp": np.asarray(cp, dtype=float),
        "inlet_total_temperature": np.asarray(inlet_total_temperature, dtype=float),
    }
    for name, value in scalars.items():
        if value.ndim != 0 or not np.isfinite(value):
            raise ValueError(f"{name} must be a finite scalar")
    if scalars["dx"] <= 0.0:
        raise ValueError("dx must be strictly positive")
    if scalars["mass_flow_rate"] <= 0.0:
        raise ValueError("mass_flow_rate must be strictly positive")
    if scalars["cp"] <= 0.0:
        raise ValueError("cp must be strictly positive")
    if scalars["inlet_total_temperature"] <= 0.0:
        raise ValueError("inlet_total_temperature must be strictly positive")

    delta_temperature = np.cumsum(line_heat * float(scalars["dx"])) / (
        float(scalars["mass_flow_rate"]) * float(scalars["cp"])
    )
    result = float(scalars["inlet_total_temperature"]) + delta_temperature
    result.setflags(write=False)
    return result


def total_power_from_enthalpy_ratio(
    mass_flow_rate: object,
    inlet_specific_total_enthalpy: object,
    outlet_to_inlet_enthalpy_ratio: object,
) -> float:
    """Convert a measured total-enthalpy ratio to heat power when scale is known.

    Energy conservation gives

    ``Qdot_total = mdot * h_t,in * (h_t,out / h_t,in - 1)``.

    The ratio alone is dimensionless evidence and is intentionally insufficient:
    both mass flow [kg/s] and inlet specific total enthalpy [J/kg] must be
    supplied independently. This is useful for a future Liu model-B chain where
    ``Ht4/Ht3`` is measured but the absolute station-3 scale remains gated.
    """
    mass_flow = np.asarray(mass_flow_rate, dtype=float)
    inlet_enthalpy = np.asarray(inlet_specific_total_enthalpy, dtype=float)
    ratio = np.asarray(outlet_to_inlet_enthalpy_ratio, dtype=float)
    for name, value in (
        ("mass_flow_rate", mass_flow),
        ("inlet_specific_total_enthalpy", inlet_enthalpy),
        ("outlet_to_inlet_enthalpy_ratio", ratio),
    ):
        if value.ndim != 0 or not np.isfinite(value):
            raise ValueError(f"{name} must be a finite scalar")
    if mass_flow <= 0.0:
        raise ValueError("mass_flow_rate must be strictly positive")
    if inlet_enthalpy <= 0.0:
        raise ValueError("inlet_specific_total_enthalpy must be strictly positive")
    if ratio < 1.0:
        raise ValueError("outlet_to_inlet_enthalpy_ratio must be >= 1 for a nonnegative heat-addition path")
    return float(mass_flow * inlet_enthalpy * (ratio - 1.0))


def total_enthalpy_ratio_from_line_heat(
    heat_release_rate_per_length: ArrayLike,
    dx: object,
    mass_flow_rate: object,
    inlet_specific_total_enthalpy: object,
) -> float:
    """Return ``h_t,out/h_t,in`` implied by a nonnegative line-heat profile.

    This is the inverse diagnostic of :func:`total_power_from_enthalpy_ratio`:

    ``h_t,out/h_t,in = 1 + integral(Qdot'(x) dx)/(mdot * h_t,in)``.

    It permits direct comparison with a measured dimensionless enthalpy ratio
    without pretending that the ratio itself supplies a missing mass flow or
    absolute inlet enthalpy.
    """
    line_heat = np.asarray(heat_release_rate_per_length, dtype=float)
    if line_heat.ndim != 1 or line_heat.size == 0:
        raise ValueError("heat_release_rate_per_length must be a nonempty 1-D array")
    if not np.all(np.isfinite(line_heat) & (line_heat >= 0.0)):
        raise ValueError("heat_release_rate_per_length must be finite and nonnegative")

    spacing = np.asarray(dx, dtype=float)
    mass_flow = np.asarray(mass_flow_rate, dtype=float)
    inlet_enthalpy = np.asarray(inlet_specific_total_enthalpy, dtype=float)
    for name, value in (
        ("dx", spacing),
        ("mass_flow_rate", mass_flow),
        ("inlet_specific_total_enthalpy", inlet_enthalpy),
    ):
        if value.ndim != 0 or not np.isfinite(value):
            raise ValueError(f"{name} must be a finite scalar")
    if spacing <= 0.0:
        raise ValueError("dx must be strictly positive")
    if mass_flow <= 0.0:
        raise ValueError("mass_flow_rate must be strictly positive")
    if inlet_enthalpy <= 0.0:
        raise ValueError("inlet_specific_total_enthalpy must be strictly positive")

    total_power = float(np.sum(line_heat) * float(spacing))
    return 1.0 + total_power / (float(mass_flow) * float(inlet_enthalpy))
