"""Guard the P11.2B evidence namespace against source-ID drift/collisions."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "cases" / "studies" / "data"
RECORDS = (
    DATA_DIR / "p11_2b_heat_release_model_source.json",
    DATA_DIR / "p11_2b_jin_liu_condition_discrepancy.json",
    DATA_DIR / "p11_2b_liu_model_b_geometry_source.json",
    DATA_DIR / "p11_2b_liu_angle_convention_source.json",
)


def _load_sources(path: Path) -> list[dict]:
    record = json.loads(path.read_text(encoding="utf-8"))
    sources = record.get("sources", [])
    if isinstance(sources, dict):
        values = list(sources.values())
    elif isinstance(sources, list):
        values = sources
    else:
        raise AssertionError(f"{path.name}: sources must be a list or object")
    return [value for value in values if isinstance(value, dict) and value.get("source_id")]


def _normalized_doi(source: dict) -> str | None:
    doi = source.get("doi")
    if doi is None:
        return None
    return str(doi).strip().lower().removeprefix("https://doi.org/").removeprefix("http://doi.org/")


def test_source_id_and_doi_registry_is_bijective_across_p11_2b_evidence() -> None:
    id_to_doi: dict[str, str] = {}
    doi_to_id: dict[str, str] = {}

    for path in RECORDS:
        for source in _load_sources(path):
            source_id = str(source["source_id"])
            doi = _normalized_doi(source)
            if doi is None:
                continue

            if source_id in id_to_doi:
                assert id_to_doi[source_id] == doi, (
                    f"{source_id} maps to both {id_to_doi[source_id]!r} and {doi!r}; "
                    "source IDs are global provenance identifiers, not file-local labels"
                )
            else:
                id_to_doi[source_id] = doi

            if doi in doi_to_id:
                assert doi_to_id[doi] == source_id, (
                    f"DOI {doi!r} is assigned to both {doi_to_id[doi]} and {source_id}; "
                    "one publication must retain one source ID"
                )
            else:
                doi_to_id[doi] = source_id

    assert id_to_doi["SRC07"] == "10.1016/j.ast.2019.105590"
    assert id_to_doi["SRC08"] == "10.1016/j.combustflame.2026.114876"
    assert id_to_doi["SRC09"] == "10.2514/6.2012-5833"
    assert id_to_doi["SRC10"] == "10.2514/1.j058391"
    assert id_to_doi["SRC11"] == "10.2514/6.2019-1681"
    assert id_to_doi["SRC12"] == "10.2514/6.2021-3536"
    assert id_to_doi["SRC13"] == "10.2514/1.j058204"
    assert id_to_doi["SRC14"] == "10.1155/2021/7525824"


def test_expected_p11_2b_source_ids_are_contiguous_through_src14() -> None:
    observed = {
        str(source["source_id"])
        for path in RECORDS
        for source in _load_sources(path)
        if str(source["source_id"]).startswith("SRC")
    }
    expected = {f"SRC{index:02d}" for index in range(7, 15)}
    assert expected.issubset(observed)
