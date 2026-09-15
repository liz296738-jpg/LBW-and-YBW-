"""Grid-convergence assessment for the NASA-BK reduced-order heated candidate."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from cases.studies.p11_2b_nasa_bk_heated_candidate import run_candidate
from cases.studies.p11_2b_nasa_bk_reference_exit import effective_exit_for_gas
from cases.studies.p11_2b_nasa_bk_thermo import reference_effective_gas
from scramjet1d.config import GasProperties


def run_grid_convergence(cell_counts: tuple[int, ...]) -> dict:
    """Run reference-gamma meshes and compare to the conservative exit target."""

    thermo = reference_effective_gas()
    gas = GasProperties(gamma=thermo.gamma, R=thermo.R_J_per_kg_K)
    target = effective_exit_for_gas(gas)
    records: list[dict[str, float | int | bool | str]] = []

    for cells in cell_counts:
        summary, _ = run_candidate(num_cells=cells)
        flow = summary["flow_scope"]
        solver = summary["solver"]
        record = {
            "cells": cells,
            "dx_m": 0.356 / cells,
            "converged": bool(solver["converged"]),
            "termination_reason": str(solver["termination_reason"]),
            "steps": int(solver["steps"]),
            "residual": float(solver["final_residual"]),
            "minimum_Mach": float(flow["minimum_Mach"]),
            "exit_Mach": float(flow["exit_Mach"]),
            "exit_pressure_Pa": float(flow["exit_pressure_Pa"]),
            "exit_temperature_K": float(flow["exit_temperature_K"]),
            "target_Mach": target.Mach,
            "target_pressure_Pa": target.p_Pa,
            "target_temperature_K": target.T_K,
            "Mach_relative_error": (float(flow["exit_Mach"]) - target.Mach) / target.Mach,
            "pressure_relative_error": (float(flow["exit_pressure_Pa"]) - target.p_Pa) / target.p_Pa,
            "temperature_relative_error": (float(flow["exit_temperature_K"]) - target.T_K) / target.T_K,
        }
        records.append(record)

    finest = records[-1]
    previous = records[-2] if len(records) > 1 else None
    if previous is None:
        refinement_change = None
    else:
        refinement_change = {
            "Mach_relative_change": abs(float(finest["exit_Mach"]) - float(previous["exit_Mach"])) / abs(float(finest["exit_Mach"])),
            "pressure_relative_change": abs(float(finest["exit_pressure_Pa"]) - float(previous["exit_pressure_Pa"])) / abs(float(finest["exit_pressure_Pa"])),
            "temperature_relative_change": abs(float(finest["exit_temperature_K"]) - float(previous["exit_temperature_K"])) / abs(float(finest["exit_temperature_K"])),
        }

    return {
        "schema_version": 1,
        "assessment_id": "P11.2B-NASA-BK-GRID-CONVERGENCE",
        "source_class": "NASA_REFERENCE_SOLUTION_DERIVED",
        "target_classification": "CONSERVATIVE_MOMENT_MATCHED_EXIT_TARGET",
        "cell_counts": list(cell_counts),
        "records": records,
        "finest_grid": finest,
        "finest_vs_previous": refinement_change,
        "claim_boundary": [
            "The target is a conservative one-dimensional moment match to the NASA Wind-US reference solution, not the experimental probe profile.",
            "This assessment tests discretization convergence and reduced-order closure consistency only.",
            "Experimental exit profiles remain independent context and are not used to construct the target or tune the solver."
        ],
    }


def write_outputs(output_dir: Path, result: dict) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "convergence.json").write_text(
        json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
    )
    records = result["records"]
    with (output_dir / "convergence.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--cells", type=int, nargs="+", default=[40, 80, 160, 320])
    args = parser.parse_args()
    counts = tuple(args.cells)
    if len(counts) < 2 or any(value < 20 for value in counts):
        raise SystemExit("provide at least two cell counts, each >= 20")
    if any(b <= a for a, b in zip(counts, counts[1:])):
        raise SystemExit("cell counts must be strictly increasing")
    result = run_grid_convergence(counts)
    write_outputs(args.output_dir, result)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
