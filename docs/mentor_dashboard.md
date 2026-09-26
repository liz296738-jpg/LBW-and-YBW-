# Mentor Dashboard

A mentor-facing dashboard is included for the project-defined course deliverable. The same Python entry point is used locally and by the deployed Render web service.

## Start

From the repository root:

```bash
python -m pip install -e ".[dev]"
python tools/mentor_dashboard.py
```

The dashboard opens at `http://127.0.0.1:8765` by default. It binds only to the local loopback interface unless `--host` is explicitly changed. The deployed service uses `python tools/mentor_dashboard.py --host 0.0.0.0 --port $PORT --no-browser` and is currently exposed at `https://lbw-and-ybw.onrender.com`.

## What the dashboard shows

The interface reads the frozen acceptance/evidence records already stored in the repository and presents:

- course-deliverable status and accepted packaging provenance;
- the accepted project-defined H2 integrated baseline;
- teacher Eq. 11.46 steady-state diagnostics;
- 20/40/80 grid-convergence-trend evidence;
- normalized mass/momentum/energy inventory diagnostics;
- the accepted P12 equivalence-ratio response sweep;
- warm-start continuation and thermal-throat grid-sensitivity evidence;
- Cao Case 2 evidence blockers and the remaining source/model boundaries.

The page uses no external JavaScript or CSS dependencies and can therefore be used offline after the Python environment is installed.

## Controlled run buttons

The **运行算例** page exposes only three frozen project-defined paths:

1. 20-cell accepted H2 smoke baseline using the historical Eq. 11.46 `1e-4` density-change tolerance;
2. the accepted P12 response sweep at `phi = 0.10 / 0.20 / 0.30` using the `2e-5` Eq. 11.46 gate;
3. the accepted 80-cell full-profile export using the `2e-5` gate.

Only one solver job can run at a time. Generated outputs are written under `artifacts/dashboard/` and are intentionally ignored by Git.

Downloaded baseline/response JSON records are self-describing: they include UTC generation time plus runtime provenance (Python version, installed scientific-package versions, and available Render Git/service identity). The 80-cell profile export additionally emits a run manifest containing SHA-256 digests for its CSV and JSON outputs. The dashboard displays integrity digests next to completed jobs.

Render instance storage is operational, not archival. Dashboard-generated artifacts can disappear after a restart or redeploy. A result becomes frozen scientific evidence only after it is intentionally reviewed and incorporated into the repository evidence workflow; merely running it on the dashboard does not change any accepted scientific claim.

The dashboard does **not** expose controls for changing source terms, thermochemistry, wall-heat mapping, flux-scheme compatibility fixes, or other scientifically gated inputs.

## Scientific claim boundary

The dashboard does not change the scientific status of the project:

- `PROJECT_DEFINED` cases remain implementation/response evidence, not Cao Case 2 reproduction.
- A forward-flow guard trigger is shown as `solver/model-domain inadmissible`; it is not labelled as unstart or a combustion-mode transition.
- Teacher Eq. 11.46 maximum relative density change remains the authoritative steady-state gate.
- Normalized residual remains an independent diagnostic with no invented hard threshold.
- 20/40/80 evidence is described as a grid-convergence trend unless an asymptotic/GCI analysis is actually performed.
- Any `SCRAM_SIDE` display is limited to the documented Cao Eq. (3-2) thermal-throat criterion scope for otherwise accepted points.
- LBW/YBW remain project/person identifiers, not physical combustion modes.
