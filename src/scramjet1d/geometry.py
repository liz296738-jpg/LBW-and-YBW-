"""Immutable quasi-one-dimensional cross-sectional area geometry."""

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray


def _validated_area_array(name: str, values: ArrayLike) -> NDArray[np.float64]:
    """Return an independent, read-only one-dimensional positive area array."""
    area = np.array(values, dtype=float, copy=True)
    if area.ndim != 1 or area.size < 1:
        raise ValueError(f"{name} must be a nonempty one-dimensional array")
    if not np.all(np.isfinite(area)) or not np.all(area > 0.0):
        raise ValueError(f"{name} must contain only finite, strictly positive areas")

    area.setflags(write=False)
    return area


@dataclass(frozen=True)
class AreaProfile:
    """Cell- and face-centred cross-sectional areas for a 1D mesh.

    ``cell_area`` has length ``N`` and ``face_area`` has length ``N + 1``.
    Both arrays are copied and exposed read-only so a profile is immutable.
    """

    cell_area: NDArray[np.float64]
    face_area: NDArray[np.float64]

    def __post_init__(self) -> None:
        cell_area = _validated_area_array("cell_area", self.cell_area)
        face_area = _validated_area_array("face_area", self.face_area)
        if face_area.size != cell_area.size + 1:
            raise ValueError("face_area must have exactly one more entry than cell_area")

        object.__setattr__(self, "cell_area", cell_area)
        object.__setattr__(self, "face_area", face_area)

    @property
    def num_cells(self) -> int:
        """Number of finite-volume cells represented by the profile."""
        return int(self.cell_area.size)


def constant_area_profile(num_cells: int, area: float = 1.0) -> AreaProfile:
    """Create a positive, constant-area profile for ``num_cells`` cells."""
    if (
        isinstance(num_cells, (bool, np.bool_))
        or not isinstance(num_cells, (int, np.integer))
        or num_cells <= 0
    ):
        raise ValueError("num_cells must be a positive integer")

    area_value = np.asarray(area, dtype=float)
    if area_value.ndim != 0 or not np.isfinite(area_value) or area_value <= 0.0:
        raise ValueError("area must be a finite, strictly positive scalar")

    count = int(num_cells)
    scalar_area = float(area_value)
    return AreaProfile(
        cell_area=np.full(count, scalar_area),
        face_area=np.full(count + 1, scalar_area),
    )


def area_change_per_cell(profile: AreaProfile) -> NDArray[np.float64]:
    """Return signed per-cell area changes, ``A_right - A_left``."""
    if not isinstance(profile, AreaProfile):
        raise TypeError("profile must be an AreaProfile")
    return profile.face_area[1:] - profile.face_area[:-1]
