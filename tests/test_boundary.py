"""Tests for transmissive ghost-cell padding along the cell axis."""

import numpy as np
import pytest

import scramjet1d.boundary as boundary


def test_three_cells_are_padded_as_a_a_b_c_c() -> None:
    """Each exterior cell copies the adjacent endpoint without reordering."""
    U = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    expected = [[1, 2, 3], [1, 2, 3], [4, 5, 6], [7, 8, 9], [7, 8, 9]]

    result = boundary.transmissive_ghost_cells(U)

    assert result.dtype == np.float64
    np.testing.assert_array_equal(result, expected)


def test_multiple_batch_axes_are_preserved() -> None:
    """Independent batches receive their own endpoint copies on axis -2."""
    U = np.array([
        [[[1, 2, 3], [4, 5, 6]], [[7, 8, 9], [10, 11, 12]]],
        [[[13, 14, 15], [16, 17, 18]], [[19, 20, 21], [22, 23, 24]]],
    ])
    expected = np.array([
        [
            [[1, 2, 3], [1, 2, 3], [4, 5, 6], [4, 5, 6]],
            [[7, 8, 9], [7, 8, 9], [10, 11, 12], [10, 11, 12]],
        ],
        [
            [[13, 14, 15], [13, 14, 15], [16, 17, 18], [16, 17, 18]],
            [[19, 20, 21], [19, 20, 21], [22, 23, 24], [22, 23, 24]],
        ],
    ])

    result = boundary.transmissive_ghost_cells(U)

    assert result.shape == (2, 2, 4, 3)
    np.testing.assert_array_equal(result, expected)


def test_single_cell_produces_three_equal_cells() -> None:
    """A one-cell domain supports both endpoint copies."""
    np.testing.assert_array_equal(
        boundary.transmissive_ghost_cells([[2.0, -3.0, 8.0]]),
        [[2.0, -3.0, 8.0], [2.0, -3.0, 8.0], [2.0, -3.0, 8.0]],
    )


def test_padding_does_not_mutate_or_alias_input() -> None:
    """Padding owns its data, including independent ghost and interior cells."""
    U = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
    original = U.copy()

    result = boundary.transmissive_ghost_cells(U)

    np.testing.assert_array_equal(U, original)
    assert not np.shares_memory(result, U)
    result[0, 0] = 99.0
    assert result[1, 0] == 1.0
    np.testing.assert_array_equal(U, original)
    U[-1, -1] = 100.0
    np.testing.assert_array_equal(result[-1], [4.0, 5.0, 6.0])


def test_finite_signed_states_are_copied_without_physical_validation() -> None:
    """This array operation leaves density and pressure validation to the RHS."""
    np.testing.assert_array_equal(
        boundary.transmissive_ghost_cells([[-1.0, 0.0, -3.0], [0.0, -2.0, 0.0]]),
        [[-1.0, 0.0, -3.0], [-1.0, 0.0, -3.0], [0.0, -2.0, 0.0], [0.0, -2.0, 0.0]],
    )


@pytest.mark.parametrize(
    "U",
    [
        1.0,
        [1.0, 2.0, 3.0],
        np.ones((2, 2)),
        np.ones((2, 4)),
        np.ones((1, 2, 4)),
        np.empty((0, 3)),
        np.empty((2, 0, 3)),
    ],
)
def test_rejects_invalid_state_dimensions(U: object) -> None:
    """A state array needs at least one cell and exactly three components."""
    with pytest.raises(ValueError):
        boundary.transmissive_ghost_cells(U)


@pytest.mark.parametrize("bad_value", [np.nan, np.inf, -np.inf])
def test_rejects_nonfinite_values(bad_value: float) -> None:
    """Nonfinite entries are rejected before boundary copying."""
    U = np.ones((2, 3))
    U[1, 1] = bad_value
    with pytest.raises(ValueError):
        boundary.transmissive_ghost_cells(U)
