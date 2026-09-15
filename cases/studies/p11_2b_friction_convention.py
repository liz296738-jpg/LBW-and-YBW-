"""P11.2B Jin/Shapiro wall-friction convention mapping.

This module contains only the coefficient-convention transformation justified by
Jin et al. (2026) Eqs. (9)-(10), their explicit citation of Shapiro [51], and
Shapiro's definition of the duct friction coefficient as wall shear divided by
dynamic head.  It does not choose a numerical Fig. 14 friction coefficient.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from numpy.typing import ArrayLike, NDArray


ROOT = Path(__file__).resolve().parents[2]
SOURCE_RECORD = (
    ROOT
    / "cases"
    / "studies"
    / "data"
    / "p11_2b_jin_friction_convention_source.json"
)


def load_friction_convention_source(path: Path = SOURCE_RECORD) -> dict:
    """Load the tracked friction-convention evidence record."""
    with path.open("r", encoding="utf-8") as stream:
        record = json.load(stream)
    if record.get("schema_version") != 1:
        raise ValueError("unsupported friction-convention schema_version")
    if record.get("record_kind") != "validation-friction-convention":
        raise ValueError("unexpected friction-convention record_kind")
    if record.get("candidate_id") != "JIN-LIU-MODEL-B-VALIDATION":
        raise ValueError("unexpected friction-convention candidate_id")
    if record.get("derived_mapping", {}).get("result") != "f_D = 4 Cf":
        raise ValueError("tracked friction-convention mapping is not f_D = 4 Cf")
    if record.get("derived_mapping", {}).get("status") != "RESOLVED":
        raise ValueError("tracked friction-convention mapping is not resolved")
    return record


def jin_cf_to_repository_darcy(
    wall_friction_coefficient: ArrayLike,
) -> NDArray[np.float64]:
    """Convert Jin/Shapiro ``Cf`` to repository Darcy friction factor.

    Jin Eqs. (9)-(10) use the Shapiro friction parameter ``4 Cf dx / D``.
    Shapiro defines ``Cf = tau_w / (0.5 rho u^2)``.  The repository wall
    source is written with Darcy ``f_D`` as
    ``-0.5 f_D rho u |u| / D_h``.  Equating the same wall shear force gives
    ``f_D = 4 Cf``.

    The function accepts scalar or array-like nonnegative finite values.  It
    performs a convention conversion only; it does not estimate the missing
    Fig. 14 numerical ``Cf``.
    """
    cf = np.asarray(wall_friction_coefficient, dtype=float)
    if not np.all(np.isfinite(cf) & (cf >= 0.0)):
        raise ValueError("wall_friction_coefficient must be finite and nonnegative")
    result = 4.0 * cf
    result.setflags(write=False)
    return result


def repository_darcy_to_jin_cf(
    darcy_friction_factor: ArrayLike,
) -> NDArray[np.float64]:
    """Return the inverse evidence-backed convention transform ``Cf=f_D/4``."""
    darcy = np.asarray(darcy_friction_factor, dtype=float)
    if not np.all(np.isfinite(darcy) & (darcy >= 0.0)):
        raise ValueError("darcy_friction_factor must be finite and nonnegative")
    result = 0.25 * darcy
    result.setflags(write=False)
    return result
