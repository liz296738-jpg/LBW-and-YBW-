"""Regression checks for the non-corrective Cao Case 2 source-table audit."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from cases.studies.p11_4_cao_case2_consistency_audit import run_consistency_audit


ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT / "cases" / "studies" / "data" / "p11_4_cao_case2_consistency_audit.json"


def test_consistency_audit_matches_frozen_record() -> None:
    current = run_consistency_audit()
    frozen = json.loads(FROZEN.read_text(encoding="utf-8"))

    assert current["source_values_modified"] is False
    assert current["formal_reproduction_promoted"] is False
    assert current["reported"] == frozen["reported"]

    current_derived = current["derived_from_frozen_mixture_thermochemistry"]
    frozen_derived = frozen["derived_from_frozen_mixture_thermochemistry"]
    for key, expected in frozen_derived.items():
        assert current_derived[key] == pytest.approx(expected, rel=1.0e-12, abs=1.0e-12)

    current_reported_gamma = current["derived_using_reported_gamma_with_frozen_mixture_R"]
    frozen_reported_gamma = frozen["derived_using_reported_gamma_with_frozen_mixture_R"]
    for key, expected in frozen_reported_gamma.items():
        assert current_reported_gamma[key] == pytest.approx(
            expected, rel=1.0e-12, abs=1.0e-12
        )


def test_audit_reports_difference_without_inventing_acceptance_gate() -> None:
    frozen = json.loads(FROZEN.read_text(encoding="utf-8"))
    derived = frozen["derived_from_frozen_mixture_thermochemistry"]

    assert frozen["acceptance_threshold"] is None
    assert derived["pressure_relative_difference_vs_reported"] != 0.0
    assert derived["density_relative_difference_vs_reported"] != 0.0
    assert derived["velocity_relative_difference_vs_reported"] != 0.0
    assert "No parameter is tuned" in frozen["interpretation"]
