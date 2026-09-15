"""Derive bounded P11.2B constraints from recovered Liu primary-source data.

This module deliberately separates exact same-row algebra from exploratory
model bridges. Its outputs are evidence-audit aids only: they do not promote a
formal Jin Fig. 14 case and do not change the production CFD solver.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = ROOT / "cases" / "studies" / "data" / "p11_2b_liu_primary_recovery.json"
DEFAULT_OUTPUT = ROOT / "artifacts" / "p11_2b" / "p11_2b_public_recovery.json"
EXPECTED_KIND = "public-primary-evidence-recovery"
EXPECTED_CANDIDATE = "JIN-LIU-MODEL-B-VALIDATION"


def load_source_record(path: Path = DEFAULT_SOURCE) -> dict:
    with path.open("r", encoding="utf-8") as stream:
        record = json.load(stream)
    if record.get("schema_version") != 1:
        raise ValueError("unsupported recovery schema")
    if record.get("record_kind") != EXPECTED_KIND:
        raise ValueError("unexpected recovery record_kind")
    if record.get("candidate_id") != EXPECTED_CANDIDATE:
        raise ValueError("unexpected recovery candidate_id")
    if record.get("formal_case_policy", {}).get("formal_case_ready") is not False:
        raise ValueError("recovery ledger must not silently promote a formal case")
    return record


def _positive(value: object, name: str) -> float:
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not math.isfinite(float(value))
        or float(value) <= 0.0
    ):
        raise ValueError(f"{name} must be finite and positive")
    return float(value)


def derive_public_recovery(record: dict) -> dict[str, object]:
    source = record["source_records"]
    geometry = source["geometry"]
    freestream = source["nominal_freestream"]
    properties = source["reacting_property_model"]
    row = source["table_2_model_B_C2H4_phi_1_03"]

    pt4 = _positive(row["exit_total_pressure_Pa"], "pt4")
    pt4_over_pt3 = _positive(
        row["exit_to_inlet_total_pressure_ratio"], "pt4_over_pt3"
    )
    pt3 = pt4 / pt4_over_pt3

    diameter = _positive(geometry["isolator_diameter_m"], "isolator_diameter_m")
    contraction = _positive(
        geometry["inlet_area_contraction_ratio"], "inlet_area_contraction_ratio"
    )
    rho_inf = _positive(freestream["density_kg_m3"], "freestream density")
    u_inf = _positive(freestream["velocity_m_s"], "freestream velocity")
    Tt_inf = _positive(
        freestream["stagnation_temperature_K"], "freestream stagnation temperature"
    )
    cp = _positive(properties["cp_J_kg_K"], "cp")
    enthalpy_ratio = _positive(
        row["exit_to_inlet_total_enthalpy_ratio"], "Ht4_over_Ht3"
    )
    if enthalpy_ratio <= 1.0:
        raise ValueError("reacting enthalpy ratio must exceed one for this recovery")

    isolator_area = math.pi * diameter**2 / 4.0
    nominal_capture_area = contraction * isolator_area
    nominal_full_capture_mass_flow = rho_inf * u_inf * nominal_capture_area

    # Exploratory bridge only. The source does not directly tabulate the exact
    # station-3 Tt or measured mass flow for Jin's Fig. 14 reconstruction.
    exploratory_Tt3 = Tt_inf
    exploratory_delta_ht = (enthalpy_ratio - 1.0) * cp * exploratory_Tt3
    exploratory_total_heat_power = (
        nominal_full_capture_mass_flow * exploratory_delta_ht
    )

    return {
        "schema_version": 1,
        "artifact_kind": "public-primary-evidence-recovery-summary",
        "candidate_id": EXPECTED_CANDIDATE,
        "source_id": record["primary_source"]["source_id"],
        "formal_case_ready": False,
        "exact_same_row_constraints": {
            "liu_model_B_phi": float(row["equivalence_ratio"]),
            "exit_Mach": float(row["exit_Mach"]),
            "pt4_Pa": pt4,
            "pt4_over_pt3": pt4_over_pt3,
            "derived_pt3_Pa": pt3,
            "Ht4_over_Ht3": enthalpy_ratio,
            "classification": "DERIVED_FROM_SAME_ROW_SOURCE_VALUES",
        },
        "source_analysis_boundary": {
            "liu_wall_friction_treatment": "neglected/negligible in Liu's own quasi-1D Eqs. (3) and (5)",
            "jin_fig14_Cf_inference_authorized": False,
            "reason": "A friction assumption in Liu's analysis does not establish the numerical Cf used by Jin in the separate Fig. 14 reconstruction.",
        },
        "exploratory_only": {
            "isolator_area_m2": isolator_area,
            "nominal_capture_area_m2": nominal_capture_area,
            "nominal_full_capture_mass_flow_kg_s": nominal_full_capture_mass_flow,
            "adiabatic_bridge_Tt3_K": exploratory_Tt3,
            "candidate_delta_ht_J_kg": exploratory_delta_ht,
            "candidate_total_heat_power_W": exploratory_total_heat_power,
            "formal_use_authorized": False,
            "assumptions": [
                "Tt3 equals nominal freestream stagnation temperature under an adiabatic no-work inlet/isolator bridge",
                "uniform nominal freestream is fully captured over the geometric inlet capture area with no spillage correction",
                "Liu's source-reported average cp is used for the enthalpy-ratio bridge",
            ],
        },
        "formal_blockers_unchanged": record["formal_case_policy"][
            "blockers_unchanged"
        ],
    }


def write_recovery_summary(summary: dict[str, object], output: Path = DEFAULT_OUTPUT) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return output


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    summary = derive_public_recovery(load_source_record(args.source))
    write_recovery_summary(summary, args.output)
    print(json.dumps(summary, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
