"""Build a machine-readable P11.2B formal-case readiness record.

The formal-case gate remains authoritative for promotion. This module also
summarizes dedicated evidence records so the tracked readiness artifact does
not lag behind requirements already resolved elsewhere (geometry, coordinate
mapping, area-law interpretation, and coefficient conventions).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[2]
STUDY_DIR = ROOT / "cases" / "studies"
DATA_DIR = STUDY_DIR / "data"
if str(STUDY_DIR) not in sys.path:
    sys.path.insert(0, str(STUDY_DIR))

from p11_2b_case_gate import assess_ledger_formal_case_readiness


SOURCE_LEDGER = DATA_DIR / "p11_2b_heat_release_model_source.json"
CONDITION_RECORD = DATA_DIR / "p11_2b_jin_liu_condition_discrepancy.json"
GEOMETRY_RECORD = DATA_DIR / "p11_2b_liu_model_b_geometry_source.json"
ANGLE_RECORD = DATA_DIR / "p11_2b_liu_angle_convention_source.json"
APPLICABILITY_RECORD = DATA_DIR / "p11_2b_jin_validation_applicability.json"
FRICTION_RECORD = DATA_DIR / "p11_2b_jin_friction_convention_source.json"
DEFAULT_OUTPUT = ROOT / "artifacts" / "p11_2b" / "p11_2b_readiness.json"
CANDIDATE_ID = "JIN-LIU-MODEL-B-VALIDATION"


def _load_json_record(path: Path, *, expected_kind: str) -> dict:
    with path.open("r", encoding="utf-8") as stream:
        record = json.load(stream)
    if record.get("schema_version") != 1:
        raise ValueError(f"unsupported evidence schema in {path.name}")
    if record.get("record_kind") != expected_kind:
        raise ValueError(f"unexpected record_kind in {path.name}")
    if record.get("candidate_id") != CANDIDATE_ID:
        raise ValueError(f"unexpected candidate_id in {path.name}")
    return record


def _repo_relative(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT.resolve()))


def build_evidence_gate_summary(
    *,
    condition_record: Path = CONDITION_RECORD,
    geometry_record: Path = GEOMETRY_RECORD,
    angle_record: Path = ANGLE_RECORD,
    applicability_record: Path = APPLICABILITY_RECORD,
    friction_record: Path = FRICTION_RECORD,
    declared_project_status: object = None,
    formal_case_ready: bool = False,
) -> dict[str, object]:
    """Summarize resolved and open evidence requirements without guessing."""

    condition = _load_json_record(
        condition_record,
        expected_kind="cross-source-validation-condition-discrepancy",
    )
    geometry = _load_json_record(
        geometry_record,
        expected_kind="validation-geometry-corollary",
    )
    angle = _load_json_record(
        angle_record,
        expected_kind="validation-geometry-angle-convention",
    )
    applicability = _load_json_record(
        applicability_record,
        expected_kind="validation-model-applicability",
    )
    friction = _load_json_record(
        friction_record,
        expected_kind="validation-friction-convention",
    )

    resolved_requirements: list[dict[str, object]] = []
    open_requirements: list[dict[str, object]] = []

    coordinate = geometry.get("coordinate_records", {})
    model_b = geometry.get("model_B_corollary", {})
    if (
        model_b.get("axial_transition_status")
        == "FROZEN_BY_SOURCE_BACKED_GEOMETRIC_CLOSURE"
        and coordinate.get("absolute_offset_status")
        == "FROZEN_FROM_SRC10_AND_INDEPENDENTLY_CLOSED_BY_SRC12_DIMENSIONS"
    ):
        resolved_requirements.append(
            {
                "requirement": "axial_coordinate_mapping",
                "status": "RESOLVED_SOURCE_BACKED",
                "evidence_record": _repo_relative(geometry_record),
                "solver_transform": coordinate.get("solver_coordinate_transform"),
            }
        )
    else:
        open_requirements.append(
            {
                "requirement": "axial_coordinate_mapping",
                "status": "NOT_FROZEN",
                "evidence_record": _repo_relative(geometry_record),
            }
        )

    area_resolution = geometry.get("area_angle_resolution", {})
    angle_decision = angle.get("interpretation_decision", {})
    if (
        area_resolution.get("study_layer_area_profile_status") == "READY"
        and angle_decision.get("status") == "READY_FOR_STUDY_LAYER_AREA_PROFILE"
        and angle_decision.get("classification") == "SOURCE_CORROBORATED_INTERPRETATION"
        and angle_decision.get("primary_source_direct_definition") is False
    ):
        resolved_requirements.append(
            {
                "requirement": "study_layer_radial_area_law",
                "status": "RESOLVED_SOURCE_CORROBORATED_INTERPRETATION",
                "classification": angle_decision.get("classification"),
                "evidence_records": [
                    _repo_relative(geometry_record),
                    _repo_relative(angle_record),
                ],
                "wall_divergence_angle_deg": angle_decision.get(
                    "wall_divergence_angle_deg"
                ),
                "primary_source_directly_defines_half_angle": False,
                "revision_policy": (
                    "A higher-authority primary figure or author dataset must "
                    "override this interpretation if contradictory."
                ),
            }
        )
    else:
        open_requirements.append(
            {
                "requirement": "study_layer_radial_area_law",
                "status": "NOT_READY",
                "evidence_records": [
                    _repo_relative(geometry_record),
                    _repo_relative(angle_record),
                ],
            }
        )

    friction_mapping = friction.get("derived_mapping", {})
    if (
        friction_mapping.get("status") == "RESOLVED"
        and friction_mapping.get("result") == "f_D = 4 Cf"
        and friction_mapping.get("classification") == "DERIVED_CONVENTION_MAPPING"
    ):
        resolved_requirements.append(
            {
                "requirement": "Cf convention to repository Darcy friction factor",
                "status": "RESOLVED_DERIVED_FROM_SOURCE_DEFINITION",
                "classification": friction_mapping.get("classification"),
                "evidence_record": _repo_relative(friction_record),
                "mapping": friction_mapping.get("result"),
                "basis": (
                    "Jin Eqs. (9)-(10) use 4 Cf dx/D and explicitly cite "
                    "Shapiro [51]; Shapiro defines the duct friction coefficient "
                    "as wall shear divided by dynamic head. Equating that wall "
                    "force to the repository Darcy source yields f_D=4 Cf."
                ),
            }
        )
    else:
        open_requirements.append(
            {
                "requirement": "Cf convention to repository Darcy friction factor",
                "status": "NOT_FROZEN",
                "evidence_record": _repo_relative(friction_record),
            }
        )

    condition_status = condition.get("status")
    if condition_status == "RESOLVED":
        resolved_requirements.append(
            {
                "requirement": "validation_condition_identity",
                "status": "RESOLVED",
                "evidence_record": _repo_relative(condition_record),
            }
        )
    else:
        open_requirements.append(
            {
                "requirement": "validation_condition_identity",
                "status": condition_status,
                "evidence_record": _repo_relative(condition_record),
                "detail": (
                    "Jin reports model B at phi=1.04, while the Liu Table-2 "
                    "model-B row matching M4=2.27 is phi=1.03 and Liu's exact "
                    "phi=1.04 row is model A."
                ),
            }
        )

    unresolved_inputs = applicability.get("unresolved_reproduction_inputs", [])
    if not isinstance(unresolved_inputs, list):
        raise ValueError("unresolved_reproduction_inputs must be a list")
    for item in unresolved_inputs:
        if not isinstance(item, dict):
            raise ValueError("each unresolved reproduction input must be an object")
        status = item.get("status")
        if status in {None, "RESOLVED"}:
            continue
        requirement = str(item.get("item"))
        # Requirements closed by a later dedicated evidence record must not be
        # duplicated as open merely because an older coarse ledger once listed
        # them. The current applicability record no longer lists the friction
        # convention, but this guard keeps readiness deterministic under stale
        # external copies.
        if requirement == "Cf convention to repository Darcy friction factor" and any(
            resolved.get("requirement") == requirement
            for resolved in resolved_requirements
        ):
            continue
        open_requirements.append(
            {
                "requirement": requirement,
                "status": status,
                "evidence_record": _repo_relative(applicability_record),
                "reason": item.get("reason"),
            }
        )

    if not formal_case_ready:
        open_requirements.append(
            {
                "requirement": "heat_release_shape_and_absolute_energy_chain",
                "status": "NOT_PROMOTED_TO_FORMAL_CASE",
                "evidence_record": _repo_relative(SOURCE_LEDGER),
                "declared_project_status": declared_project_status,
                "detail": (
                    "No candidate_formal_cases entry currently supplies the full "
                    "same-condition heat-release shape plus absolute energy scale."
                ),
            }
        )

    return {
        "candidate_id": CANDIDATE_ID,
        "resolved_requirements": resolved_requirements,
        "open_requirements": open_requirements,
        "resolved_count": len(resolved_requirements),
        "open_count": len(open_requirements),
        "formal_promotion_unchanged": True,
    }


def build_readiness_record(source_ledger: Path = SOURCE_LEDGER) -> dict[str, object]:
    """Assess the tracked evidence ledger without inventing missing inputs."""
    with source_ledger.open("r", encoding="utf-8") as stream:
        ledger = json.load(stream)
    assessment = assess_ledger_formal_case_readiness(ledger)
    declared_status = ledger.get("project_decision", {}).get("formal_case_status")
    evidence_summary = build_evidence_gate_summary(
        declared_project_status=declared_status,
        formal_case_ready=bool(assessment.get("formal_case_ready")),
    )
    return {
        "schema_version": 1,
        "stage": "P11.2B",
        "artifact_kind": "formal-case-readiness",
        "source_ledger": str(source_ledger.relative_to(ROOT)),
        "declared_project_status": declared_status,
        "evidence_gate_summary": evidence_summary,
        **assessment,
    }


def write_readiness_record(record: dict[str, object], output: Path = DEFAULT_OUTPUT) -> Path:
    """Write canonical sorted JSON and return its path."""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(record, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return output


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-ledger", type=Path, default=SOURCE_LEDGER)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="return nonzero when no formal source-backed case is ready",
    )
    args = parser.parse_args(argv)

    record = build_readiness_record(args.source_ledger)
    write_readiness_record(record, args.output)
    print(json.dumps(record, indent=2, sort_keys=True, allow_nan=False))
    if args.require_ready and not record["formal_case_ready"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
