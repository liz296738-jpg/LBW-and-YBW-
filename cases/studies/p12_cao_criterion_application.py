"""Apply Cao's source-defined thermal-throat criterion to accepted P12 evidence.

The underlying flow cases remain PROJECT_DEFINED.  Only the combustion-mode
criterion is source-defined.  A solver guard/nonconverged point is never promoted
to a physical mode label.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

from scramjet1d.cao_mode_criteria import ThermalThroatState, classify_thermal_throat

ROOT = Path(__file__).resolve().parents[2]
SWEEP_ACCEPTANCE = ROOT / "cases" / "studies" / "data" / "p12_project_defined_response_sweep_acceptance.json"

CASE_CLASSIFICATION = "P12_SOURCE_CRITERION_ON_PROJECT_DEFINED_SWEEP"
NOT_A_SOURCE_REPRODUCTION = True
# Numerical sensitivity set only. Cao's source boundary is exactly Ma=1 and does
# not prescribe any floating-point tolerance.
PROJECT_SONIC_TOLERANCES = (1.0e-6, 1.0e-4, 1.0e-3, 1.0e-2)


@dataclass(frozen=True)
class CriterionApplicationPoint:
    equivalence_ratio: float
    solver_status: str
    minimum_mach: float | None
    sonic_margin: float | None
    criterion_state: str | None
    tolerance_stable: bool | None


def _load_sweep_acceptance() -> dict:
    return json.loads(SWEEP_ACCEPTANCE.read_text(encoding="utf-8"))


def classify_accepted_point(point: dict) -> CriterionApplicationPoint:
    """Classify one frozen response point without rerunning the CFD solver."""

    phi = float(point["equivalence_ratio"])
    solver_status = str(point["status"])
    if solver_status != "CONVERGED":
        return CriterionApplicationPoint(
            equivalence_ratio=phi,
            solver_status=solver_status,
            minimum_mach=None,
            sonic_margin=None,
            criterion_state=None,
            tolerance_stable=None,
        )

    minimum_mach = float(point["min_mach"])
    states = {
        classify_thermal_throat(
            [minimum_mach], sonic_tolerance=tolerance
        ).state
        for tolerance in PROJECT_SONIC_TOLERANCES
    }
    stable = len(states) == 1
    state = next(iter(states)).value if stable else "TOLERANCE_SENSITIVE"
    return CriterionApplicationPoint(
        equivalence_ratio=phi,
        solver_status=solver_status,
        minimum_mach=minimum_mach,
        sonic_margin=minimum_mach - 1.0,
        criterion_state=state,
        tolerance_stable=stable,
    )


def run_application() -> list[CriterionApplicationPoint]:
    record = _load_sweep_acceptance()
    if record.get("not_a_source_reproduction") is not True:
        raise ValueError("response-sweep acceptance must remain project-defined")
    return [classify_accepted_point(point) for point in record["points"]]


if __name__ == "__main__":
    payload = {
        "classification": CASE_CLASSIFICATION,
        "not_a_source_reproduction": NOT_A_SOURCE_REPRODUCTION,
        "source_criterion": "Cao Eq.(3-2): min(Ma(x)) relative to 1",
        "project_sonic_tolerances": PROJECT_SONIC_TOLERANCES,
        "points": [asdict(point) for point in run_application()],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
