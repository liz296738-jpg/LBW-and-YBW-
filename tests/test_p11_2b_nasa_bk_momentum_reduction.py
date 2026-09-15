"""Regression tests for the NASA-BK reference axial-momentum reduction."""

import numpy as np
import pytest
from numpy.testing import assert_allclose

from cases.studies.p11_2b_nasa_bk_momentum_reduction import (
    cell_net_momentum_rate_per_length,
    conservation_diagnostic,
    interpolate_specific_momentum,
    load_momentum_reduction,
)


def test_frozen_momentum_curve_identity_and_endpoints() -> None:
    record = load_momentum_reduction()
    provenance = record["provenance"]

    assert provenance["source_class"] == "NASA_REFERENCE_SOLUTION_DERIVED"
    assert provenance["status"] == "FROZEN_NON_CIRCULAR_REFERENCE_DERIVATION"
    assert record["x_m"].size == 121
    assert record["x_m"][0] == pytest.approx(0.0)
    assert record["x_m"][-1] == pytest.approx(0.356)
    assert record["delta_specific_momentum_m_per_s"][0] == pytest.approx(0.0)
    assert record["delta_specific_momentum_m_per_s"][-1] == pytest.approx(-11.8476014832952)


def test_reference_momentum_curve_contains_net_streamwise_loss() -> None:
    record = load_momentum_reduction()
    momentum = record["delta_specific_momentum_m_per_s"]

    assert np.min(momentum) < -17.0
    assert np.max(momentum) > 0.0
    assert momentum[-1] < 0.0


def test_cell_line_force_is_signed_and_globally_conservative() -> None:
    faces = np.linspace(0.0, 0.356, 41)
    mass_flow = 2.0
    line_force = cell_net_momentum_rate_per_length(faces, mass_flow)
    diagnostic = conservation_diagnostic(faces, mass_flow)

    assert line_force.shape == (40,)
    assert np.any(line_force < 0.0)
    assert np.any(line_force > 0.0)
    assert diagnostic["absolute_mismatch_N"] < 1.0e-12
    assert diagnostic["expected_net_force_N"] == pytest.approx(
        mass_flow * -11.8476014832952
    )


def test_mesh_refinement_preserves_total_net_force() -> None:
    mass_flow = 2.0674506962
    totals = []
    for cells in (20, 40, 80, 160):
        faces = np.linspace(0.0, 0.356, cells + 1)
        line_force = cell_net_momentum_rate_per_length(faces, mass_flow)
        totals.append(float(np.sum(line_force * np.diff(faces))))

    assert_allclose(totals, totals[0], rtol=0.0, atol=1.0e-12)


def test_interpolation_rejects_out_of_domain_requests() -> None:
    with pytest.raises(ValueError, match="outside"):
        interpolate_specific_momentum(np.array([-1.0e-4, 0.1]))
    with pytest.raises(ValueError, match="outside"):
        interpolate_specific_momentum(np.array([0.1, 0.3561]))


def test_invalid_mesh_or_mass_flow_is_rejected() -> None:
    with pytest.raises(ValueError):
        cell_net_momentum_rate_per_length([0.0, 0.1, 0.05], 2.0)
    with pytest.raises(ValueError):
        cell_net_momentum_rate_per_length([0.0, 0.1, 0.356], 0.0)
