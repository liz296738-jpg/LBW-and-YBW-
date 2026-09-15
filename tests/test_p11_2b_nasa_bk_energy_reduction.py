"""Regression tests for the NASA-BK reference-solution energy reduction."""

import numpy as np
import pytest
from numpy.testing import assert_allclose

from cases.studies.p11_2b_nasa_bk_energy_reduction import (
    cell_net_energy_rate_per_length,
    conservation_diagnostic,
    interpolate_delta_h0,
    load_energy_reduction,
)


def test_frozen_curve_has_expected_identity_and_endpoints() -> None:
    record = load_energy_reduction()
    provenance = record["provenance"]

    assert provenance["source_class"] == "NASA_REFERENCE_SOLUTION_DERIVED"
    assert provenance["status"] == "FROZEN_NON_CIRCULAR_REFERENCE_DERIVATION"
    assert record["x_m"].size == 121
    assert record["x_m"][0] == pytest.approx(0.0)
    assert record["x_m"][-1] == pytest.approx(0.356)
    assert record["delta_h0_J_per_kg"][0] == pytest.approx(0.0)
    assert record["delta_h0_J_per_kg"][-1] == pytest.approx(53952.0670978236)


def test_reference_curve_contains_both_cooling_and_heating_relative_to_inlet() -> None:
    record = load_energy_reduction()
    delta = record["delta_h0_J_per_kg"]

    assert np.min(delta) < -40_000.0
    assert np.max(delta) > 50_000.0


def test_cell_line_energy_is_signed_and_globally_conservative() -> None:
    faces = np.linspace(0.0, 0.356, 41)
    mass_flow = 2.0
    qline = cell_net_energy_rate_per_length(faces, mass_flow)
    diagnostic = conservation_diagnostic(faces, mass_flow)

    assert qline.shape == (40,)
    assert np.any(qline < 0.0)
    assert np.any(qline > 0.0)
    assert diagnostic["absolute_mismatch_W"] < 1.0e-9
    assert diagnostic["expected_net_power_W"] == pytest.approx(
        mass_flow * 53952.0670978236
    )


def test_mesh_refinement_preserves_total_net_power() -> None:
    mass_flow = 1.985
    totals = []
    for cells in (20, 40, 80, 160):
        faces = np.linspace(0.0, 0.356, cells + 1)
        qline = cell_net_energy_rate_per_length(faces, mass_flow)
        totals.append(float(np.sum(qline * np.diff(faces))))

    assert_allclose(totals, totals[0], rtol=0.0, atol=1.0e-9)


def test_interpolation_rejects_out_of_domain_requests() -> None:
    with pytest.raises(ValueError, match="outside"):
        interpolate_delta_h0(np.array([-1.0e-4, 0.1]))
    with pytest.raises(ValueError, match="outside"):
        interpolate_delta_h0(np.array([0.1, 0.3561]))


def test_invalid_mesh_or_mass_flow_is_rejected() -> None:
    with pytest.raises(ValueError):
        cell_net_energy_rate_per_length([0.0, 0.1, 0.05], 2.0)
    with pytest.raises(ValueError):
        cell_net_energy_rate_per_length([0.0, 0.1, 0.356], 0.0)
