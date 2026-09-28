# Professional Research Platform Implementation Plan

**Goal:** Convert the mentor-focused dashboard into a professional research product website without changing any solver physics or scientific claims.

**Architecture:** Keep the Python server and existing JSON APIs. Rework `web/mentor_dashboard/index.html` into four client-side views—home, verified results, research evidence, and controlled runs—fed exclusively by `/api/summary` and the existing jobs endpoints.

**Constraints:** Use clear Chinese; never present project-defined evidence as experimental validation, formal Cao Case 2 reproduction, mode classification, or grid independence; keep run modes fixed and single-job-only; preserve current APIs; support keyboard, contrast, reduced motion, and mobile layouts.

### Task 1: Product navigation and safe content model

**Files:** Modify `web/mentor_dashboard/index.html`; test `tests/test_mentor_dashboard.py`.

- [ ] Replace mentor-first navigation with `首页`, `已验证能力`, `研究证据`, and `受控算例` views.
- [ ] Keep all existing DOM/API behavior used by render and run functions.
- [ ] Add an availability test covering `/` and `/api/summary`.
- [ ] Run `pytest tests/test_mentor_dashboard.py -q`.

### Task 2: Customer-facing home and verified results

**Files:** Modify `web/mentor_dashboard/index.html`.

- [ ] Add a value proposition, three capability cards, scope summary, research workflow, and routes to results/runs.
- [ ] Render H2 baseline, grid trend, P12 response, and P13 sensitivity from existing summary data, each with an explicit claim boundary.
- [ ] Translate loading and data-error states into specific Chinese recovery guidance.
- [ ] Verify desktop and narrow viewport rendering against the local dashboard.

### Task 3: Research evidence and controlled examples

**Files:** Modify `web/mentor_dashboard/index.html` and `docs/mentor_dashboard.md`.

- [ ] Present blockers as “当前限制、原因、所需资料”.
- [ ] State that a forward-flow guard means solver/model-domain inadmissibility only.
- [ ] Explain fixed run inputs, output types, transient artifacts, job status, and downloads.
- [ ] Run `pytest -q` and request `/`, `/api/health`, `/api/summary`, and `/api/jobs` from the local server.

### Task 4: Accessible engineering visual system and release verification

**Files:** Modify `web/mentor_dashboard/index.html`; test `tests/test_mentor_dashboard.py`.

- [ ] Apply navy, signal-blue, mist, ink, and amber tokens; reduce decorative glass effects.
- [ ] Add visible focus states, non-colour status cues, and reduced-motion behavior.
- [ ] Add a regression test for product navigation and existing controlled-run invocation.
- [ ] Run the full test suite and inspect approved screenshots at desktop and mobile widths.
