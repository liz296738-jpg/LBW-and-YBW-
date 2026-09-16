import math

from cases.studies import p12_project_defined_response_sweep as sweep


def test_scientific_classification_is_explicit():
    assert sweep.CASE_CLASSIFICATION == "P12_PROJECT_DEFINED_RESPONSE_SWEEP"
    assert sweep.NOT_A_SOURCE_REPRODUCTION is True
    assert sweep.NO_MODE_LABEL_CLAIM is True
    assert sweep.PROJECT_EQUIVALENCE_RATIOS == (0.10, 0.20, 0.30)


def test_response_point_rejects_nonpositive_phi():
    for phi in (0.0, -0.1):
        try:
            sweep.run_response_point(phi)
        except ValueError as exc:
            assert "positive" in str(exc)
        else:
            raise AssertionError("nonpositive phi must be rejected")


def test_project_defined_sweep_respects_solver_admissibility_and_teacher_gate():
    points = sweep.run_sweep()
    assert [p.equivalence_ratio for p in points] == list(sweep.PROJECT_EQUIVALENCE_RATIOS)

    # The default study is accepted only when a point either converges through
    # the teacher Eq.11.46 gate or is stopped by the already-documented
    # forward-flow model-domain guard.  A future, separately verified model
    # improvement may allow a previously guarded point to converge, so the
    # test deliberately does not require any specific phi to remain guarded.
    allowed_statuses = {sweep.STATUS_CONVERGED, sweep.STATUS_FORWARD_FLOW_GUARD}
    assert all(point.status in allowed_statuses for point in points)

    converged = [point for point in points if point.status == sweep.STATUS_CONVERGED]
    guarded = [point for point in points if point.status == sweep.STATUS_FORWARD_FLOW_GUARD]
    assert len(converged) >= 2

    # phi=0.20 is the accepted P11.4 project-defined H2 baseline and must remain
    # a valid converged point unless the baseline itself is intentionally revised.
    baseline_point = next(point for point in points if point.equivalence_ratio == 0.20)
    assert baseline_point.status == sweep.STATUS_CONVERGED

    for point in converged:
        assert point.converged is True
        assert point.steps is not None and point.steps > 0
        assert point.density_change is not None and point.density_change <= 1.0e-4
        # The normalized semi-discrete residual is an independent diagnostic;
        # no unsourced 1e-4 acceptance threshold is imposed on it.
        assert point.normalized_residual is not None and math.isfinite(point.normalized_residual)
        assert point.normalized_residual >= 0.0
        assert point.fuel_mass_source_kg_per_s > 0.0
        assert point.mass_inventory_relative_to_inlet is not None
        assert math.isfinite(point.mass_inventory_relative_to_inlet)
        assert 0.0 <= point.mass_inventory_relative_to_inlet <= 5.0e-3
        for value in (
            point.momentum_inventory_relative_to_inlet,
            point.energy_inventory_relative_to_inlet,
        ):
            assert value is not None and math.isfinite(value) and value >= 0.0
        assert point.min_mach is not None and point.max_mach is not None
        assert point.min_mach > 0.0 and point.max_mach >= point.min_mach
        assert point.min_pressure_Pa is not None and point.max_pressure_Pa is not None
        assert point.min_pressure_Pa > 0.0 and point.max_pressure_Pa >= point.min_pressure_Pa
        assert point.min_temperature_K is not None and point.max_temperature_K is not None
        assert point.min_temperature_K > 0.0 and point.max_temperature_K >= point.min_temperature_K

    for point in guarded:
        assert point.converged is False
        assert point.note is not None and "forward axial flow" in point.note
        assert point.steps is None
        assert point.density_change is None
        assert point.normalized_residual is None
        assert point.mass_inventory_relative_to_inlet is None
        assert point.momentum_inventory_relative_to_inlet is None
        assert point.energy_inventory_relative_to_inlet is None
        assert point.min_mach is None and point.max_mach is None
        assert point.min_pressure_Pa is None and point.max_pressure_Pa is None
        assert point.min_temperature_K is None and point.max_temperature_K is None
