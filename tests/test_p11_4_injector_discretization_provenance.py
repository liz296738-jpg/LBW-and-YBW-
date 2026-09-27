"""Freeze the nominal-vs-discrete injector-location provenance."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from cases.studies import p11_4_project_defined_h2_smoke as baseline


ROOT = Path(__file__).resolve().parents[1]
PROVENANCE = (
    ROOT / "cases" / "studies" / "data" / "p11_4_project_defined_h2_input_provenance.json"
)


@pytest.mark.parametrize(
    ("cells", "expected_center"),
    [(20, 0.0700), (40, 0.0750), (80, 0.0775)],
)
def test_baseline_injector_uses_frozen_nearest_cell_realization(
    cells: int,
    expected_center: float,
) -> None:
    mapping = baseline.build_case(cells)[2]
    actual = float(mapping.x_cell_m[mapping.injector_cell])

    assert baseline.INJECTOR_X_M == pytest.approx(0.0800)
    assert actual == pytest.approx(expected_center, rel=0.0, abs=1.0e-15)


def test_input_provenance_records_nominal_vs_discrete_injector_location() -> None:
    record = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    injector = record["physical_inputs"]["INJECTOR_X_M"]
    discrete = injector["discrete_realization"]["by_grid_cells"]

    assert injector["value"] == 0.08
    assert discrete["20"]["actual_injector_cell_center_m"] == 0.07
    assert discrete["40"]["actual_injector_cell_center_m"] == 0.075
    assert discrete["80"]["actual_injector_cell_center_m"] == 0.0775
    assert injector["discrete_realization"]["physics_change"] is False
