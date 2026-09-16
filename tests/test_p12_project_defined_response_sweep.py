import pytest

from cases.studies import p12_project_defined_response_sweep as sweep


def test_scientific_classification_is_explicit():
    assert sweep.CASE_CLASSIFICATION == "P12_PROJECT_DEFINED_RESPONSE_SWEEP"
    assert sweep.NOT_A_SOURCE_REPRODUCTION is True
    assert sweep.NO_MODE_LABEL_CLAIM is True
    assert sweep.PROJECT_EQUIVALENCE_RATIOS == (0.10, 0.20, 0.30)


def test_response_point_rejects_nonpositive_phi():
    for phi in (0.0, -0.1):
        with pytest.raises(ValueError, match="positive"):
            sweep.run_response_point(phi)


def test_forward_flow_guard_is_recorded_without_mode_claim(monkeypatch):
    def _raise_guard(*args, **kwargs):
        raise ValueError(sweep.FORWARD_FLOW_GUARD_TEXT)

    monkeypatch.setattr(sweep, "solve_teacher_boundary_steady", _raise_guard)
    point = sweep.run_response_point(0.30)

    assert point.status == sweep.STATUS_FORWARD_FLOW_GUARD
    assert point.converged is False
    assert point.note is not None and "forward axial flow" in point.note
    assert point.steps is None
    assert point.density_change is None
    assert point.normalized_residual is None
    assert point.mass_inventory_relative_to_inlet is None
    assert point.momentum_inventory_relative_to_inlet is None
    assert point.energy_inventory_relative_to_inlet is None
    assert point.min_mach is None and point.max_mach is None


def test_unexpected_solver_value_error_is_not_swallowed(monkeypatch):
    def _raise_unexpected(*args, **kwargs):
        raise ValueError("unexpected thermodynamic failure")

    monkeypatch.setattr(sweep, "solve_teacher_boundary_steady", _raise_unexpected)
    with pytest.raises(ValueError, match="unexpected thermodynamic failure"):
        sweep.run_response_point(0.20)


# The full 0.10/0.20/0.30 sweep is intentionally executed in the dedicated
# P12 GitHub Actions workflow rather than in ordinary pytest.  It is a
# multi-minute numerical study and its acceptance artifact belongs with the
# study workflow, while pytest remains a fast regression/contract suite.
