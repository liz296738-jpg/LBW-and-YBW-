"""Internal-consistency audit for the source-reported Cao Case 2 inlet table.

The audit does not correct, tune, or replace any teacher/Cao source value. It
only evaluates how the simultaneously reported p/rho/T/Mach/u/gamma/composition
compare with the repository's frozen ideal-mixture thermochemistry closure.
"""
from __future__ import annotations

import json
from math import sqrt
from pathlib import Path

from cases.studies.teacher_thermochemistry_database import build_species_database
from scramjet1d.thermochemistry import mixture_thermo_state


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = ROOT / "cases" / "studies" / "data" / "teacher_cao_case2_source.json"


def _relative_difference(calculated: float, reported: float) -> float:
    return (float(calculated) - float(reported)) / float(reported)


def run_consistency_audit() -> dict[str, object]:
    record = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    table = record["table_2_2_isolator_entrance"]
    species = build_species_database()

    T = float(table["temperature_K"])
    p = float(table["pressure_Pa"])
    rho = float(table["density_kg_per_m3"])
    mach = float(table["Mach"])
    u = float(table["axial_velocity_m_per_s"])
    reported_gamma = float(table["reported_heat_capacity_ratio"])
    composition = {name: float(value) for name, value in table["mass_fractions"].items()}

    thermo = mixture_thermo_state(T, composition, species)
    R_mix = thermo.gas_constant_J_per_kg_K
    gamma_mix = thermo.gamma

    pressure_from_reported_rho = rho * R_mix * T
    density_from_reported_pressure = p / (R_mix * T)

    sound_speed_source_thermo = sqrt(gamma_mix * R_mix * T)
    velocity_from_reported_mach_source_thermo = mach * sound_speed_source_thermo
    mach_from_reported_velocity_source_thermo = u / sound_speed_source_thermo

    sound_speed_reported_gamma = sqrt(reported_gamma * R_mix * T)
    velocity_from_reported_mach_reported_gamma = mach * sound_speed_reported_gamma
    mach_from_reported_velocity_reported_gamma = u / sound_speed_reported_gamma

    return {
        "schema_version": 1,
        "classification": "CAO_CASE2_SOURCE_TABLE_INTERNAL_CONSISTENCY_AUDIT",
        "source_values_modified": False,
        "formal_reproduction_promoted": False,
        "source_record": str(SOURCE_PATH.relative_to(ROOT)),
        "thermochemistry_source": (
            "frozen GRI-Mech 3.0 core species database used by the teacher-reference "
            "variable-thermochemistry path"
        ),
        "reported": {
            "Mach": mach,
            "density_kg_per_m3": rho,
            "pressure_Pa": p,
            "temperature_K": T,
            "axial_velocity_m_per_s": u,
            "heat_capacity_ratio": reported_gamma,
            "mass_fractions": composition,
        },
        "derived_from_frozen_mixture_thermochemistry": {
            "gas_constant_J_per_kg_K": R_mix,
            "cp_J_per_kg_K": thermo.cp_J_per_kg_K,
            "gamma_at_reported_temperature": gamma_mix,
            "pressure_from_reported_rho_T_Pa": pressure_from_reported_rho,
            "pressure_relative_difference_vs_reported": _relative_difference(
                pressure_from_reported_rho, p
            ),
            "density_from_reported_p_T_kg_per_m3": density_from_reported_pressure,
            "density_relative_difference_vs_reported": _relative_difference(
                density_from_reported_pressure, rho
            ),
            "velocity_from_reported_Mach_m_per_s": velocity_from_reported_mach_source_thermo,
            "velocity_relative_difference_vs_reported": _relative_difference(
                velocity_from_reported_mach_source_thermo, u
            ),
            "Mach_from_reported_velocity": mach_from_reported_velocity_source_thermo,
        },
        "derived_using_reported_gamma_with_frozen_mixture_R": {
            "velocity_from_reported_Mach_m_per_s": velocity_from_reported_mach_reported_gamma,
            "velocity_relative_difference_vs_reported": _relative_difference(
                velocity_from_reported_mach_reported_gamma, u
            ),
            "Mach_from_reported_velocity": mach_from_reported_velocity_reported_gamma,
        },
        "interpretation": (
            "The source-reported Table 2-2 fields are preserved exactly as evidence. "
            "They are not exactly thermodynamically closed under the repository's frozen "
            "ideal-mixture/GRI thermochemistry when treated as simultaneous exact constraints. "
            "This audit therefore forbids silently tuning R, gamma, p, rho, T, Mach, or u "
            "merely to force exact agreement. Formal Cao Case 2 reproduction remains blocked "
            "by the separately documented spatial-input gaps."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run_consistency_audit(), indent=2, sort_keys=True))
