"""Cheap contract tests for the P11.4 three-level numerical audit."""
import pytest

from cases.studies.p11_4_grid_convergence import GRID_LEVELS, relative_change


def test_grid_levels_form_three_successive_refinements() -> None:
    assert GRID_LEVELS == (20, 40, 80)
    assert GRID_LEVELS[1] == 2 * GRID_LEVELS[0]
    assert GRID_LEVELS[2] == 2 * GRID_LEVELS[1]


def test_relative_change_is_symmetric_in_difference_and_scaled_to_fine() -> None:
    assert relative_change(100.0, 110.0) == pytest.approx(10.0 / 110.0)
    assert relative_change(2.0, 2.0) == 0.0
