# Mentor Dashboard

A local mentor-facing dashboard is included for the project-defined course deliverable.

## Start

From the repository root:

```bash
python -m pip install -e ".[dev]"
export DASHBOARD_RUN_TOKEN="choose-a-private-run-password"
python tools/mentor_dashboard.py
```

The dashboard opens at `http://127.0.0.1:8765` by default. It binds only to the local loopback interface unless `--host` is explicitly changed.

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

## Hosted deployment and downloads

Use `render.yaml` for a new Render Blueprint. For an existing Render service set:

- Build command: `pip install -e .`
- Start command: `python tools/mentor_dashboard.py --host 0.0.0.0 --port $PORT --no-browser`
- Health check: `/api/health`
- Environment: `DASHBOARD_RUN_TOKEN` set to a private run password.

The dashboard asks for the password when starting a calculation. A missing token
makes execution read-only; viewing frozen evidence remains public. Completed run
outputs and job metadata are also public to visitors, so this dashboard is intended
for these non-sensitive project-defined cases. Do not put the password in the URL.

Each job has its own output directory and CSV/JSON download links. Job records are
saved atomically. On process restart, unfinished jobs become `interrupted` and may
be rerun manually; numerical state/checkpoint resumption is not implemented.
Use a single server process per data directory. Set `DASHBOARD_DATA_DIR` to a
persistent disk mount to retain jobs and outputs across hosting redeploys. The
default local directory is `artifacts/dashboard`; ephemeral hosting storage does
not preserve data across redeploys. A persistent disk is not provisioned by the
Blueprint and may require a paid hosting plan.

The overview still shows frozen accepted evidence, not results from the latest
interactive job. Download job-specific outputs for fresh calculations.
