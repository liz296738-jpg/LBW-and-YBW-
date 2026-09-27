# External Lineage Audit for Teacher Eq.11.19--11.20 Mixing Closures

## Purpose

This note records what can and cannot currently be corroborated outside the
teacher-provided Chapter 11 pages for the mixing-efficiency and complete-mixing
length closures.

The teacher material remains the **primary project authority** for Eq.11.19,
Eq.11.20, their branch definitions, and the stated calibration ranges.

## Confirmed external lineage

### Heiser & Pratt

William H. Heiser and David T. Pratt, *Hypersonic Airbreathing Propulsion*,
AIAA Education Series, 1994, ISBN 978-1-56347-035-6.

Later scramjet model literature explicitly cites this text for the mixing model.
Independent bibliographic records confirm the AIAA 1994 edition.

### Pulsonetti, Erdos & Early

M. V. Pulsonetti, J. I. Erdos, and K. Early,
“Engineering Model for Analysis of Scramjet Combustor Performance with
Finite-Rate Chemistry,” *Journal of Propulsion and Power*, 7(6), 1055--1063,
1991. DOI: https://doi.org/10.2514/3.23427

The published model is a reduced-order supersonic-combustion engineering model
that feeds fuel and oxidizer into a product stream using an empirical mixing
model and finite-rate reaction. It is useful as lineage/context for
mixing-limited reduced-order modeling, not as a replacement for the teacher
equations.

### NASA Langley mixing-recipe corroboration

Public NASA/AIAA material using the Langley mixing recipe contains the same
equivalence-ratio dependence used in the complete-mixing-length family:

- a lean-side factor proportional to `0.179 exp(1.72 phi)`;
- a rich-side factor proportional to approximately `3.333 exp(-1.204 phi)`
  (published sources may show rounded variants);
- a stoichiometric complete-mixing length expressed using injector/duct gap
  scaling, commonly around 60 gaps in that specific recipe.

This strongly corroborates the **functional lineage** of the teacher Eq.11.20
family.

## What is not directly promoted

The repository has **not yet directly inspected a primary Heiser/Pratt or
Pulsonetti full-text page that independently states the exact teacher
`C_m = 25--60` interval in the same notation.

A later scramjet modeling paper reproduces the teacher-style equation and states
`C_m=25--60` while citing Heiser/Pratt and Pulsonetti/Erdos/Early for the
mixing calculation. That is useful corroboration, but it is a secondary
citation chain.

Therefore the evidence classification is:

- Eq.11.20 functional form: **teacher-primary + externally corroborated lineage**;
- exact `C_m=25--60` range: **teacher-primary / later-secondary corroborated**;
- a specific project value such as `C_m=30`: **project-selected**, even though
  it lies inside the teacher-source range.

## Consequence for P13

P13 may legitimately use `[25,60]` as the teacher-source sensitivity domain,
because that range is directly frozen in the project primary source.

P13 must not claim that:

- `25`, `30`, `42.5`, or `60` are experimental operating points;
- `C_m=30` is a literature-recommended optimum;
- the exact `25--60` interval has been independently verified from the
  Pulsonetti primary article until a directly inspectable source page supports
  that statement.

## Source locators

- Teacher Chapter 11 ledger:
  `cases/studies/data/teacher_mixing_combustion_closure.json`
- Heiser & Pratt bibliographic record:
  ISBN 9781563470356, AIAA Education Series, 1994
- Pulsonetti et al.:
  DOI 10.2514/3.23427
- NASA Langley mixing-recipe public record:
  AIAA 2002-0543 / NASA public archive
- P13 protocol:
  `docs/p13_teacher_mixing_constant_sensitivity.md`

## Evidence rule

External lineage corroboration can strengthen confidence that the closure family
is established in scramjet engineering. It cannot silently upgrade a
project-selected parameter value into a measured or source-prescribed value.
