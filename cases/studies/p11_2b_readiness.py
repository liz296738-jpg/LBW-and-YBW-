"""Build a machine-readable P11.2B formal-case readiness record."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from p11_2b_case_gate import assess_ledger_formal_case_readiness


ROOT = Path(__file__).resolve().parents[2]
SOURCE_LEDGER = ROOT / "cases" / "studies" / "data" / "p11_2b_heat_release_model_source.json"
DEFAULT_OUTPUT = ROOT / "artifacts" / "p11_2b" / "p11_2b_readiness.json"


def build_readiness_record(source_ledger: Path = SOURCE_LEDGER) -> dict[str, object]:
    """Assess the tracked evidence ledger without inventing missing inputs."""
    with source_ledger.open("r", encoding="utf-8") as stream:
        ledger = json.load(stream)
    assessment = assess_ledger_formal_case_readiness(ledger)
    return {
        "schema_version": 1,
        "stage": "P11.2B",
        "artifact_kind": "formal-case-readiness",
        "source_ledger": str(source_ledger.relative_to(ROOT)),
        "declared_project_status": ledger.get("project_decision", {}).get("formal_case_status"),
        **assessment,
    }


def write_readiness_record(record: dict[str, object], output: Path = DEFAULT_OUTPUT) -> Path:
    """Write canonical sorted JSON and return its path."""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(record, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return output


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-ledger", type=Path, default=SOURCE_LEDGER)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="return nonzero when no formal source-backed case is ready",
    )
    args = parser.parse_args(argv)

    record = build_readiness_record(args.source_ledger)
    write_readiness_record(record, args.output)
    print(json.dumps(record, indent=2, sort_keys=True, allow_nan=False))
    if args.require_ready and not record["formal_case_ready"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
