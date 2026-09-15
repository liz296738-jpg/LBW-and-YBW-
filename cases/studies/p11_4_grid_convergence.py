"""Three-level convergence study for the P11.4 project-defined H2 case.

This remains a numerical audit of PROJECT_DEFINED_INTEGRATED_SMOKE_CASE, not a
source reproduction.  The driver deliberately records only quantities already
exposed by the accepted integrated case; it does not introduce new physics.
"""
from __future__ import annotations

from dataclasses import asdict
import json

from cases.studies.p11_4_project_defined_h2_smoke import run_smoke

GRID_LEVELS = (20, 40, 80)
TOLERANCE = 2.0e-5
MAX_STEPS = 20_000


def relative_change(coarse: float, fine: float) -> float:
    scale = max(abs(fine), 1.0e-30)
    return abs(fine - coarse) / scale


def run_grid_study() -> dict[str, object]:
    results = [run_smoke(n, tolerance=TOLERANCE, max_steps=MAX_STEPS) for n in GRID_LEVELS]
    if not all(r.converged for r in results):
        raise RuntimeError("all three project-defined grid levels must converge")

    pairs = []
    for coarse, fine in zip(results[:-1], results[1:]):
        pairs.append(
            {
                "coarse_cells": coarse.cells,
                "fine_cells": fine.cells,
                "max_temperature_relative_change": relative_change(coarse.max_temperature_K, fine.max_temperature_K),
                "max_pressure_relative_change": relative_change(coarse.max_pressure_Pa, fine.max_pressure_Pa),
                "min_mach_relative_change": relative_change(coarse.min_mach, fine.min_mach),
                "max_mach_relative_change": relative_change(coarse.max_mach, fine.max_mach),
            }
        )

    return {
        "classification": "PROJECT_DEFINED_NUMERICAL_GRID_AUDIT",
        "not_a_source_reproduction": True,
        "tolerance": TOLERANCE,
        "levels": [asdict(r) for r in results],
        "successive_grid_changes": pairs,
    }


if __name__ == "__main__":
    print(json.dumps(run_grid_study(), indent=2, sort_keys=True))
