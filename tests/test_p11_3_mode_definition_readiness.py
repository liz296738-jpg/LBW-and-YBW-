"""Regression tests for P11.3 definition-first mode evidence."""

from cases.studies.p11_3_mode_definition_readiness import (
    build_readiness,
    load_mode_definition_source,
)


def test_general_mode_taxonomy_is_frozen_but_project_labels_are_not() -> None:
    record = load_mode_definition_source()
    readiness = record["classifier_readiness"]

    assert readiness["general_mode_taxonomy_ready"] is True
    assert readiness["transition_mechanism_evidence_ready"] is True
    assert readiness["lbw_ybw_label_mapping_ready"] is False
    assert readiness["classifier_ready"] is False
    assert readiness["regime_map_ready"] is False
    assert record["project_label_resolution"]["status"] == "UNRESOLVED_PROJECT_SPECIFIC_SEMANTICS"


def test_authoritative_sources_and_dois_are_frozen() -> None:
    record = load_mode_definition_source()
    sources = {entry["source_id"]: entry for entry in record["evidence_sources"]}

    assert sources["TIAN-ET-AL-2014-Q1D-MULTIMODES"]["doi"] == "10.2514/1.B35177"
    assert sources["ZHANG-ET-AL-2014-MODE-TRANSITION"]["doi"] == "10.1016/j.actaastro.2014.06.006"
    assert sources["LIU-ET-AL-2019-AXISYMMETRIC-TRANSITION"]["doi"] == "10.2514/1.J058391"
    assert sources["FOTIA-DRISCOLL-2013-RAM-SCRAM"]["doi"] == "10.2514/1.B34486"
    assert sources["CAO-ET-AL-2020-1D-BOUNDARY"]["doi"] == "10.1016/j.ast.2019.105590"


def test_tian_taxonomy_distinguishes_dual_modes_by_post_shock_mach() -> None:
    record = load_mode_definition_source()
    sources = {entry["source_id"]: entry for entry in record["evidence_sources"]}
    taxonomy = sources["TIAN-ET-AL-2014-Q1D-MULTIMODES"]["mode_taxonomy"]

    supersonic = taxonomy["dual_mode_supersonic_combustion_mode"]["flow_observable"].lower()
    subsonic = taxonomy["dual_mode_subsonic_combustion_mode"]["flow_observable"].lower()
    assert "greater than one" in supersonic
    assert "less than one" in subsonic


def test_facility_specific_pressure_thresholds_cannot_be_promoted_universally() -> None:
    record = load_mode_definition_source()
    sources = {entry["source_id"]: entry for entry in record["evidence_sources"]}
    zhang = sources["ZHANG-ET-AL-2014-MODE-TRANSITION"]

    assert "0.23" in zhang["facility_specific_example"]["lower_transition"]
    assert "0.34" in zhang["facility_specific_example"]["upper_transition"]
    assert "must not be promoted as universal" in zhang["limitation"]


def test_readiness_refuses_classifier_until_label_and_observable_mapping_exist() -> None:
    readiness = build_readiness()

    assert readiness["definition_evidence_ready"] is True
    assert readiness["lbw_ybw_label_mapping_ready"] is False
    assert readiness["solver_observable_mapping_ready"] is False
    assert readiness["classifier_ready"] is False
    assert readiness["regime_map_ready"] is False
    assert len(readiness["blocking_items"]) >= 3


def test_mach_only_and_downstream_reacceleration_shortcuts_are_forbidden() -> None:
    record = load_mode_definition_source()
    rules = {entry["rule_id"]: entry["rule"].lower() for entry in record["frozen_general_rules"]}

    assert "solely" in rules["MODE-DEF-001"]
    assert "minimum mach" in rules["MODE-DEF-001"]
    assert "reacceleration" in rules["MODE-DEF-003"]
    assert "cannot by itself" in rules["MODE-DEF-003"]
