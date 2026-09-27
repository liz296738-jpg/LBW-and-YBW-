"""Tests for data-driven canonical-paper figures."""
from __future__ import annotations

from pathlib import Path

import pytest

from tools.build_paper_figures import build_figures, paper_figure_series


def test_paper_figure_series_are_loaded_from_frozen_acceptance_records() -> None:
    series = paper_figure_series()

    fig2 = series["fig2_grid_min_mach.svg"]
    assert fig2["x"] == [20, 40, 80]
    assert fig2["y"] == [
        1.27140884274981,
        1.2634394882103626,
        1.2568481737088568,
    ]

    fig3 = series["fig3_phi_min_mach.svg"]
    assert fig3["x"] == [0.10, 0.20, 0.22, 0.24]
    assert fig3["y"] == [
        1.6919033208821357,
        1.27140884274981,
        1.176579560375719,
        1.0766129859616784,
    ]
    assert fig3["reference_y"] == 1.0

    fig4 = series["fig4_phi024_grid.svg"]
    assert fig4["x"] == [20, 40, 80]
    assert fig4["y"] == [
        1.0766129859616784,
        1.04462708512229,
        1.0126683915382297,
    ]
    assert fig4["reference_y"] == 1.0

    fig5 = series["fig5_p13_cm_max_pressure.svg"]
    assert fig5["x"] == [25.0, 30.0, 42.5, 60.0]
    assert fig5["y"] == pytest.approx([
        118.79552373494236,
        115.4742519502044,
        93.12907393130471,
        77.75800789870585,
    ], rel=1.0e-15, abs=0.0)
    assert fig5["reference_y"] is None
    assert fig5["sources"] == [
        "cases/studies/data/p13_teacher_mixing_constant_sensitivity_acceptance.json"
    ]


def test_paper_figure_builder_writes_traceable_svg(tmp_path: Path) -> None:
    paths = build_figures(tmp_path)

    assert {path.name for path in paths} == {
        "fig2_grid_min_mach.svg",
        "fig3_phi_min_mach.svg",
        "fig4_phi024_grid.svg",
        "fig5_p13_cm_max_pressure.svg",
    }
    for path in paths:
        svg = path.read_text(encoding="utf-8")
        assert svg.startswith("<svg")
        assert "Generated from frozen acceptance evidence:" in svg
        assert "plotted data:" in svg
        assert "<polyline" in svg
