"""Regenerate data-driven SVG figures for the canonical project paper.

The plotted numerical values are loaded only from frozen acceptance records.
This script intentionally does not run CFD or create new scientific evidence.

Usage:
    python tools/build_paper_figures.py
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
PAPER_ASSETS = ROOT / "paper" / "assets"
GRID_RECORD = ROOT / "cases" / "studies" / "data" / "p11_4_grid_convergence_acceptance.json"
P12_RESPONSE = ROOT / "cases" / "studies" / "data" / "p12_project_defined_response_sweep_acceptance.json"
P12_CONTINUATION = ROOT / "cases" / "studies" / "data" / "p12_thermal_throat_continuation_acceptance.json"
P12_GRID = ROOT / "cases" / "studies" / "data" / "p12_thermal_throat_grid_sensitivity_acceptance.json"
P13_ACCEPTANCE = ROOT / "cases" / "studies" / "data" / "p13_teacher_mixing_constant_sensitivity_acceptance.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def paper_figure_series() -> dict[str, dict[str, object]]:
    """Return the accepted numerical series used by paper Figures 2--5."""

    grid = _load(GRID_RECORD)
    response = _load(P12_RESPONSE)
    continuation = _load(P12_CONTINUATION)
    thermal_grid = _load(P12_GRID)
    p13 = _load(P13_ACCEPTANCE)

    fig2 = {
        "x": [row["cells"] for row in grid["levels"]],
        "y": [row["min_mach"] for row in grid["levels"]],
        "title": "P11.4 three-level grid trend",
        "x_label": "Number of cells",
        "y_label": "Minimum Mach number",
        "reference_y": None,
        "sources": [GRID_RECORD.relative_to(ROOT).as_posix()],
    }

    response_points = {
        float(row["equivalence_ratio"]): row
        for row in response["points"]
        if row["status"] == "CONVERGED"
    }
    continuation_points = {
        float(row["equivalence_ratio"]): row
        for row in continuation["points"]
        if row["status"] == "CONVERGED"
    }
    phi_values = [0.10, 0.20, 0.22, 0.24]
    min_mach_values = []
    for phi in phi_values:
        row = continuation_points.get(phi, response_points.get(phi))
        if row is None:
            raise ValueError(f"accepted P12 evidence missing converged phi={phi:g}")
        min_mach_values.append(float(row["min_mach"]))

    # The overlapping phi=0.20 point must be numerically identical across the
    # frozen response and continuation records.
    if 0.20 in response_points and 0.20 in continuation_points:
        if float(response_points[0.20]["min_mach"]) != float(
            continuation_points[0.20]["min_mach"]
        ):
            raise ValueError("P12 phi=0.20 min-Mach evidence drifted between records")

    fig3 = {
        "x": phi_values,
        "y": min_mach_values,
        "title": "Accepted P12 response / continuation points",
        "x_label": "Equivalence ratio, phi",
        "y_label": "Minimum Mach number",
        "reference_y": 1.0,
        "sources": [
            P12_RESPONSE.relative_to(ROOT).as_posix(),
            P12_CONTINUATION.relative_to(ROOT).as_posix(),
        ],
    }

    phi_024 = thermal_grid["target_points"]["phi_0.24"]
    fig4 = {
        "x": [row["cells"] for row in phi_024],
        "y": [row["min_mach"] for row in phi_024],
        "title": "P12 phi=0.24 grid sensitivity",
        "x_label": "Number of cells",
        "y_label": "Minimum Mach number",
        "reference_y": 1.0,
        "sources": [P12_GRID.relative_to(ROOT).as_posix()],
    }

    p13_40 = sorted(
        (row for row in p13["points"] if row["cells"] == 40),
        key=lambda row: float(row["mixing_C_m"]),
    )
    fig5 = {
        "x": [float(row["mixing_C_m"]) for row in p13_40],
        "y": [float(row["max_pressure_Pa"]) / 1000.0 for row in p13_40],
        "title": "P13 accepted C_m sensitivity (40-cell max pressure)",
        "x_label": "Mixing constant, C_m",
        "y_label": "Maximum static pressure (kPa)",
        "reference_y": None,
        "sources": [P13_ACCEPTANCE.relative_to(ROOT).as_posix()],
    }

    return {
        "fig2_grid_min_mach.svg": fig2,
        "fig3_phi_min_mach.svg": fig3,
        "fig4_phi024_grid.svg": fig4,
        "fig5_p13_cm_max_pressure.svg": fig5,
    }


def _fmt(value: float) -> str:
    return f"{value:.6g}"


def render_line_svg(
    x: Iterable[float],
    y: Iterable[float],
    *,
    title: str,
    x_label: str,
    y_label: str,
    reference_y: float | None,
    sources: Iterable[str],
) -> str:
    xs = [float(v) for v in x]
    ys = [float(v) for v in y]
    if len(xs) != len(ys) or len(xs) < 2:
        raise ValueError("line chart requires at least two paired points")

    width, height = 800.0, 500.0
    left, right, top, bottom = 90.0, 30.0, 65.0, 70.0
    plot_w = width - left - right
    plot_h = height - top - bottom

    xmin, xmax = min(xs), max(xs)
    ymin_data, ymax_data = min(ys), max(ys)
    if reference_y is not None:
        ymin_data = min(ymin_data, reference_y)
        ymax_data = max(ymax_data, reference_y)
    yspan = max(ymax_data - ymin_data, 1.0e-9)
    ymin = ymin_data - 0.08 * yspan
    ymax = ymax_data + 0.08 * yspan

    def sx(v: float) -> float:
        return left + (v - xmin) / (xmax - xmin) * plot_w

    def sy(v: float) -> float:
        return top + (ymax - v) / (ymax - ymin) * plot_h

    y_ticks = [ymin + i * (ymax - ymin) / 4 for i in range(5)]
    point_string = " ".join(f"{sx(a):.1f},{sy(b):.1f}" for a, b in zip(xs, ys))
    source_text = " | ".join(sources)
    raw_points = "; ".join(f"({_fmt(a)},{_fmt(b)})" for a, b in zip(xs, ys))

    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="500" viewBox="0 0 800 500">',
        '<style>text{font-family:Arial,sans-serif;fill:#111}.g{stroke:#ddd}.a{stroke:#111}.l{fill:none;stroke:#333;stroke-width:3}.p{fill:#fff;stroke:#333;stroke-width:3}.r{stroke:#777;stroke-width:2;stroke-dasharray:8 6}</style>',
        f"<desc>Generated from frozen acceptance evidence: {source_text}; plotted data: {raw_points}</desc>",
        f'<text x="400" y="32" text-anchor="middle" font-size="24" font-weight="bold">{title}</text>',
    ]
    for tick in y_ticks:
        yy = sy(tick)
        lines.append(
            f'<line x1="{left:g}" y1="{yy:.1f}" x2="{width-right:g}" y2="{yy:.1f}" class="g"/>'
            f'<text x="{left-12:g}" y="{yy+5:.1f}" text-anchor="end" font-size="15">{tick:.3f}</text>'
        )
    for value in xs:
        xx = sx(value)
        label = f"{value:g}"
        lines.append(
            f'<line x1="{xx:.1f}" y1="{top:g}" x2="{xx:.1f}" y2="{height-bottom:g}" class="g"/>'
            f'<text x="{xx:.1f}" y="{height-bottom+27:g}" text-anchor="middle" font-size="15">{label}</text>'
        )
    lines.extend(
        [
            f'<line x1="{left:g}" y1="{top:g}" x2="{left:g}" y2="{height-bottom:g}" class="a"/>',
            f'<line x1="{left:g}" y1="{height-bottom:g}" x2="{width-right:g}" y2="{height-bottom:g}" class="a"/>',
        ]
    )
    if reference_y is not None and ymin <= reference_y <= ymax:
        yy = sy(reference_y)
        lines.append(
            f'<line x1="{left:g}" y1="{yy:.1f}" x2="{width-right:g}" y2="{yy:.1f}" class="r"/>'
        )
    lines.append(f'<polyline points="{point_string}" class="l"/>')
    for a, b in zip(xs, ys):
        lines.append(f'<circle cx="{sx(a):.1f}" cy="{sy(b):.1f}" r="6" class="p"/>')
    lines.extend(
        [
            f'<text x="{left+plot_w/2:.1f}" y="482" text-anchor="middle" font-size="18">{x_label}</text>',
            f'<text x="22" y="{top+plot_h/2:.1f}" text-anchor="middle" font-size="18" transform="rotate(-90 22 {top+plot_h/2:.1f})">{y_label}</text>',
            "</svg>",
        ]
    )
    return "\n".join(lines) + "\n"


def build_figures(output_dir: Path = PAPER_ASSETS) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for filename, spec in paper_figure_series().items():
        svg = render_line_svg(
            spec["x"],
            spec["y"],
            title=str(spec["title"]),
            x_label=str(spec["x_label"]),
            y_label=str(spec["y_label"]),
            reference_y=spec["reference_y"],
            sources=spec["sources"],
        )
        path = output_dir / filename
        path.write_text(svg, encoding="utf-8")
        written.append(path)
    return written


if __name__ == "__main__":
    for path in build_figures():
        print(path.relative_to(ROOT))
