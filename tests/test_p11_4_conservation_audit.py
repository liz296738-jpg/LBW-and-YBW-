"""Contract tests for the P11.4 discrete conservation audit."""
from cases.studies.p11_4_conservation_audit import (
    CASE_CLASSIFICATION,
    NOT_A_SOURCE_REPRODUCTION,
)


def test_conservation_audit_claim_boundary() -> None:
    assert CASE_CLASSIFICATION == "PROJECT_DEFINED_DISCRETE_CONSERVATION_AUDIT"
    assert NOT_A_SOURCE_REPRODUCTION is True
