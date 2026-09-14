"""Assemble the offline, exact-SHA P10.4 verification evidence closure."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from copy import deepcopy
from pathlib import Path
from typing import Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
BASELINE_SHA = "bc9963f66cb64f043254b34532863b97432cc287"
EXPECTED_EVIDENCE_IDS = tuple(f"E{number:02d}" for number in range(1, 17))
EXPECTED_CLAIM_IDS = tuple(f"C{number:02d}" for number in range(1, 16))
EVIDENCE_FIELDS = (
    "evidence_id", "stage", "category", "subject", "method", "reference",
    "result", "status", "supported_claim_ids", "limitations",
)
CLAIM_FIELDS = ("claim_id", "claim", "status", "evidence_ids", "scope", "qualification")
CLAIM_STATUSES = {"SUPPORTED", "QUALIFIED", "NOT_ESTABLISHED"}
SUMMARY_HEADINGS = (
    "# P10 Verification & Validation Closure", "## Scope", "## Accepted Evidence",
    "## Numerical Verification", "## Physics/Source Verification",
    "## Boundary Verification", "## Spatial Convergence", "## CFL Sensitivity",
    "## RK3 Temporal Verification", "## Scheme Comparison", "## Supported Claims",
    "## Qualified Claims", "## Not Established", "## Limitations", "## Closure Status",
)

ACCEPTED_EVIDENCE = {
    "P10.1": {
        "stage": "P10.1", "accepted_sha": "32eb50cd687da6e23a4cb2269bc31120fbff2b3e",
        "standard_ci_run": 34638173666, "pytest_passed": 706,
        "artifact_id": None, "status": "accepted",
    },
    "P10.2": {
        "stage": "P10.2", "accepted_sha": "ce27e3fd841362432791f45f3c8ad53a3002ecf4",
        "dedicated_run": 34686588293, "artifact_id": 10295429740, "status": "accepted",
    },
    "P10.3": {
        "stage": "P10.3", "accepted_sha": "bc9963f66cb64f043254b34532863b97432cc287",
        "standard_ci_run": 34700186067, "dedicated_run": 34700559898,
        "artifact_id": 10299894650,
        "artifact_sha256": "a5834f82789839f05a74a1dae0e6198722b14059a1d3ecef89914df73e615785",
        "pytest_passed": 736, "status": "accepted",
    },
}

EVIDENCE_MATRIX = [
    {"evidence_id": "E01", "stage": "P2", "category": "state algebra", "subject": "primitive-to-conservative conversion and ideal-gas state consistency", "method": "unit identities", "reference": "P2 tests", "result": "thermodynamic/state algebra identities pass", "status": "verified", "supported_claim_ids": ["C01"], "limitations": "perfect-gas thermodynamics"},
    {"evidence_id": "E02", "stage": "P3", "category": "flux", "subject": "physical Euler flux implementation", "method": "unit identities", "reference": "P3 tests", "result": "Euler flux identities pass", "status": "verified", "supported_claim_ids": ["C01"], "limitations": "inviscid Euler model"},
    {"evidence_id": "E03", "stage": "P5", "category": "flux", "subject": "Steger-Warming FVS with eigenvalues lambda1=u-a, lambda2=u, lambda3=u+a", "method": "splitting and interface tests", "reference": "P5 tests", "result": "implementation verification passes", "status": "verified", "supported_claim_ids": ["C03", "C09"], "limitations": "does not establish a universally superior flux"},
    {"evidence_id": "E04", "stage": "P4", "category": "geometry", "subject": "quasi-1D area source", "method": "variable-area formulation, static constant-pressure well-balanced test, constant-area reduction", "reference": "P4 tests", "result": "area formulation passes controlled checks", "status": "verified", "supported_claim_ids": ["C01", "C02"], "limitations": "quasi-one-dimensional model"},
    {"evidence_id": "E05", "stage": "P9", "category": "boundaries", "subject": "supersonic inflow/outflow and subsonic total-condition inflow/static-pressure outlet", "method": "boundary unit and integration tests", "reference": "P9 tests", "result": "physical boundary contracts pass", "status": "verified on tested rightward regimes", "supported_claim_ids": ["C06"], "limitations": "not arbitrary multidirectional boundary flow"},
    {"evidence_id": "E06", "stage": "P10.1", "category": "conservation", "subject": "global mass, momentum, and energy balance", "method": "discrete conservation ledger", "reference": "P10.1 accepted evidence", "result": "global conservation identities close", "status": "verified", "supported_claim_ids": ["C01"], "limitations": "tested discrete configurations"},
    {"evidence_id": "E07", "stage": "P6", "category": "source terms", "subject": "wall friction and wall heat source", "method": "analytical and algebraic source checks", "reference": "P6 tests", "result": "wall sources pass", "status": "analytically / algebraically verified", "supported_claim_ids": ["C07"], "limitations": "prescribed wall source models"},
    {"evidence_id": "E08", "stage": "P7", "category": "source terms", "subject": "fuel injection mass, momentum, and energy source accounting", "method": "analytical integral and accounting tests", "reference": "P7 tests", "result": "source formulation passes", "status": "analytically verified source formulation", "supported_claim_ids": ["C07"], "limitations": "not physical fuel-atomization validation"},
    {"evidence_id": "E09", "stage": "P8", "category": "source terms", "subject": "prescribed burn rate and LHV heat-release source", "method": "controlled source-term tests", "reference": "P8 tests", "result": "prescribed energy mapping passes", "status": "controlled source-term verification", "supported_claim_ids": ["C07"], "limitations": "not chemistry, species, or flame validation"},
    {"evidence_id": "E10", "stage": "P10.1", "category": "source terms", "subject": "wall + fuel + combustion + quasi-1D source superposition", "method": "combined ledger identity", "reference": "P10.1 accepted evidence", "result": "source sum equals combined source", "status": "verified", "supported_claim_ids": ["C01", "C07"], "limitations": "instantaneous prescribed-source identity"},
    {"evidence_id": "E11", "stage": "P10.2", "category": "spatial convergence", "subject": "smooth subsonic/supersonic Rusanov and Steger-Warming solutions at N=40/80/160", "method": "grid refinement against analytical solution", "reference": "P10.2 accepted evidence", "result": "approximately first-order convergence", "status": "verified on tested smooth benchmark", "supported_claim_ids": ["C02", "C03", "C09"], "limitations": "smooth benchmark only; no equivalent shock convergence closure"},
    {"evidence_id": "E12", "stage": "P10.2/P10.3", "category": "steady convergence", "subject": "all formal P10.2 and P10.3 steady cases", "method": "normalized residual gate", "reference": "P10.2 and P10.3 accepted evidence", "result": "residual <= 1e-8", "status": "verified for tested benchmarks", "supported_claim_ids": ["C02", "C03", "C04"], "limitations": "tested benchmarks only"},
    {"evidence_id": "E13", "stage": "P10.3", "category": "CFL sensitivity", "subject": "CFL=0.1, 0.2, and 0.4 at N=80", "method": "converged-field difference relative to spatial error", "reference": "P10.3 accepted evidence", "result": "converged discrete steady state materially insensitive", "status": "verified within tested CFL range", "supported_claim_ids": ["C04"], "limitations": "does not establish a universal stability limit"},
    {"evidence_id": "E14", "stage": "P10.3", "category": "temporal convergence", "subject": "SSP-RK3 on y'=-y", "method": "dt refinement against exp(-1)", "reference": "P10.3 orders 3.0578255193509354, 3.0288865949946873, 3.014435458873415", "result": "approximately third-order", "status": "verified on tested scalar ODE", "supported_claim_ids": ["C05"], "limitations": "not a complete transient-CFD temporal-order study"},
    {"evidence_id": "E15", "stage": "P10.3", "category": "scheme comparison", "subject": "Rusanov versus Steger-Warming", "method": "implemented benchmark comparison", "reference": "P10.3 accepted evidence", "result": "quantitative comparison complete", "status": "benchmark-specific comparison complete", "supported_claim_ids": ["C09"], "limitations": "no universal winner established"},
    {"evidence_id": "E16", "stage": "P10.1-P10.4", "category": "reproducibility", "subject": "exact SHA, standard CI, dedicated workflows, and artifact provenance", "method": "immutable registry and runtime Git gates", "reference": "accepted evidence registry", "result": "provenance chain is auditable", "status": "verified", "supported_claim_ids": ["C01", "C02", "C03", "C04", "C05", "C06", "C07", "C08", "C09"], "limitations": "workflow evidence is tied to recorded revisions"},
]

CLAIM_LEDGER = [
    {"claim_id": "C01", "claim": "The quasi-1D solver satisfies the tested discrete conservation identities.", "status": "SUPPORTED", "evidence_ids": ["E01", "E02", "E04", "E06", "E10", "E16"], "scope": "tested discrete conservation configurations", "qualification": ""},
    {"claim_id": "C02", "claim": "The tested smooth quasi-1D solutions exhibit approximately first-order spatial convergence under grid refinement.", "status": "SUPPORTED", "evidence_ids": ["E04", "E11", "E12", "E16"], "scope": "tested smooth quasi-1D analytical benchmark", "qualification": ""},
    {"claim_id": "C03", "claim": "Both Rusanov and Steger-Warming pass the tested smooth subsonic and supersonic spatial-convergence protocol.", "status": "SUPPORTED", "evidence_ids": ["E03", "E11", "E12", "E16"], "scope": "tested smooth subsonic and supersonic cases", "qualification": ""},
    {"claim_id": "C04", "claim": "Within CFL 0.1-0.4 on the tested N=80 steady benchmarks, the converged discrete solution is materially insensitive to pseudo-time CFL.", "status": "SUPPORTED", "evidence_ids": ["E12", "E13", "E16"], "scope": "CFL 0.1-0.4; tested N=80 steady benchmarks", "qualification": ""},
    {"claim_id": "C05", "claim": "The existing SSP-RK3 implementation shows approximately third-order temporal convergence on the tested smooth scalar ODE.", "status": "SUPPORTED", "evidence_ids": ["E14", "E16"], "scope": "tested scalar ODE only", "qualification": "not all transient CFD flows"},
    {"claim_id": "C06", "claim": "The physical boundary-condition implementations pass the tested rightward subsonic and supersonic regimes.", "status": "SUPPORTED", "evidence_ids": ["E05", "E16"], "scope": "tested rightward-flow regimes", "qualification": ""},
    {"claim_id": "C07", "claim": "Wall, fuel-injection, and prescribed combustion source terms pass controlled analytical/accounting verification tests.", "status": "SUPPORTED", "evidence_ids": ["E07", "E08", "E09", "E10", "E16"], "scope": "implemented prescribed source models", "qualification": ""},
    {"claim_id": "C08", "claim": "The solver is suitable for controlled one-dimensional scramjet/ramjet engineering studies within the implemented model assumptions.", "status": "QUALIFIED", "evidence_ids": ["E01", "E02", "E04", "E05", "E06", "E07", "E08", "E09", "E10", "E11", "E12", "E13", "E14", "E15", "E16"], "scope": "controlled studies within verified benchmark envelope", "qualification": "quasi-1D; perfect gas; prescribed source models; no full chemistry; no experimental engine validation"},
    {"claim_id": "C09", "claim": "Steger-Warming and Rusanov can be compared quantitatively on the implemented benchmarks.", "status": "QUALIFIED", "evidence_ids": ["E03", "E11", "E15", "E16"], "scope": "implemented benchmarks", "qualification": "benchmark-specific; no universal winner"},
    {"claim_id": "C10", "claim": "The complete CFD solver is third-order accurate in physical time for arbitrary transient flows.", "status": "NOT_ESTABLISHED", "evidence_ids": [], "scope": "arbitrary transient CFD", "qualification": "P10.3 covers only a scalar ODE"},
    {"claim_id": "C11", "claim": "CFL=0.4 is a universal stability limit.", "status": "NOT_ESTABLISHED", "evidence_ids": [], "scope": "universal stability", "qualification": "only CFL 0.1-0.4 on selected steady cases was tested"},
    {"claim_id": "C12", "claim": "Steger-Warming is universally more accurate than Rusanov.", "status": "NOT_ESTABLISHED", "evidence_ids": [], "scope": "all flow regimes", "qualification": "comparisons are benchmark-specific"},
    {"claim_id": "C13", "claim": "The combustion model predicts real flame chemistry.", "status": "NOT_ESTABLISHED", "evidence_ids": [], "scope": "real reacting flow", "qualification": "the model uses prescribed heat release"},
    {"claim_id": "C14", "claim": "The model has been experimentally validated against a real engine.", "status": "NOT_ESTABLISHED", "evidence_ids": [], "scope": "real engines", "qualification": "no experimental engine validation has been performed"},
    {"claim_id": "C15", "claim": "The current solver predicts real LBW/YBW operating maps with established experimental accuracy.", "status": "NOT_ESTABLISHED", "evidence_ids": [], "scope": "LBW/YBW operating maps", "qualification": "P11 studies and experimental validation have not been completed"},
]

MANDATORY_LIMITATIONS = (
    "quasi-one-dimensional model",
    "perfect-gas thermodynamics",
    "no species transport",
    "no finite-rate chemistry",
    "combustion is prescribed heat release from burn-rate input",
    "no turbulence model",
    "no multidimensional viscous flow",
    "no experimental engine validation",
    "RK3 third-order evidence applies only to tested scalar ODE",
    "CFL study does not establish universal stability limits",
    "spatial convergence result applies to tested smooth benchmark",
    "shock problems have not undergone an equivalent formal grid-convergence closure in P10",
    "scheme comparison is benchmark-specific",
    "full LBW/YBW parametric conclusions are not yet established",
)


def resolve_head_sha(explicit: str | None = None) -> str:
    """Resolve exact SHA from explicit input, Actions, or the local checkout."""
    head = explicit or os.environ.get("GITHUB_SHA")
    if head is None:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if re.fullmatch(r"[0-9a-fA-F]{40}", head) is None:
        raise ValueError("head SHA must contain exactly 40 hexadecimal characters")
    return head.lower()


def git_ancestry_checks(head: str = "HEAD") -> dict[str, bool]:
    """Check every accepted revision against the current local Git graph."""
    return {
        stage: subprocess.run(
            ["git", "merge-base", "--is-ancestor", entry["accepted_sha"], head],
            cwd=ROOT, check=False, capture_output=True,
        ).returncode == 0
        for stage, entry in ACCEPTED_EVIDENCE.items()
    }


def production_files_changed(head: str = "HEAD") -> list[str]:
    """List production files changed after the frozen P10.3 baseline."""
    output = subprocess.check_output(
        ["git", "diff", "--name-only", BASELINE_SHA, head, "--", "src/scramjet1d/"],
        cwd=ROOT, text=True,
    )
    return [line for line in output.splitlines() if line]


def parse_pytest_xml(path: Path | str) -> dict[str, int]:
    """Read aggregate pytest counts from JUnit XML."""
    root = ET.parse(path).getroot()
    if root.tag == "testsuites" and "tests" not in root.attrib:
        suites = list(root.findall("testsuite"))
        counts = {name: sum(int(suite.attrib.get(name, 0)) for suite in suites) for name in ("tests", "failures", "errors", "skipped")}
    else:
        counts = {name: int(root.attrib.get(name, 0)) for name in ("tests", "failures", "errors", "skipped")}
    return {
        "pytest_tests": counts["tests"], "pytest_failures": counts["failures"],
        "pytest_errors": counts["errors"], "pytest_skipped": counts["skipped"],
        "pytest_passed": counts["tests"] - counts["failures"] - counts["errors"] - counts["skipped"],
    }


def _ids(rows: Sequence[Mapping[str, object]], key: str) -> list[str]:
    return [str(row.get(key, "")) for row in rows]


def assess_closure(
    *, accepted_evidence: Mapping[str, Mapping[str, object]], ancestry_checks: Mapping[str, bool],
    production_files_changed: Sequence[str], regression_summary: Mapping[str, object],
    evidence_matrix: Sequence[Mapping[str, object]], claim_ledger: Sequence[Mapping[str, object]],
    limitations: Sequence[str],
) -> dict:
    """Apply all fixed P10.4 closure gates without I/O."""
    stages_complete = set(accepted_evidence) == set(ACCEPTED_EVIDENCE)
    registry_exact = stages_complete and all(dict(accepted_evidence[stage]) == expected for stage, expected in ACCEPTED_EVIDENCE.items())
    shas_valid = stages_complete and all(re.fullmatch(r"[0-9a-f]{40}", str(entry.get("accepted_sha", ""))) for entry in accepted_evidence.values())
    ancestors = set(ancestry_checks) == set(ACCEPTED_EVIDENCE) and all(ancestry_checks.values())
    pytest_passed = (
        regression_summary.get("pytest_step_passed") is True
        and regression_summary.get("pytest_failures") == 0
        and regression_summary.get("pytest_errors") == 0
        and isinstance(regression_summary.get("pytest_passed"), int)
        and regression_summary["pytest_passed"] >= 736
    )
    evidence_ids = _ids(evidence_matrix, "evidence_id")
    claim_ids = _ids(claim_ledger, "claim_id")
    evidence_complete = len(evidence_ids) == len(set(evidence_ids)) and set(evidence_ids) == set(EXPECTED_EVIDENCE_IDS)
    claims_complete = len(claim_ids) == len(set(claim_ids)) and set(claim_ids) == set(EXPECTED_CLAIM_IDS)
    statuses_valid = claims_complete and all(row.get("status") in CLAIM_STATUSES for row in claim_ledger)
    valid_evidence = set(evidence_ids)
    references_valid = evidence_complete and all(
        isinstance(row.get("evidence_ids"), list)
        and all(reference in valid_evidence for reference in row["evidence_ids"])
        and (row.get("status") == "NOT_ESTABLISHED" or len(row["evidence_ids"]) >= 1)
        for row in claim_ledger
    )
    qualifications_complete = claims_complete and all(
        row.get("status") != "QUALIFIED" or bool(str(row.get("qualification", "")).strip())
        for row in claim_ledger
    )
    c08 = next((row for row in claim_ledger if row.get("claim_id") == "C08"), {})
    c08_qualification = str(c08.get("qualification", "")).lower()
    qualification_terms = ("quasi-1d", "perfect gas", "prescribed source models", "no full chemistry", "no experimental engine validation")
    c05 = next((row for row in claim_ledger if row.get("claim_id") == "C05"), {})
    c05_scope = str(c05.get("scope", "")).lower()
    scope_consistent = (
        all(term in c08_qualification for term in qualification_terms)
        and "tested scalar ode" in c05_scope
        and "all cfd transient flows" not in c05_scope
    )
    limitations_complete = set(MANDATORY_LIMITATIONS).issubset(set(limitations))
    gates = {
        "accepted_stage_registry_complete": bool(stages_complete and registry_exact),
        "accepted_shas_valid": bool(shas_valid),
        "all_accepted_stages_ancestors": bool(ancestors),
        "production_freeze_passed": not production_files_changed,
        "pytest_passed": bool(pytest_passed),
        "baseline_validation_passed": regression_summary.get("baseline_validation_passed") is True,
        "evidence_matrix_complete": bool(evidence_complete),
        "claim_ledger_complete": bool(claims_complete and statuses_valid),
        "claim_references_valid": bool(references_valid),
        "qualifications_complete": bool(qualifications_complete),
        "mandatory_limitations_complete": bool(limitations_complete),
        "closure_scope_consistent": bool(scope_consistent),
    }
    return {
        "gates": gates, "all_passed": all(gates.values()),
        "evidence_ids": evidence_ids, "claim_ids": claim_ids,
        "missing_evidence_ids": sorted(set(EXPECTED_EVIDENCE_IDS) - set(evidence_ids)),
        "unexpected_evidence_ids": sorted(set(evidence_ids) - set(EXPECTED_EVIDENCE_IDS)),
        "missing_claim_ids": sorted(set(EXPECTED_CLAIM_IDS) - set(claim_ids)),
        "unexpected_claim_ids": sorted(set(claim_ids) - set(EXPECTED_CLAIM_IDS)),
    }


def assemble_artifact(
    head_sha: str, regression_summary: Mapping[str, object], *,
    ancestry_checks: Mapping[str, bool] | None = None,
    production_files_changed: Sequence[str] | None = None,
) -> dict:
    """Build the canonical P10.4 exact-SHA artifact."""
    head = resolve_head_sha(head_sha)
    ancestry = dict(ancestry_checks) if ancestry_checks is not None else git_ancestry_checks(head)
    changed = list(production_files_changed) if production_files_changed is not None else globals()["production_files_changed"](head)
    assessment = assess_closure(
        accepted_evidence=ACCEPTED_EVIDENCE, ancestry_checks=ancestry,
        production_files_changed=changed, regression_summary=regression_summary,
        evidence_matrix=EVIDENCE_MATRIX, claim_ledger=CLAIM_LEDGER,
        limitations=MANDATORY_LIMITATIONS,
    )
    return {
        "schema_version": 1, "stage": "P10.4",
        "artifact_kind": "exact-sha-integrated-vv-closure",
        "baseline_sha": BASELINE_SHA, "head_sha": head,
        "accepted_evidence": deepcopy(ACCEPTED_EVIDENCE),
        "ancestry_checks": ancestry,
        "production_freeze": {
            "production_baseline_sha": BASELINE_SHA,
            "production_files_changed": changed,
            "production_freeze_passed": not changed,
        },
        "regression_summary": dict(regression_summary),
        "evidence_matrix": deepcopy(EVIDENCE_MATRIX),
        "claim_ledger": deepcopy(CLAIM_LEDGER),
        "limitations": list(MANDATORY_LIMITATIONS),
        **assessment,
    }


def _csv_value(value: object) -> object:
    return ";".join(str(item) for item in value) if isinstance(value, list) else value


def _write_csv(path: Path, fields: Sequence[str], rows: Sequence[Mapping[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: _csv_value(row.get(field, "")) for field in fields} for row in rows)


def _summary_markdown(artifact: Mapping[str, object]) -> str:
    claims = artifact["claim_ledger"]
    by_status = {status: [row for row in claims if row["status"] == status] for status in CLAIM_STATUSES}
    sections = [
        "# P10 Verification & Validation Closure",
        "## Scope\n\nThis closure integrates accepted numerical and implementation verification evidence. Verification asks whether the declared equations are implemented correctly; experimental validation asks whether the model represents a real engine. No experimental engine validation is claimed.",
        "## Accepted Evidence\n\n" + "\n".join(f"- {stage}: `{entry['accepted_sha']}` ({entry['status']})" for stage, entry in artifact["accepted_evidence"].items()),
        "## Numerical Verification\n\nState algebra, Euler flux, area formulation, conservation, and reproducibility evidence are traceable through E01-E06 and E16.",
        "## Physics/Source Verification\n\nControlled wall, fuel-injection, prescribed combustion, and source-superposition checks are covered by E07-E10. These do not validate atomization, chemistry, species, or flames.",
        "## Boundary Verification\n\nE05 supports only the tested rightward subsonic and supersonic boundary regimes.",
        "## Spatial Convergence\n\nE11-E12 support approximately first-order behavior on the tested smooth quasi-1D benchmarks. Shock-capable smoke tests exist, but they are not a formal shock grid-convergence closure.",
        "## CFL Sensitivity\n\nE13 supports material steady-state insensitivity over CFL 0.1-0.4 for the tested N=80 cases, not a universal stability limit.",
        "## RK3 Temporal Verification\n\nE14 supports approximately third-order convergence only on the tested scalar ODE `y'=-y`.",
        "## Scheme Comparison\n\nE15 supports benchmark-specific quantitative comparison; it establishes no universal winner.",
        "## Supported Claims\n\n" + "\n".join(f"- {row['claim_id']}: {row['claim']}" for row in by_status["SUPPORTED"]),
        "## Qualified Claims\n\n" + "\n".join(f"- {row['claim_id']}: {row['claim']} Qualification: {row['qualification']}." for row in by_status["QUALIFIED"]),
        "## Not Established\n\n" + "\n".join(f"- {row['claim_id']}: {row['claim']}" for row in by_status["NOT_ESTABLISHED"]),
        "## Limitations\n\nSee `p10_4_limitations.md` for the mandatory limitation ledger.",
        "## Closure Status\n\n" + ("P10 verification closure passed. The evidence chain is complete within the tested assumptions and benchmarks." if artifact["all_passed"] else "P10 verification closure did not pass; inspect the machine-readable gates."),
    ]
    return "\n\n".join(sections) + "\n"


def write_artifacts(artifact: Mapping[str, object], output_dir: Path | str = ROOT / "artifacts" / "p10_4") -> list[Path]:
    """Write the five required closure deliverables."""
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    json_path = target / "p10_4_vv_closure.json"
    evidence_path = target / "p10_4_evidence_matrix.csv"
    claim_path = target / "p10_4_claim_ledger.csv"
    limitations_path = target / "p10_4_limitations.md"
    summary_path = target / "p10_4_summary.md"
    json_path.write_text(json.dumps(artifact, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    _write_csv(evidence_path, EVIDENCE_FIELDS, artifact["evidence_matrix"])
    _write_csv(claim_path, CLAIM_FIELDS, artifact["claim_ledger"])
    limitations_path.write_text(
        "# P10.4 Limitation Ledger\n\nVerification success is not experimental validation.\n\n"
        + "\n".join(f"{index}. {item}" for index, item in enumerate(artifact["limitations"], 1))
        + "\n\nA shock-tube smoke test is not a formal shock convergence validation.\n",
        encoding="utf-8",
    )
    summary_path.write_text(_summary_markdown(artifact), encoding="utf-8")
    return [json_path, evidence_path, claim_path, limitations_path, summary_path]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--head-sha")
    parser.add_argument("--pytest-xml", type=Path, default=ROOT / "artifacts" / "p10_4" / "pytest.xml")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "artifacts" / "p10_4")
    args = parser.parse_args(argv)
    regression = parse_pytest_xml(args.pytest_xml)
    regression.update({
        "pytest_step_passed": os.environ.get("P10_4_PYTEST_OUTCOME", "success") == "success",
        "baseline_validation_passed": os.environ.get("P10_4_BASELINE_OUTCOME", "success") == "success",
    })
    artifact = assemble_artifact(resolve_head_sha(args.head_sha), regression)
    write_artifacts(artifact, args.output_dir)
    print(json.dumps({"head_sha": artifact["head_sha"], "gates": artifact["gates"], "all_passed": artifact["all_passed"]}, indent=2, allow_nan=False))
    return 0 if artifact["all_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
