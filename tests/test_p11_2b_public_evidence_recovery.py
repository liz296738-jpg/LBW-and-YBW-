import importlib.util
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "cases" / "studies" / "p11_2b_public_evidence_recovery.py"
SPEC = importlib.util.spec_from_file_location("p11_2b_public_evidence_recovery", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_primary_recovery_preserves_formal_blockers():
    record = MODULE.load_source_record()
    summary = MODULE.derive_public_recovery(record)

    assert summary["formal_case_ready"] is False
    assert len(summary["formal_blockers_unchanged"]) == 4
    assert summary["source_analysis_boundary"]["jin_fig14_Cf_inference_authorized"] is False
    assert summary["exploratory_only"]["formal_use_authorized"] is False


def test_same_row_total_pressure_derivation_is_exact_and_traceable():
    summary = MODULE.derive_public_recovery(MODULE.load_source_record())
    exact = summary["exact_same_row_constraints"]

    assert exact["liu_model_B_phi"] == 1.03
    assert exact["exit_Mach"] == 2.27
    assert exact["classification"] == "DERIVED_FROM_SAME_ROW_SOURCE_VALUES"
    assert math.isclose(
        exact["derived_pt3_Pa"],
        17383.8 / 0.39,
        rel_tol=0.0,
        abs_tol=1.0e-10,
    )


def test_exploratory_energy_bridge_is_numerically_reproducible_but_not_formal():
    summary = MODULE.derive_public_recovery(MODULE.load_source_record())
    exploratory = summary["exploratory_only"]

    expected_isolator_area = math.pi * 0.035**2 / 4.0
    expected_capture_area = 1.9 * expected_isolator_area
    expected_mdot = 0.0025 * 1966.0 * expected_capture_area
    expected_delta_ht = (1.16 - 1.0) * 1255.0 * 2400.0
    expected_power = expected_mdot * expected_delta_ht

    assert math.isclose(exploratory["isolator_area_m2"], expected_isolator_area)
    assert math.isclose(exploratory["nominal_capture_area_m2"], expected_capture_area)
    assert math.isclose(
        exploratory["nominal_full_capture_mass_flow_kg_s"], expected_mdot
    )
    assert math.isclose(exploratory["candidate_delta_ht_J_kg"], expected_delta_ht)
    assert math.isclose(exploratory["candidate_total_heat_power_W"], expected_power)
    assert exploratory["formal_use_authorized"] is False


def test_recovery_summary_writer_round_trip(tmp_path):
    summary = MODULE.derive_public_recovery(MODULE.load_source_record())
    output = tmp_path / "recovery.json"
    written = MODULE.write_recovery_summary(summary, output)

    assert written == output
    text = output.read_text(encoding="utf-8")
    assert '"formal_case_ready": false' in text
    assert '"derived_pt3_Pa"' in text
    assert '"candidate_total_heat_power_W"' in text
