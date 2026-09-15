"""Effective constant-gas reduction for the NASA Burrows-Kurkov candidate.

This module does not add variable-property thermodynamics to the production
solver. It derives a transparent reference-state R/cp/gamma from the NASA
vitiated inlet composition and public NASA7 species polynomials, and exposes
heated-range sensitivity values that must accompany a formal reduced-order
study.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = ROOT / "cases" / "studies" / "data" / "p11_2b_nasa_bk_thermo_reduction.json"
EXPECTED_CANDIDATE_ID = "NASA-BURROWS-KURKOV-REACTING-VALIDATION"


@dataclass(frozen=True)
class EffectiveGasState:
    temperature_K: float
    R_J_per_kg_K: float
    cp_J_per_kg_K: float
    cv_J_per_kg_K: float
    gamma: float


def _positive(name: str, value: object) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{name} must be numeric")
    scalar = float(value)
    if not math.isfinite(scalar) or scalar <= 0.0:
        raise ValueError(f"{name} must be finite and positive")
    return scalar


def nasa7_cp_over_R(coefficients: list[float], temperature_K: float) -> float:
    """Evaluate NASA7 cp/R using the first five polynomial coefficients."""

    if len(coefficients) != 5:
        raise ValueError("NASA7 cp/R requires exactly five coefficients")
    T = _positive("temperature_K", temperature_K)
    if not all(isinstance(value, (int, float)) and math.isfinite(float(value)) for value in coefficients):
        raise ValueError("NASA7 coefficients must be finite numeric values")
    a1, a2, a3, a4, a5 = map(float, coefficients)
    return a1 + a2 * T + a3 * T**2 + a4 * T**3 + a5 * T**4


def load_thermo_reduction(path: Path | str = SOURCE_PATH) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as stream:
        record = json.load(stream)
    if record.get("schema_version") != 1:
        raise ValueError("unsupported NASA-BK thermo-reduction schema")
    if record.get("record_kind") != "effective-gas-thermodynamic-reduction":
        raise ValueError("unexpected NASA-BK thermo record_kind")
    if record.get("candidate_id") != EXPECTED_CANDIDATE_ID:
        raise ValueError("unexpected NASA-BK thermo candidate_id")
    if record.get("status") != "FROZEN_REDUCED_ORDER_REFERENCE_STATE_POLICY":
        raise ValueError("NASA-BK thermo-reduction policy is not frozen")

    composition = record.get("composition_source")
    thermo = record.get("thermo_source")
    constants = record.get("constants")
    derived = record.get("derived_reference_state")
    policy = record.get("formal_case_policy")
    if not all(isinstance(item, dict) for item in (composition, thermo, constants, derived, policy)):
        raise ValueError("NASA-BK thermo-reduction record is incomplete")

    fractions = composition.get("mass_fractions")
    species = thermo.get("species")
    if not isinstance(fractions, dict) or not isinstance(species, dict):
        raise ValueError("NASA-BK thermo source composition/species are incomplete")
    if set(fractions) != {"O2", "H2O", "N2"} or set(species) != set(fractions):
        raise ValueError("NASA-BK thermo species set drifted")
    if not math.isclose(sum(float(value) for value in fractions.values()), 1.0, rel_tol=0.0, abs_tol=1.0e-12):
        raise ValueError("NASA-BK thermo mass fractions must sum to 1")

    T_ref = _positive("temperature_reference_K", composition.get("temperature_reference_K"))
    for name, entry in species.items():
        if not isinstance(entry, dict):
            raise ValueError(f"thermo species {name} must be a mapping")
        interval = entry.get("temperature_interval_K")
        coefficients = entry.get("cp_over_R_coefficients")
        if not isinstance(interval, list) or len(interval) != 2:
            raise ValueError(f"thermo species {name} interval is invalid")
        lo, hi = map(float, interval)
        if not lo <= T_ref <= hi:
            raise ValueError(f"reference temperature is outside {name} coefficient interval")
        if not isinstance(coefficients, list) or len(coefficients) != 5:
            raise ValueError(f"thermo species {name} coefficients are invalid")
        _positive(f"{name}.molecular_weight_kg_per_kmol", entry.get("molecular_weight_kg_per_kmol"))

    _positive("universal_gas_constant", constants.get("universal_gas_constant_J_per_kmol_K"))
    if derived.get("derivation_class") != "SOURCE_BACKED_THERMO_DERIVED_REDUCED_ORDER_CONSTANT_GAS":
        raise ValueError("NASA-BK thermo derivation class drifted")
    if policy.get("classification") != "MODEL_REDUCTION_WITH_SOURCE_BACKED_REFERENCE_PROPERTIES":
        raise ValueError("NASA-BK thermo formal-case classification drifted")
    return record


def mixture_state_at_temperature(
    temperature_K: float,
    path: Path | str = SOURCE_PATH,
) -> EffectiveGasState:
    """Evaluate fixed-inlet-composition ideal-gas mixture properties."""

    record = load_thermo_reduction(path)
    T = _positive("temperature_K", temperature_K)
    fractions = record["composition_source"]["mass_fractions"]
    species = record["thermo_source"]["species"]
    R_u = float(record["constants"]["universal_gas_constant_J_per_kmol_K"])

    R_mix = 0.0
    cp_mix = 0.0
    for name, mass_fraction_raw in fractions.items():
        mass_fraction = float(mass_fraction_raw)
        entry = species[name]
        lo, hi = map(float, entry["temperature_interval_K"])
        if not lo <= T <= hi:
            raise ValueError(f"temperature_K={T} is outside {name} NASA7 interval [{lo}, {hi}]")
        molecular_weight = float(entry["molecular_weight_kg_per_kmol"])
        R_i = R_u / molecular_weight
        cp_over_R = nasa7_cp_over_R(entry["cp_over_R_coefficients"], T)
        R_mix += mass_fraction * R_i
        cp_mix += mass_fraction * cp_over_R * R_i

    cv_mix = cp_mix - R_mix
    if cv_mix <= 0.0:
        raise ValueError("derived mixture cv must be positive")
    gamma = cp_mix / cv_mix
    return EffectiveGasState(T, R_mix, cp_mix, cv_mix, gamma)


def reference_effective_gas(path: Path | str = SOURCE_PATH) -> EffectiveGasState:
    record = load_thermo_reduction(path)
    return mixture_state_at_temperature(record["composition_source"]["temperature_reference_K"], path)


def validate_tracked_derivations(path: Path | str = SOURCE_PATH) -> dict[str, Any]:
    """Recompute every tracked reference/sensitivity value and reject drift."""

    record = load_thermo_reduction(path)
    reference = reference_effective_gas(path)
    tracked_reference = record["derived_reference_state"]
    checks = {
        "R_mix_J_per_kg_K": reference.R_J_per_kg_K,
        "cp_mix_J_per_kg_K": reference.cp_J_per_kg_K,
        "cv_mix_J_per_kg_K": reference.cv_J_per_kg_K,
        "gamma_eff": reference.gamma,
    }
    for key, expected in checks.items():
        actual = float(tracked_reference[key])
        if not math.isclose(actual, expected, rel_tol=0.0, abs_tol=1.0e-10):
            raise ValueError(f"tracked thermo value {key} drifted from the source-backed derivation")

    sensitivity = record.get("temperature_sensitivity_fixed_inlet_composition")
    if not isinstance(sensitivity, list) or len(sensitivity) < 2:
        raise ValueError("thermo sensitivity record is incomplete")
    recomputed = []
    for row in sensitivity:
        state = mixture_state_at_temperature(float(row["temperature_K"]), path)
        if not math.isclose(float(row["cp_mix_J_per_kg_K"]), state.cp_J_per_kg_K, rel_tol=0.0, abs_tol=1.0e-10):
            raise ValueError("tracked thermo sensitivity cp drifted")
        if not math.isclose(float(row["gamma"]), state.gamma, rel_tol=0.0, abs_tol=1.0e-12):
            raise ValueError("tracked thermo sensitivity gamma drifted")
        recomputed.append(
            {
                "temperature_K": state.temperature_K,
                "cp_mix_J_per_kg_K": state.cp_J_per_kg_K,
                "gamma": state.gamma,
            }
        )
    return {
        "reference": reference,
        "sensitivity": recomputed,
        "required_sensitivity": record["formal_case_policy"]["required_sensitivity"],
    }
