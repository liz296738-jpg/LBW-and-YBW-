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
SUPPORTED_FRICTION_MODES = {"disabled_source_backed", "darcy_scalar_source_backed"}


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


def _resolved_cross_source_link(candidate: Mapping[str, Any], blockers: list[str]) -> set[str]:
    """Return explicitly authorized component sources for a resolved cross-source chain.

    A different paper may legitimately provide a closure fitted to an identified
    experiment (for example Jin fitting a Liu experiment), but arbitrary source
    mixing remains prohibited. Cross-source use is therefore allowed only when
    the candidate carries an explicit, traceable, *resolved* identity link.
    """
    link = candidate.get("cross_source_link")
    if link is None:
        return set()
    if not isinstance(link, Mapping):
        blockers.append("cross_source_link must be a mapping")
        return set()
    if link.get("status") != "RESOLVED":
        blockers.append("cross_source_link.status must be 'RESOLVED' before cross-source promotion")
        return set()
    if link.get("operating_condition_id") != candidate.get("operating_condition_id"):
        blockers.append("cross_source_link operating condition does not match candidate")
    if not _nonempty_locators(link.get("source_locators")):
        blockers.append("missing cross_source_link.source_locators")
    if not _nonempty_text(link.get("link_description")):
        blockers.append("missing cross_source_link.link_description")

    source_ids = link.get("source_ids")
    if not (
        isinstance(source_ids, Sequence)
        and not isinstance(source_ids, (str, bytes))
        and len(source_ids) >= 2
        and all(_nonempty_text(item) for item in source_ids)
    ):
        blockers.append("cross_source_link.source_ids must list at least two nonempty source IDs")
        return set()
    allowed = {str(item) for item in source_ids}
    if candidate.get("source_id") not in allowed:
        blockers.append("candidate source_id must be included in cross_source_link.source_ids")
    return allowed


def _validate_component_identity(
    component_name: str,
    component: Mapping[str, Any],
    source_id: object,
    condition_id: object,
    allowed_cross_sources: set[str],
    blockers: list[str],
) -> None:
    component_source = component.get("source_id")
    if component_source != source_id and component_source not in allowed_cross_sources:
        blockers.append(
            f"{component_name}.source_id must match candidate source_id or be authorized by a resolved cross_source_link"
        )
    if component.get("operating_condition_id") != condition_id:
        blockers.append(f"{component_name} operating condition does not match candidate")
    if not _nonempty_locators(component.get("source_locators")):
        blockers.append(f"missing {component_name}.source_locators")


def _validate_geometry(
    geometry: object,
    source_id: object,
    condition_id: object,
    allowed_cross_sources: set[str],
    blockers: list[str],
) -> None:
    if not isinstance(geometry, Mapping):
        blockers.append("missing geometry")
        return
    _validate_component_identity(
        "geometry", geometry, source_id, condition_id, allowed_cross_sources, blockers
    )
    if geometry.get("area_profile_status") != "FROZEN":
        blockers.append("geometry.area_profile_status must be 'FROZEN'")
    if not _positive_number(geometry.get("domain_length_m")):
        blockers.append("geometry.domain_length_m must be positive")
    if not _nonempty_text(geometry.get("area_model_description")):
        blockers.append("missing geometry.area_model_description")


def _validate_inlet_state(
    inlet: object,
    source_id: object,
    condition_id: object,
    allowed_cross_sources: set[str],
    blockers: list[str],
) -> None:
    if not isinstance(inlet, Mapping):
        blockers.append("missing inlet_state")
        return
    _validate_component_identity(
        "inlet_state", inlet, source_id, condition_id, allowed_cross_sources, blockers
    )
    if inlet.get("boundary_type") != "supersonic-inflow":
        blockers.append("inlet_state.boundary_type must be 'supersonic-inflow' for the current formal P11.2B path")
    for key in ("rho_kg_m3", "u_m_s", "p_Pa"):
        if not _positive_number(inlet.get(key)):
            blockers.append(f"inlet_state.{key} must be positive")


