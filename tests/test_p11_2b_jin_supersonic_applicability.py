"""Tests for the explicit Jin et al. supersonic applicability diagnostic."""

import importlib.util
from pathlib import Path

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "cases" / "studies" / "p11_2b_heat_release_closure.py"
SPEC = importlib.util.spec_from_file_location("p11_2b_heat_release_closure_applicability", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_strictly_supersonic_profile_passes_exact_source_gate() -> None:
    result = MODULE.assess_jin_supersonic_applicability([2.3, 1.2, 1.05])

    assert result["all_supersonic"] is True
    assert result["minimum_mach"] == pytest.approx(1.05)
    assert result["maximum_mach"] == pytest.approx(2.3)
    assert result["sonic_margin"] == pytest.approx(0.05)
    assert result["scientific_gate"] == "min(M)>1"
    assert result["flow_separation_assumption"] == "NOT_ASSESSABLE_FROM_1D_MACH_PROFILE"
    assert result["shock_train_assumption"] == "NOT_ASSESSABLE_FROM_1D_MACH_PROFILE"


def test_sonic_or_subsonic_profile_fails_source_gate_without_artificial_margin() -> None:
    sonic = MODULE.assess_jin_supersonic_applicability([2.0, 1.0, 1.2])
    subsonic = MODULE.assess_jin_supersonic_applicability([2.0, 0.98, 1.2])

    assert sonic["all_supersonic"] is False
    assert sonic["sonic_margin"] == pytest.approx(0.0)
    assert subsonic["all_supersonic"] is False
    assert subsonic["sonic_margin"] == pytest.approx(-0.02)


@pytest.mark.parametrize(
    "mach",
    [
        [],
        [1.2, np.nan],
        [1.2, np.inf],
        [1.2, 0.0],
        [1.2, -0.5],
        [[1.2, 1.3]],
    ],
)
def test_invalid_mach_profiles_are_rejected(mach) -> None:
    with pytest.raises(ValueError):
        MODULE.assess_jin_supersonic_applicability(mach)
