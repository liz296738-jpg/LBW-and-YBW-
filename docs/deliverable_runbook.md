# Course Deliverable Runbook

This runbook freezes copy-paste commands for the accepted project-defined H2 baseline and P12 response study. These commands reproduce project-defined implementation/V&V evidence; they do **not** promote the runs to Cao Case 2 source reproduction.

## Environment

From the repository root, using the repository-pinned Python 3.11.11 (`.python-version`):

```bash
python --version  # expected: Python 3.11.11
python -m pip install -e ".[dev]"
```
Direct numerical/runtime dependencies are pinned in `pyproject.toml` to the versions exercised by CI/Render. The purpose of these pins is reproducibility; dependency changes require a new verification run before results are promoted as accepted evidence.

## Accepted H2 integrated baseline

The accepted H2 integrated implementation path is `cases.studies.p11_4_project_defined_h2_smoke`. The following command reproduces the 20-cell integrated smoke output used by the dedicated workflow while keeping teacher Eq. 11.46 as the steady-state convergence diagnostic:

```bash
python - <<'PY'
from dataclasses import asdict
import json
from pathlib import Path
from cases.studies.p11_4_project_defined_h2_smoke import run_smoke

result = run_smoke(cells=20, tolerance=1.0e-4, max_steps=8_000)
payload = asdict(result)
out = Path("artifacts/deliverable/p11_4_h2_baseline.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(out)
if not result.converged:
    raise SystemExit("P11.4 integrated H2 baseline did not converge")
if result.min_temperature_K <= 0.0 or result.min_pressure_Pa <= 0.0:
    raise SystemExit("P11.4 integrated H2 baseline produced a nonphysical state")
PY
```

Expected output: `artifacts/deliverable/p11_4_h2_baseline.json`.

The frozen acceptance record remains `cases/studies/data/p11_4_project_defined_h2_smoke_acceptance.json`. The higher-resolution 20/40/80 numerical evidence is separately frozen in `cases/studies/data/p11_4_grid_convergence_acceptance.json`; this smoke command is not a replacement for that grid audit.

## Accepted P12 project-defined response study

The response command below uses the same default sweep implementation and acceptance semantics as the dedicated P12 workflow. Teacher Eq. 11.46 maximum relative density change remains the authoritative steady-state gate. Normalized residual is reported independently and is not assigned an invented hard threshold. The existing forward-flow guard is preserved.

```bash
python - <<'PY'
from dataclasses import asdict
import json
from pathlib import Path
from cases.studies import p12_project_defined_response_sweep as sweep

points = sweep.run_sweep()
payload = {
    "classification": sweep.CASE_CLASSIFICATION,
    "not_a_source_reproduction": sweep.NOT_A_SOURCE_REPRODUCTION,
    "mode_label_claim": False,
    "equivalence_ratios": list(sweep.PROJECT_EQUIVALENCE_RATIOS),
    "teacher_eq_11_46_steady_tolerance": sweep.TEACHER_EQ_11_46_STEADY_TOLERANCE,
    "points": [asdict(point) for point in points],
}
out = Path("artifacts/deliverable/p12_project_defined_response_sweep.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(out)
PY
```

Expected output: `artifacts/deliverable/p12_project_defined_response_sweep.json`.

The machine-readable accepted response evidence remains `cases/studies/data/p12_project_defined_response_sweep_acceptance.json`. Stricter `2e-5` continuation and thermal-throat grid evidence remain frozen separately in `cases/studies/data/p12_thermal_throat_continuation_acceptance.json` and `cases/studies/data/p12_thermal_throat_grid_sensitivity_acceptance.json`.

## Claim boundaries

- A forward-flow-guard point is `solver/model-domain inadmissible`; it is not evidence of unstart or a combustion-mode transition.
- The P12 output is a continuous project-defined response study. No broader ramjet/scramjet/dual-mode label is inferred outside the frozen Cao Eq. (3-2) criterion scope.
- Cao Case 2 formal reproduction remains blocked by exact source `A(x)`, prescribed `Yi(x)` spatial information/rule, and the original fuel/injection/source spatial convention.
- The integrated variable-thermochemistry production path remains Rusanov until the Steger-Warming energy-reference/epsilon blockers are source-resolved.
- Eq. 11.26 is not converted into a dimensional wall-heat source without a defensible source mapping.
