"""Guard delivery-manifest links to the maintained project paper."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "cases" / "studies" / "data" / "course_deliverable_manifest.json"


def test_deliverable_manifest_links_canonical_publication_files() -> None:
    record = json.loads(MANIFEST.read_text(encoding="utf-8"))
    publication = record["publication"]

    for key in ("canonical_paper", "evidence_map", "figure_generator"):
        assert (ROOT / publication[key]).is_file(), publication[key]

    assert "frozen repository evidence" in publication["policy"]
    assert record["course_project_status"] == "DELIVERABLE_COMPLETE"


def test_extension_gates_and_accepted_p13_are_separated() -> None:
    record = json.loads(MANIFEST.read_text(encoding="utf-8"))
    gates = " ".join(record["extension_gates"])

    assert "C10H22" in gates
    assert "separate future-model route" in gates
    assert "P13" not in gates

    acceptance_records = {
        row["acceptance_record"] for row in record["evidence"]
    }
    assert (
        "cases/studies/data/p13_teacher_mixing_constant_sensitivity_acceptance.json"
        in acceptance_records
    )
