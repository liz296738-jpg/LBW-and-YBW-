"""Contract tests for the P11.4 discrete conservation audit."""
from dataclasses import fields

from cases.studies.p11_4_conservation_audit import (
    CASE_CLASSIFICATION,
    NOT_A_SOURCE_REPRODUCTION,
    ConservationAuditResult,
)


def test_conservation_audit_claim_boundary() -> None:
    assert CASE_CLASSIFICATION == "PROJECT_DEFINED_DISCRETE_CONSERVATION_AUDIT"
    assert NOT_A_SOURCE_REPRODUCTION is True


def test_conservation_audit_reports_dimensionless_inventory_diagnostics() -> None:
    names = {field.name for field in fields(ConservationAuditResult)}
    assert "mass_rate_relative_to_inlet" in names
    assert "momentum_rate_relative_to_inlet" in names
    assert "energy_rate_relative_to_inlet" in names
