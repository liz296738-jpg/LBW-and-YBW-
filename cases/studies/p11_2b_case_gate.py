"""Evidence gate for formal P11.2B prescribed heat-release cases.

The gate is intentionally conservative. It does not create missing physics or
parameters; it only decides whether a candidate case carries enough traceable,
internally consistent evidence to be promoted from a development/surrogate
exercise to a formal source-backed P11.2B case.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from math import isfinite
from typing import Any


SUPPORTED_SHAPE_MODELS = {"eq8_asymmetric", "tabulated_line_heat"}


def _positive_number(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and isfinite(float(value))
        and float(value) > 0.0
    )


def _nonnegative_number(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and isfinite(float(value))
        and float(value) >= 0.0
    )


def _nonempty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _nonempty_locators(value: object) -> bool:
    return (
        isinstance(value, Sequence)
        and not isinstance(value, (str, bytes))
        and len(value) > 0
        and all(_nonempty_text(item) for item in value)
    )


def _validate_absolute_energy(
    energy: object,
    source_id: object,
    condition_id: object,
    blockers: list[str],
) -> None:
    """Validate a separate absolute energy scale for normalized shape models."""
    if not isinstance(energy, Mapping):
        blockers.append("missing absolute_energy")
        return

    if energy.get("source_id") != source_id:
        blockers.append("absolute_energy.source_id must match candidate source_id")
    if energy.get("operating_condition_id") != condition_id:
        blockers.append("absolute-energy operating condition does not match candidate")
    if not _nonempty_locators(energy.get("source_locators")):
        blockers.append("missing absolute_energy.source_locators")

    has_power = _positive_number(energy.get("total_heat_release_power_W"))
    has_enthalpy = _positive_number(energy.get("stagnation_enthalpy_increment_J_kg"))
    if has_power == has_enthalpy:
        blockers.append(
            "absolute_energy must provide exactly one of total power or stagnation-enthalpy increment"
        )
    if has_enthalpy and not _positive_number(energy.get("mass_flow_rate_kg_s")):
        blockers.append("stagnation-enthalpy route requires positive mass_flow_rate_kg_s")


def assess_formal_case_candidate(candidate: Mapping[str, Any]) -> dict[str, object]:
    """Return machine-readable readiness and blockers for one candidate case.

    Shape, energy addition, coordinate mapping, and operating condition must be
    traceable to the same declared case. Two evidence paths are supported:

    - ``eq8_asymmetric`` is a normalized shape and therefore requires a separate
      absolute-energy scale;
    - ``tabulated_line_heat`` contains absolute ``Qdot'(x)`` values in W/m and
      therefore already carries its energy scale. Supplying a second
      ``absolute_energy`` block is rejected to avoid two potentially
      inconsistent absolute scales.

    Passing this gate is permission to *run* a formal reduced-order case, not
    evidence that the model has been experimentally validated.
    """
    blockers: list[str] = []

    source_id = candidate.get("source_id")
    condition_id = candidate.get("operating_condition_id")
    if not _nonempty_text(source_id):
        blockers.append("missing source_id")
    if not _nonempty_text(condition_id):
        blockers.append("missing operating_condition_id")
    if not _nonempty_locators(candidate.get("source_locators")):
        blockers.append("missing source_locators")

    coordinate = candidate.get("coordinate_mapping")
    if not isinstance(coordinate, Mapping):
        blockers.append("missing coordinate_mapping")
    else:
        if coordinate.get("length_unit") != "m":
            blockers.append("coordinate_mapping.length_unit must be 'm'")
        if not _nonempty_text(coordinate.get("source_origin_description")):
            blockers.append("missing coordinate_mapping.source_origin_description")
        if not _nonempty_text(coordinate.get("solver_origin_description")):
            blockers.append("missing coordinate_mapping.solver_origin_description")
        if not _positive_number(coordinate.get("scale_to_solver_m")):
            blockers.append("coordinate_mapping.scale_to_solver_m must be positive")
        offset = coordinate.get("offset_m")
        if (
            not isinstance(offset, (int, float))
            or isinstance(offset, bool)
            or not isfinite(float(offset))
        ):
            blockers.append("coordinate_mapping.offset_m must be finite")
        if not _nonempty_locators(coordinate.get("source_locators")):
            blockers.append("missing coordinate_mapping.source_locators")

    shape = candidate.get("shape")
    model = None
    if not isinstance(shape, Mapping):
        blockers.append("missing shape")
    else:
        model = shape.get("model")
        if model not in SUPPORTED_SHAPE_MODELS:
            blockers.append("shape.model is not supported")
        if shape.get("source_id") != source_id:
            blockers.append("shape.source_id must match candidate source_id")
        if shape.get("operating_condition_id") != condition_id:
            blockers.append("shape operating condition does not match candidate")
        if not _nonempty_locators(shape.get("source_locators")):
            blockers.append("missing shape.source_locators")

        if model == "eq8_asymmetric":
            x_i = shape.get("x_initiation_m")
            x_m = shape.get("x_peak_m")
            x_c = shape.get("x_core_end_m")
            k = shape.get("asymmetry_length_m")
            if not all(
                _nonnegative_number(value) for value in (x_i, x_m, x_c, k)
            ):
                blockers.append(
                    "Eq. 8 shape parameters must be finite nonnegative metres"
                )
            elif not float(x_i) < float(x_m) < float(x_c):
                blockers.append(
                    "Eq. 8 requires x_initiation_m < x_peak_m < x_core_end_m"
                )
        elif model == "tabulated_line_heat":
            x_values = shape.get("x_m")
            q_values = shape.get("heat_release_rate_per_length_W_m")
            if not (
                isinstance(x_values, Sequence)
                and not isinstance(x_values, (str, bytes))
                and isinstance(q_values, Sequence)
                and not isinstance(q_values, (str, bytes))
                and len(x_values) == len(q_values)
                and len(x_values) >= 2
                and all(_nonnegative_number(value) for value in x_values)
                and all(_nonnegative_number(value) for value in q_values)
            ):
                blockers.append(
                    "tabulated line heat requires matching finite nonnegative x_m and W/m arrays"
                )
            elif any(
                float(b) <= float(a) for a, b in zip(x_values, x_values[1:])
            ):
                blockers.append("tabulated shape x_m must be strictly increasing")
            elif not any(float(value) > 0.0 for value in q_values):
                blockers.append(
                    "tabulated heat-release profile must contain positive heat addition"
                )

    if model == "eq8_asymmetric":
        _validate_absolute_energy(
            candidate.get("absolute_energy"), source_id, condition_id, blockers
        )
    elif model == "tabulated_line_heat":
        if candidate.get("absolute_energy") is not None:
            blockers.append(
                "tabulated_line_heat already contains the absolute energy scale; omit absolute_energy"
            )
    else:
        # Preserve an explicit missing-energy diagnostic when the shape itself
        # is absent or unsupported, without attempting to guess its semantics.
        if candidate.get("absolute_energy") is not None:
            blockers.append("absolute_energy cannot be assessed for unsupported shape.model")

    return {
        "formal_case_ready": not blockers,
        "blockers": blockers,
        "source_id": source_id,
        "operating_condition_id": condition_id,
        "energy_scale_path": (
            "separate_absolute_energy"
            if model == "eq8_asymmetric"
            else "absolute_tabulated_line_heat"
            if model == "tabulated_line_heat"
            else None
        ),
    }


def assess_ledger_formal_case_readiness(
    ledger: Mapping[str, Any],
) -> dict[str, object]:
    """Assess every declared candidate and preserve an explicit blocked state."""
    candidates = ledger.get("candidate_formal_cases", [])
    if not isinstance(candidates, list):
        raise ValueError("candidate_formal_cases must be a list")
    assessments = [assess_formal_case_candidate(candidate) for candidate in candidates]
    ready = [item for item in assessments if item["formal_case_ready"]]
    blockers = [] if candidates else ["no candidate_formal_cases declared"]
    if candidates and not ready:
        blockers.append("all declared formal-case candidates remain evidence-blocked")
    return {
        "formal_case_ready": bool(ready),
        "ready_candidate_count": len(ready),
        "candidate_count": len(candidates),
        "candidate_assessments": assessments,
        "blockers": blockers,
    }
