# Professional research platform website design

## Goal

Replace the current mentor-only dashboard framing with a professional product website for researchers, academic supervisors, and engineering collaborators using one-dimensional scramjet or dual-mode ramjet CFD workflows. The website must help a new visitor understand the product, evaluate the strength and limits of its evidence, and take a safe next action.

## Audience and tone

The primary audience is technically literate: supervisors reviewing work, research collaborators assessing reproducibility, and engineers evaluating a controlled numerical workflow. Use plain Chinese with conventional scientific terms where needed. Explain unfamiliar internal terms in place. Never imply experimental validation, formal Cao Case 2 reproduction, physical mode classification, or grid independence where the repository does not support it.

## Information architecture

1. **Home / capability overview** — a clear value proposition, a short description of the validated workflow, and explicit paths to evidence and controlled examples.
2. **Verified results** — accepted H2 baseline, grid-convergence trend, conservation diagnostics, and accepted parameter responses. Every result carries its claim scope.
3. **Research evidence** — provenance, source records, frozen acceptance scope, unresolved inputs, and project limitations. This is the home for detailed P12/P13/P14 material.
4. **Controlled runs** — the existing fixed run modes, with expected output, fixed inputs, single-job behavior, transient-artifact notice, and downloads.

## Home page composition

The hero states: “为超燃冲压与双模态冲压研究提供可追溯的一维 CFD 工作流。” Supporting copy describes the product as a controlled research workflow, not a design-certification system. Primary actions are “查看已验证能力” and “运行示例”.

Follow the hero with:

- three capability cards: controlled numerical workflow, evidence review, reproducible exports;
- a compact “what the current results mean” panel, including validated H2 scope and key exclusions;
- a three-step research workflow: select a fixed study, generate a traceable output, review the evidence boundary;
- a concise research-evidence preview that leads to the detailed evidence page;
- a final action panel with links to run an example, download records, and read methodology.

## Visual system

Use a restrained engineering-instrument palette: deep navy `#0D1B2A`, signal blue `#1463FF`, mist `#F5F8FC`, ink `#17212B`, and evidence amber `#B45309`. Use a clear Chinese-capable sans-serif stack and avoid decorative glass effects. Reserve colour for state, not decoration. Use an airy, responsive single-column narrative at narrow widths and a max-width content grid on desktop. Ensure keyboard focus, sufficient contrast, reduced-motion support, and non-colour status cues.

## Copy rules

- Prefer “已验证范围”, “项目定义的数值证据”, “当前不支持”, and “需要补充的来源信息”.
- Explain “frozen” as “已定稿的研究配置/证据记录” where it appears.
- Replace internal labels such as “mentor console”, “deliverable complete”, and opaque P-number-first navigation with user-oriented names.
- State negative claims explicitly: a forward-flow guard is only solver/model-domain inadmissibility and is not labelled unstart.

## Functionality and data handling

Existing `/api/summary`, health, job, run, and artifact download endpoints remain the source of truth. The homepage reads the summary API and renders only accepted/frozen repository evidence. Controlled-run modes remain fixed and single-job-only; no scientifically gated model control becomes an online form. Loading, runtime errors, an empty job list, failed jobs, and unavailable artifacts must provide a specific next action.

## Verification

- Run the existing Python test suite and dashboard-specific tests.
- Verify the server serves the updated interface and existing API paths keep working.
- Check desktop and mobile rendering with screenshots; inspect screenshots with the project-required visual-analysis tool after explicit approval.
- Review visible Chinese copy against the claim-boundary records and `docs/mentor_dashboard.md`.

## Scope boundary

This change restructures the product experience, wording, navigation, accessibility, and safe presentation of current data. It does not alter solver physics, numerical acceptance criteria, scientific source records, or the scientific status of any result.
