"""Conservative effective inlet for the NASA Burrows-Kurkov reduced domain."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = ROOT / "cases" / "studies" / "data" / "p11_2b_nasa_bk_reference_inlet_reduction.json"
EXPECTED_CANDIDATE_ID = "NASA-BURROWS-KURKOV-REACTING-VALIDATION"


@dataclass(frozen=True)
class EffectiveInletState:
    rho_kg_per_m3: float
    u_m_per_s: float
    p_Pa: float
    T_K: float
    Mach: float
    mass_flow_kg_s: float
    specific_total_enthalpy_J_per_kg: float


def load_reference_inlet(path: Path | str = SOURCE_PATH) -> dict[str, Any]:
    """Load the frozen record and independently recompute its moment match."""

    with Path(path).open("r", encoding="utf-8") as stream:
        record = json.load(stream)
    if record.get("schema_version") != 1:
        raise ValueError("unsupported NASA-BK reference-inlet schema")
    if record.get("candidate_id") != EXPECTED_CANDIDATE_ID:
        raise ValueError("NASA-BK reference-inlet candidate_id mismatch")
    if record.get("status") != "FROZEN_CONSERVATIVE_MOMENT_MATCHED_INLET":
        raise ValueError("NASA-BK reference inlet is not frozen")
    if record.get("source_class") != "NASA_REFERENCE_SOLUTION_DERIVED":
        raise ValueError("NASA-BK reference-inlet source class drifted")

    section = record["x0_reference_section"]
    gas = record["effective_gas_policy"]
    targets = record["matched_integral_targets"]
    state = record["effective_inlet_state"]

    width = float(section["duct_width_m"])
    area = float(section["source_backed_quasi_1d_area_m2"])
    mdot = width * float(section["mass_flux_per_width_kg_m_s"])
    momentum_flux = width * float(section["momentum_flux_per_width_N_per_m"])
    T_flux = float(section["thermal_T_flux_per_width_kgK_m_s"])
    mass_flux_per_width = float(section["mass_flux_per_width_kg_m_s"])
    kinetic_flux = float(section["kinetic_energy_flux_per_width_W_m"])
    cp = float(gas["cp_J_per_kg_K"])
    R = float(gas["R_J_per_kg_K"])
    gamma = float(gas["gamma"])
    T_mass = T_flux / mass_flux_per_width
    h0 = cp * T_mass + kinetic_flux / mass_flux_per_width

    if not math.isclose(mdot, float(targets["mass_flow_kg_s"]), rel_tol=0.0, abs_tol=1.0e-12):
        raise ValueError("NASA-BK reference inlet mass-flow target drifted")
    if not math.isclose(momentum_flux, float(targets["axial_momentum_flux_N"]), rel_tol=0.0, abs_tol=1.0e-10):
        raise ValueError("NASA-BK reference inlet momentum target drifted")
    if not math.isclose(h0, float(targets["effective_specific_total_enthalpy_J_per_kg"]), rel_tol=0.0, abs_tol=1.0e-8):
        raise ValueError("NASA-BK reference inlet h0 target drifted")

    mass_flux = mdot / area
    a2 = 0.5 - cp / R
    a1 = cp * (momentum_flux / area) / (mass_flux * R)
    a0 = -h0
    discriminant = a1 * a1 - 4.0 * a2 * a0
    if discriminant <= 0.0:
        raise ValueError("NASA-BK effective-inlet quadratic has no real branch")
    roots = (
        (-a1 + math.sqrt(discriminant)) / (2.0 * a2),
        (-a1 - math.sqrt(discriminant)) / (2.0 * a2),
    )
    candidates: list[EffectiveInletState] = []
    for u in roots:
        if u <= 0.0:
            continue
        p = momentum_flux / area - mass_flux * u
        if p <= 0.0:
            continue
        rho = mdot / (u * area)
        T = p / (rho * R)
        Mach = u / math.sqrt(gamma * R * T)
        candidates.append(EffectiveInletState(rho, u, p, T, Mach, mdot, h0))
    supersonic = [candidate for candidate in candidates if candidate.Mach > 1.0]
    if len(supersonic) != 1:
        raise ValueError("NASA-BK effective inlet must have exactly one positive supersonic branch")
    derived = supersonic[0]

    checks = {
        "rho_kg_per_m3": derived.rho_kg_per_m3,
        "u_m_per_s": derived.u_m_per_s,
        "p_Pa": derived.p_Pa,
        "T_K": derived.T_K,
        "Mach": derived.Mach,
        "mass_flow_kg_s": derived.mass_flow_kg_s,
        "specific_total_enthalpy_J_per_kg": derived.specific_total_enthalpy_J_per_kg,
    }
    tolerances = {
        "rho_kg_per_m3": 1.0e-12,
        "u_m_per_s": 1.0e-9,
        "p_Pa": 1.0e-7,
        "T_K": 1.0e-9,
        "Mach": 1.0e-12,
        "mass_flow_kg_s": 1.0e-12,
        "specific_total_enthalpy_J_per_kg": 1.0e-8,
    }
    for key, expected in checks.items():
        if not math.isclose(float(state[key]), expected, rel_tol=0.0, abs_tol=tolerances[key]):
            raise ValueError(f"NASA-BK effective inlet {key} drifted")
    if state.get("classification") != "NASA_REFERENCE_SOLUTION_DERIVED_CONSERVATIVE_MOMENT_MATCH":
        raise ValueError("NASA-BK effective inlet classification drifted")
    return record


def reference_effective_inlet(path: Path | str = SOURCE_PATH) -> EffectiveInletState:
    record = load_reference_inlet(path)
    state = record["effective_inlet_state"]
    return EffectiveInletState(
        rho_kg_per_m3=float(state["rho_kg_per_m3"]),
        u_m_per_s=float(state["u_m_per_s"]),
        p_Pa=float(state["p_Pa"]),
        T_K=float(state["T_K"]),
        Mach=float(state["Mach"]),
        mass_flow_kg_s=float(state["mass_flow_kg_s"]),
        specific_total_enthalpy_J_per_kg=float(state["specific_total_enthalpy_J_per_kg"]),
    )
