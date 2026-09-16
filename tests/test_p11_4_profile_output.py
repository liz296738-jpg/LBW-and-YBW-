"""Fast contract tests for P11.4 full-profile export."""
from cases.studies import p11_4_profile_output as profile


def test_profile_export_claim_boundary_and_resolution_are_explicit() -> None:
    assert profile.CASE_CLASSIFICATION == "PROJECT_DEFINED_H2_FULL_PROFILE_EXPORT"
    assert profile.NOT_A_SOURCE_REPRODUCTION is True
    assert profile.DEFAULT_CELLS == 80
    assert profile.DEFAULT_TOLERANCE == 2.0e-5


def test_profile_schema_contains_flow_closure_and_composition_inputs() -> None:
    required = {
        "x_m",
        "area_m2",
        "rho_kg_per_m3",
        "u_m_per_s",
        "p_Pa",
        "T_K",
        "Mach",
        "mass_flow_kg_per_s",
        "equivalence_ratio",
        "raw_mixing_efficiency",
        "combustion_efficiency",
        "fuel_mass_source_gradient_kg_per_s_per_m",
    }
    assert required.issubset(set(profile.BASE_PROFILE_COLUMNS))
