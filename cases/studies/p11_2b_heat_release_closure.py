"""P11.2B prescribed heat-release closure utilities.

This module implements only source-backed mathematical transformations needed
for a future reactive/heat-addition surrogate.  It deliberately does not choose
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
    if not {"SRC07", "SRC08"}.issubset(source_ids):
        raise ValueError("P11.2B source ledger must retain SRC07 and SRC08")
    return data


def quasi_gaussian_eq7_normalized(
    x: ArrayLike,
    q_peak: object,
    x_peak: object,
    x_core_end: object,
) -> NDArray[np.float64]:
    """Return Jin et al. (2026) Eq. 7 normalized quasi-Gaussian heat release.

    The implemented relation is

    ``Q*(x) = Q*_m exp(-(x-x_m)^2 / (x_c-x_m)^2)``.

    All position arguments must use the same length unit.  This helper does not
    assign a physical unit or an operating-condition value to ``x_m`` or
    ``x_c``.  It reproduces the published functional form only; a formal case
    must obtain those values from traceable evidence rather than guessing them.
    """
    coordinate = np.asarray(x, dtype=float)
    if coordinate.ndim != 1 or coordinate.size == 0 or not np.all(np.isfinite(coordinate)):
        raise ValueError("x must be a nonempty finite one-dimensional array")

    peak = np.asarray(q_peak, dtype=float)
    x_m = np.asarray(x_peak, dtype=float)
    x_c = np.asarray(x_core_end, dtype=float)
    for name, value in (("q_peak", peak), ("x_peak", x_m), ("x_core_end", x_c)):
        if value.ndim != 0 or not np.isfinite(value):
            raise ValueError(f"{name} must be a finite scalar")
    if peak < 0.0:
        raise ValueError("q_peak must be nonnegative")
    width = float(x_c - x_m)
    if width == 0.0:
        raise ValueError("x_core_end must differ from x_peak")

    exponent = -((coordinate - float(x_m)) ** 2) / (width**2)
    result = float(peak) * np.exp(exponent)
    result.setflags(write=False)
    return result


def scale_shape_to_total_power(
    shape: ArrayLike,
    dx: object,
    total_power: object,
) -> NDArray[np.float64]:
    """Scale a nonnegative cell-centred shape to line heat release [W/m].

    The finite-volume normalization is exact for the solver convention:
    ``sum(Qdot_prime_i * dx) == total_power``.  ``total_power`` [W] is an
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
