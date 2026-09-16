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


def test_project_defined_sweep_executes_and_converges():
    points = sweep.run_sweep()
    assert [p.equivalence_ratio for p in points] == list(sweep.PROJECT_EQUIVALENCE_RATIOS)
    assert all(p.converged for p in points)
    assert all(p.steps > 0 for p in points)
    assert all(p.normalized_residual <= 1.0e-4 for p in points)
    assert all(p.fuel_mass_source_kg_per_s > 0.0 for p in points)
    assert all(p.min_mach > 0.0 and p.max_mach >= p.min_mach for p in points)
    assert all(p.min_pressure_Pa > 0.0 and p.max_pressure_Pa >= p.min_pressure_Pa for p in points)
    assert all(p.min_temperature_K > 0.0 and p.max_temperature_K >= p.min_temperature_K for p in points)
