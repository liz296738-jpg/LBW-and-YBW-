"""Three-level verification study for the P11.4 project-defined H2 case.

This is solution-verification evidence for PROJECT_DEFINED_INTEGRATED_SMOKE_CASE,
not a source reproduction and not experimental validation.

The grid-refinement calculations follow docs/verification_methodology.md:
20/40/80 cells use r=2; every grid must satisfy the teacher Eq. 11.46 steady
gate; observed order is diagnostic only; conservative fine-grid GCI uses the
nominal first-order spatial accuracy and Fs=3; no automatic grid-independent or
asymptotic-range claim is made.
"""
from __future__ import annotations

from dataclasses import asdict
import json
import math

from cases.studies.p11_4_project_defined_h2_smoke import (
    DEFAULT_DENSITY_CHANGE_TOLERANCE,
    DEFAULT_MAX_STEPS,
    run_smoke,
)

GRID_LEVELS = (20, 40, 80)
TOLERANCE = DEFAULT_DENSITY_CHANGE_TOLERANCE
MAX_STEPS = DEFAULT_MAX_STEPS
REFINEMENT_RATIO = 2.0
NOMINAL_SPATIAL_ORDER = 1.0
CONSERVATIVE_GCI_SAFETY_FACTOR = 3.0


def relative_change(coarse: float, fine: float) -> float:
    scale = max(abs(fine), 1.0e-30)
    return abs(fine - coarse) / scale


def observed_order_diagnostic(
    coarse: float,
    medium: float,
    fine: float,
    *,
    refinement_ratio: float = REFINEMENT_RATIO,
) -> dict[str, object]:
    """Return the constant-r three-grid observed-order diagnostic."""

    values = (float(coarse), float(medium), float(fine))
    if not all(math.isfinite(value) for value in values):
        raise ValueError("grid-study quantities must be finite")
    r = float(refinement_ratio)
    if not math.isfinite(r) or r <= 1.0:
        raise ValueError("refinement_ratio must be finite and greater than one")

    delta_coarse_medium = medium - coarse
    delta_medium_fine = fine - medium

    if delta_coarse_medium == 0.0 and delta_medium_fine == 0.0:
        return {
            "behavior": "UNCHANGED_TO_REPORTED_PRECISION",
            "observed_order": None,
            "eligible_for_observed_order": False,
        }
    if delta_coarse_medium == 0.0 or delta_medium_fine == 0.0:
        return {
            "behavior": "DEGENERATE_DIFFERENCE",
            "observed_order": None,
            "eligible_for_observed_order": False,
        }
    if delta_coarse_medium * delta_medium_fine < 0.0:
        return {
            "behavior": "OSCILLATORY",
            "observed_order": None,
            "eligible_for_observed_order": False,
        }

    p = math.log(abs(delta_coarse_medium / delta_medium_fine)) / math.log(r)
    return {
        "behavior": "MONOTONIC",
        "observed_order": float(p),
        "eligible_for_observed_order": bool(math.isfinite(p) and p > 0.0),
    }


def conservative_fine_grid_gci(
    medium: float,
    fine: float,
    *,
    refinement_ratio: float = REFINEMENT_RATIO,
    nominal_order: float = NOMINAL_SPATIAL_ORDER,
    safety_factor: float = CONSERVATIVE_GCI_SAFETY_FACTOR,
) -> float:
    """Return conservative finest-grid GCI as a fraction, not percent."""

    medium = float(medium)
    fine = float(fine)
    r = float(refinement_ratio)
    p = float(nominal_order)
    fs = float(safety_factor)
    if not all(math.isfinite(value) for value in (medium, fine, r, p, fs)):
        raise ValueError("GCI inputs must be finite")
    if fine == 0.0:
        raise ValueError("fine-grid quantity must be non-zero")
    if r <= 1.0 or p <= 0.0 or fs <= 0.0:
        raise ValueError(
            "refinement ratio, nominal order, and safety factor must be positive"
        )
    return fs * abs((medium - fine) / fine) / (r**p - 1.0)


def quantity_verification(
    coarse: float,
    medium: float,
    fine: float,
) -> dict[str, object]:
    diagnostic = observed_order_diagnostic(coarse, medium, fine)
    gci = conservative_fine_grid_gci(medium, fine)
    return {
        **diagnostic,
        "nominal_spatial_order": NOMINAL_SPATIAL_ORDER,
        "gci_safety_factor": CONSERVATIVE_GCI_SAFETY_FACTOR,
        "conservative_fine_grid_gci_fraction": gci,
        "conservative_fine_grid_gci_percent": 100.0 * gci,
        "formal_asymptotic_grid_independence_claim": False,
    }


def run_grid_study() -> dict[str, object]:
    results = [
        run_smoke(n, tolerance=TOLERANCE, max_steps=MAX_STEPS)
        for n in GRID_LEVELS
    ]
    if not all(result.converged for result in results):
        raise RuntimeError("all three project-defined grid levels must converge")

    pairs = []
    for coarse, fine in zip(results[:-1], results[1:]):
        pairs.append(
            {
                "coarse_cells": coarse.cells,
                "fine_cells": fine.cells,
                "max_temperature_relative_change": relative_change(
                    coarse.max_temperature_K, fine.max_temperature_K
                ),
                "max_pressure_relative_change": relative_change(
                    coarse.max_pressure_Pa, fine.max_pressure_Pa
                ),
                "min_mach_relative_change": relative_change(
                    coarse.min_mach, fine.min_mach
                ),
                "max_mach_relative_change": relative_change(
                    coarse.max_mach, fine.max_mach
                ),
            }
        )

    coarse, medium, fine = results
    verification = {
        "max_temperature_K": quantity_verification(
            coarse.max_temperature_K,
            medium.max_temperature_K,
            fine.max_temperature_K,
        ),
        "max_pressure_Pa": quantity_verification(
            coarse.max_pressure_Pa,
            medium.max_pressure_Pa,
            fine.max_pressure_Pa,
        ),
        "min_mach": quantity_verification(
            coarse.min_mach,
            medium.min_mach,
            fine.min_mach,
        ),
        "max_mach": quantity_verification(
            coarse.max_mach,
            medium.max_mach,
            fine.max_mach,
        ),
    }

    return {
        "classification": "PROJECT_DEFINED_NUMERICAL_GRID_AUDIT",
        "not_a_source_reproduction": True,
        "not_experimental_validation": True,
        "tolerance": TOLERANCE,
        "grid_levels": list(GRID_LEVELS),
        "refinement_ratio": REFINEMENT_RATIO,
        "nominal_spatial_order": NOMINAL_SPATIAL_ORDER,
        "levels": [asdict(result) for result in results],
        "successive_grid_changes": pairs,
        "verification": verification,
        "interpretation": (
            "Observed orders are diagnostics only. Conservative fine-grid GCI "
            "estimates use nominal first-order spatial accuracy with Fs=3. "
            "No automatic asymptotic grid-independence claim is made."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run_grid_study(), indent=2, sort_keys=True))
