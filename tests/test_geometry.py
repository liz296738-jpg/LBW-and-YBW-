"""Tests for immutable quasi-1D cross-sectional area geometry."""

import numpy as np
import pytest

import scramjet1d.geometry as geometry


def test_valid_profile_copies_immutable_cell_and_face_areas() -> None:
    """A profile retains independent, read-only SI area arrays."""
    cell = np.array([1.0, 1.1, 1.2])
    face = np.array([0.95, 1.05, 1.15, 1.25])
    profile = geometry.AreaProfile(cell, face)
    cell[0] = 999.0
    face[0] = 999.0

    assert profile.num_cells == 3
    assert profile.cell_area.shape == (3,)
    assert profile.face_area.shape == (4,)
    assert profile.cell_area.dtype == np.float64
    assert profile.face_area.dtype == np.float64
    assert profile.cell_area[0] == 1.0
    assert profile.face_area[0] == 0.95
    with pytest.raises(ValueError):
        profile.cell_area[0] = 2.0
    with pytest.raises(ValueError):
        profile.face_area[0] = 2.0


@pytest.mark.parametrize("bad", [0.0, -1.0, np.nan, np.inf])
def test_profile_rejects_invalid_cell_or_face_areas(bad: float) -> None:
    """Every cell and face area must be finite and strictly positive."""
    with pytest.raises(ValueError):
        geometry.AreaProfile([1.0, bad], [1.0, 1.0, 1.0])
    with pytest.raises(ValueError):
        geometry.AreaProfile([1.0, 1.0], [1.0, bad, 1.0])


@pytest.mark.parametrize(
    "cell, face",
    [
        (1.0, [1.0, 1.0]),
        ([[1.0]], [1.0, 1.0]),
        ([1.0], [[1.0, 1.0]]),
        ([], [1.0]),
        ([1.0], []),
        ([1.0, 1.0, 1.0], [1.0, 1.0, 1.0]),
    ],
)
def test_profile_rejects_invalid_dimensions_and_lengths(cell: object, face: object) -> None:
    """Profiles require one-dimensional cell N and face N+1 arrays."""
    with pytest.raises(ValueError):
        geometry.AreaProfile(cell, face)


def test_constant_area_profile_and_discrete_area_change() -> None:
    """Constant geometry preserves separate N and N+1 representations and zero delta A."""
    profile = geometry.constant_area_profile(5, 0.02)

    assert profile.num_cells == 5
    np.testing.assert_allclose(profile.cell_area, [0.02] * 5)
    np.testing.assert_allclose(profile.face_area, [0.02] * 6)
    np.testing.assert_allclose(geometry.area_change_per_cell(profile), [0.0] * 5)


def test_area_change_retains_known_and_converging_signs() -> None:
    """The utility returns right face area minus left face area without absolute value."""
    increasing = geometry.AreaProfile([1.5, 3.0, 5.5], [1.0, 2.0, 4.0, 7.0])
    converging = geometry.AreaProfile([3.5, 2.5, 1.5], [4.0, 3.0, 2.0, 1.0])

    np.testing.assert_allclose(geometry.area_change_per_cell(increasing), [1.0, 2.0, 3.0])
    np.testing.assert_allclose(geometry.area_change_per_cell(converging), [-1.0, -1.0, -1.0])


@pytest.mark.parametrize("num_cells", [0, -1, True, 3.5, "3"])
def test_constant_profile_rejects_invalid_cell_count(num_cells: object) -> None:
    with pytest.raises(ValueError):
        geometry.constant_area_profile(num_cells)


@pytest.mark.parametrize("area", [0.0, -0.1, np.nan, np.inf, [1.0]])
def test_constant_profile_rejects_invalid_area(area: object) -> None:
    with pytest.raises(ValueError):
        geometry.constant_area_profile(3, area)
