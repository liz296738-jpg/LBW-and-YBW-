import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "cases" / "studies" / "data" / "p12_project_defined_response_sweep_acceptance.json"


def _load() -> dict:
    return json.loads(RECORD.read_text(encoding="utf-8"))


def test_response_sweep_acceptance_preserves_claim_boundary() -> None:
    record = _load()
    assert record["not_a_source_reproduction"] is True
    assert record["mode_label_claim"] is False
    assert record["project_equivalence_ratios"] == [0.1, 0.2, 0.3]


def test_response_sweep_acceptance_records_two_converged_and_one_guarded_point() -> None:
    points = _load()["points"]
    assert [point["status"] for point in points] == [
        "CONVERGED",
        "CONVERGED",
        "FORWARD_FLOW_GUARD_TRIGGERED",
    ]
    for point in points[:2]:
        assert point["density_change"] <= 1.0e-4
        assert point["mass_inventory_relative_to_inlet"] <= 5.0e-3
        assert point["min_mach"] > 1.0
    assert points[2]["physical_mode_claim"] is None