def _validate_wall_friction(
    friction: object,
    source_id: object,
    condition_id: object,
    allowed_cross_sources: set[str],
    blockers: list[str],
) -> None:
    if not isinstance(friction, Mapping):
        blockers.append("missing wall_friction")
        return
    _validate_component_identity(
        "wall_friction", friction, source_id, condition_id, allowed_cross_sources, blockers
    )
    mode = friction.get("mode")
    if mode not in SUPPORTED_FRICTION_MODES:
        blockers.append("wall_friction.mode is not supported")
        return
    if not _nonempty_text(friction.get("convention")):
        blockers.append("missing wall_friction.convention")
    if mode == "disabled_source_backed":
        if friction.get("darcy_friction_factor") not in (0, 0.0):
            blockers.append("disabled_source_backed wall friction requires darcy_friction_factor=0")
    elif mode == "darcy_scalar_source_backed":
        if not _nonnegative_number(friction.get("darcy_friction_factor")):
            blockers.append("wall_friction.darcy_friction_factor must be finite and nonnegative")
        if not _positive_number(friction.get("hydraulic_diameter_m")):
            blockers.append("wall_friction.hydraulic_diameter_m must be positive")
        if friction.get("convention") != "Darcy":
            blockers.append("darcy_scalar_source_backed requires wall_friction.convention='Darcy'")


def _validate_absolute_energy(
    energy: object,
    source_id: object,
    condition_id: object,
    allowed_cross_sources: set[str],
    blockers: list[str],
) -> None:
    """Validate a separate absolute energy scale for normalized shape models."""
    if not isinstance(energy, Mapping):
        blockers.append("missing absolute_energy")
        return

    _validate_component_identity(
        "absolute_energy", energy, source_id, condition_id, allowed_cross_sources, blockers
    )
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

    Passing this gate means only that the case has enough traceable inputs to be
    *run* as a formal reduced-order P11.2B case. It is not evidence that the
    result is converged, experimentally validated, or applicable outside the
    assumptions of the cited source.
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

    allowed_cross_sources = _resolved_cross_source_link(candidate, blockers)

    coordinate = candidate.get("coordinate_mapping")
    if not isinstance(coordinate, Mapping):
        blockers.append("missing coordinate_mapping")
    else:
        _validate_component_identity(
            "coordinate_mapping",
            coordinate,
            source_id,
            condition_id,
            allowed_cross_sources,
            blockers,
        )
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

    _validate_geometry(
        candidate.get("geometry"), source_id, condition_id, allowed_cross_sources, blockers
    )
    _validate_inlet_state(
        candidate.get("inlet_state"), source_id, condition_id, allowed_cross_sources, blockers
    )
    _validate_wall_friction(
        candidate.get("wall_friction"), source_id, condition_id, allowed_cross_sources, blockers
    )

    shape = candidate.get("shape")
    model = None
    if not isinstance(shape, Mapping):
        blockers.append("missing shape")
    else:
        model = shape.get("model")
        if model not in SUPPORTED_SHAPE_MODELS:
            blockers.append("shape.model is not supported")
        _validate_component_identity(
            "shape", shape, source_id, condition_id, allowed_cross_sources, blockers
        )

        if model == "eq8_asymmetric":
            x_i = shape.get("x_initiation_m")
            x_m = shape.get("x_peak_m")
            x_c = shape.get("x_core_end_m")
            k = shape.get("asymmetry_length_m")
            if not all(_nonnegative_number(value) for value in (x_i, x_m, x_c, k)):
                blockers.append("Eq. 8 shape parameters must be finite nonnegative metres")
            elif not float(x_i) < float(x_m) < float(x_c):
                blockers.append("Eq. 8 requires x_initiation_m < x_peak_m < x_core_end_m")
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
            elif any(float(b) <= float(a) for a, b in zip(x_values, x_values[1:])):
                blockers.append("tabulated shape x_m must be strictly increasing")
            elif not any(float(value) > 0.0 for value in q_values):
                blockers.append("tabulated heat-release profile must contain positive heat addition")

    if model == "eq8_asymmetric":
        _validate_absolute_energy(
            candidate.get("absolute_energy"),
            source_id,
            condition_id,
            allowed_cross_sources,
            blockers,
        )
    elif model == "tabulated_line_heat":
        if candidate.get("absolute_energy") is not None:
            blockers.append(
                "tabulated_line_heat already contains the absolute energy scale; omit absolute_energy"
            )
    elif candidate.get("absolute_energy") is not None:
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
        "cross_source_authorized": bool(allowed_cross_sources),
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
