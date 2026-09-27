"""Guard the external-lineage claim boundary for teacher mixing closures."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "cases" / "studies" / "data" / "teacher_mixing_external_lineage.json"


def test_mixing_lineage_does_not_promote_project_parameter_values() -> None:
    record = json.loads(LEDGER.read_text(encoding="utf-8"))
    classification = record["evidence_classification"]

    assert classification["eq_11_20_functional_form"] == (
        "TEACHER_PRIMARY_EXTERNALLY_CORROBORATED_LINEAGE"
    )
    assert classification["C_m_25_60_range"].startswith(
        "TEACHER_PRIMARY_LATER_SECONDARY_CORROBORATED"
    )
    assert classification["baseline_C_m_30"] == (
        "PROJECT_SELECTED_WITHIN_TEACHER_SOURCE_RANGE"
    )

    forbidden = " ".join(record["prohibited_promotions"])
    assert "C_m=30" in forbidden
    assert "experimentally calibrated" in forbidden
    assert "directly verified from Pulsonetti" in forbidden


def test_pulsonetti_lineage_identifier_is_frozen() -> None:
    record = json.loads(LEDGER.read_text(encoding="utf-8"))
    pulsonetti = next(
        row for row in record["external_lineage"] if "Pulsonetti" in row["source"]
    )
    assert pulsonetti["year"] == 1991
    assert pulsonetti["journal"] == "Journal of Propulsion and Power"
    assert pulsonetti["doi"] == "10.2514/3.23427"
