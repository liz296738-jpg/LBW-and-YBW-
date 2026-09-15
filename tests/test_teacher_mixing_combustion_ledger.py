"""Guard the machine-readable teacher Chapter 11 closure evidence ledger."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "cases" / "studies" / "data" / "teacher_mixing_combustion_closure.json"


def _load() -> dict[str, object]:
    with LEDGER.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def test_teacher_closure_ledger_freezes_primary_source_and_equation_scope() -> None:
    record = _load()
    assert record["schema_version"] == 1
    assert record["stage"] == "P11.3C"
    assert record["status"] == (
        "TEACHER_CH11_MIXING_LEAN_COMPOSITION_AND_EFFICIENCY_POLICY_VERIFIED_VARIABLE_COMPOSITION_COUPLING_GATED"
    )

    source = record["primary_source"]
    assert "高超声速气动布局理论及应用" in source["identity"]
    assert source["page_range"] == "255-258"
    assert len(source["local_evidence"]) == 4

    equations = record["equations"]
    assert set(equations) == {"11.18", "11.19", "11.20", "11.21-11.24", "11.27-11.29"}
    assert equations["11.18"]["physical_interval"] == [0.0, 1.0]
    assert equations["11.19"]["implementation_policy"] == (
        "RETURN_RAW_EMPIRICAL_CORRELATION_WITHOUT_SILENT_CLIPPING"
    )
    assert equations["11.27-11.29"]["validity"] == "phi <= 1"
    assert equations["11.27-11.29"]["air_molar_basis_per_O2"] == {
        "N2": 3.7274,
        "AR": 0.04592,
    }


def test_teacher_closure_ledger_freezes_explicit_efficiency_policy_and_remaining_gates() -> None:
    record = _load()
    policy = record["project_adapter_policy"]
    assert policy["identity"] == "EXPLICIT_MIXING_TO_COMBUSTION_EFFICIENCY_SATURATION"
    assert policy["formula"] == "eta = min(eta_m_raw, 1.0)"
    assert policy["classification"] == "PROJECT_POLICY_NOT_A_MODIFICATION_OF_EQ_11_19"

    boundaries = record["scientific_boundaries"]
    assert boundaries["raw_mixing_efficiency_can_exceed_one"] is True
    assert boundaries["raw_mixing_correlation_remains_unmodified"] is True
    assert boundaries["reaction_efficiency_requires_unit_interval"] is True
    assert boundaries["raw_to_reaction_efficiency_policy"] == (
        "EXPLICIT_SATURATION_AT_ONE_IN_SEPARATE_ADAPTER"
    )
    assert boundaries["prescribed_Qdot_double_counting_forbidden"] is True

    coverage = record["thermochemistry_coverage"]
    assert coverage["H2"] == "CORE_THERMO_DATABASE_AVAILABLE"
    assert coverage["C2H4"] == "CORE_THERMO_DATABASE_AVAILABLE"
    assert coverage["C10H22"].endswith("THERMO_POLYNOMIALS_STILL_BLOCKED")

    readiness = record["readiness"]
    assert readiness["source_transcription_ready"] is True
    assert readiness["isolated_closure_verification_ready"] is True
    assert readiness["combustion_efficiency_policy_ready"] is True
    assert readiness["variable_composition_solver_coupling_ready"] is False
    assert readiness["production_solver_replacement_ready"] is False
