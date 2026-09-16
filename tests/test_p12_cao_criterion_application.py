from cases.studies import p12_cao_criterion_application as application
from scramjet1d.cao_mode_criteria import ThermalThroatState


def test_application_claim_boundary_is_explicit() -> None:
    assert application.CASE_CLASSIFICATION == "P12_SOURCE_CRITERION_ON_PROJECT_DEFINED_SWEEP"
    assert application.NOT_A_SOURCE_REPRODUCTION is True
    assert application.PROJECT_SONIC_TOLERANCES == (1.0e-6, 1.0e-4, 1.0e-3, 1.0e-2)


def test_two_converged_points_are_robustly_on_cao_scram_side() -> None:
    points = application.run_application()
    assert [point.equivalence_ratio for point in points] == [0.1, 0.2, 0.3]
    for point in points[:2]:
        assert point.solver_status == "CONVERGED"
        assert point.minimum_mach is not None and point.minimum_mach > 1.0
        assert point.sonic_margin is not None and point.sonic_margin > 0.0
        assert point.criterion_state == ThermalThroatState.SCRAM_SIDE.value
        assert point.tolerance_stable is True


def test_guarded_point_is_not_assigned_a_physical_mode() -> None:
    point = application.run_application()[2]
    assert point.solver_status == "FORWARD_FLOW_GUARD_TRIGGERED"
    assert point.minimum_mach is None
    assert point.sonic_margin is None
    assert point.criterion_state is None
    assert point.tolerance_stable is None
