"""Conservative effective exit target for the NASA Burrows-Kurkov reduction."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from scramjet1d.config import GasProperties
from cases.studies.p11_2b_nasa_bk_reference_inlet import (
    EffectiveInletState,
    _solve_supersonic_moment_match,
)

ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = ROOT / "cases" / "studies" / "data" / "p11_2b_nasa_bk_reference_exit_reduction.json"
EXPECTED_CANDIDATE_ID = "NASA-BURROWS-KURKOV-REACTING-VALIDATION"


def load_reference_exit(path: Path | str = SOURCE_PATH) -> dict[str, Any]:
    """Load and independently validate the frozen conservative exit target."""

    with Path(path).open("r", encoding="utf-8") as stream:
        record = json.load(stream)
    if record.get("schema_version") != 1:
        raise ValueError("unsupported NASA-BK reference-exit schema")
    if record.get("candidate_id") != EXPECTED_CANDIDATE_ID:
        raise ValueError("NASA-BK reference-exit candidate_id mismatch")
    if record.get("status") != "FROZEN_CONSERVATIVE_MOMENT_MATCHED_EXIT_TARGET":
        raise ValueError("NASA-BK reference exit is not frozen")
    if record.get("source_class") != "NASA_REFERENCE_SOLUTION_DERIVED":
        raise ValueError("NASA-BK reference-exit source class drifted")

    targets = record["source_integral_targets"]
    gas_record = record["derivation"]["reference_effective_gas"]
    expected = record["derivation"]["reference_gamma_supersonic_state"]
    gas = GasProperties(
        gamma=float(gas_record["gamma"]),
        R=float(gas_record["R_J_per_kg_K"]),
    )
    derived = _solve_supersonic_moment_match(
        area_m2=float(targets["area_exit_m2"]),
        mass_flow_kg_s=float(targets["mass_flow_kg_s"]),
        axial_momentum_flux_N=float(targets["axial_momentum_flux_N"]),
        specific_total_enthalpy_J_per_kg=float(targets["specific_total_enthalpy_J_per_kg"]),
        gas=gas,
    )
    checks = {
        "rho_kg_per_m3": derived.rho_kg_per_m3,
        "u_m_per_s": derived.u_m_per_s,
        "p_Pa": derived.p_Pa,
        "T_K": derived.T_K,
        "Mach": derived.Mach,
    }
    tolerances = {
        "rho_kg_per_m3": 1.0e-12,
        "u_m_per_s": 1.0e-9,
        "p_Pa": 1.0e-7,
        "T_K": 1.0e-9,
        "Mach": 1.0e-12,
    }
    for key, value in checks.items():
        if not math.isclose(float(expected[key]), value, rel_tol=0.0, abs_tol=tolerances[key]):
            raise ValueError(f"NASA-BK effective exit {key} drifted")
    return record


def effective_exit_for_gas(
    gas: GasProperties,
    path: Path | str = SOURCE_PATH,
) -> EffectiveInletState:
    """Moment-match the frozen NASA exit integral targets for ``gas``."""

    if not isinstance(gas, GasProperties):
        raise TypeError("gas must be GasProperties")
    record = load_reference_exit(path)
    targets = record["source_integral_targets"]
    return _solve_supersonic_moment_match(
        area_m2=float(targets["area_exit_m2"]),
        mass_flow_kg_s=float(targets["mass_flow_kg_s"]),
        axial_momentum_flux_N=float(targets["axial_momentum_flux_N"]),
        specific_total_enthalpy_J_per_kg=float(targets["specific_total_enthalpy_J_per_kg"]),
        gas=gas,
    )
