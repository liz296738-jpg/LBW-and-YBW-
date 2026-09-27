# C10H22 / n-Decane External Thermochemistry Candidate Audit

## Purpose

Teacher Chapter 11 includes a `C10H22` stoichiometric/composition branch, but
the repository has not recovered source-compatible `C10H22` thermochemical
polynomials for the current teacher/CHEMKIN convention.

This audit asks a narrower question:

> Are there authoritative external n-decane / kerosene-surrogate mechanisms
> that could support a **future, separately validated model branch**?

The answer is yes. This does **not** close the teacher-path source gap.

## Authoritative external candidates

### LLNL C8--C16 n-alkane mechanisms

Lawrence Livermore National Laboratory publishes archived detailed mechanisms
for C8--C16 normal alkanes, explicitly including n-decane (`n-C10H22`).
The LLNL record states that the mechanisms include high- and low-temperature
reaction pathways and were compared against experimental data from shock tubes,
flow reactors, and jet-stirred reactors.

Public source:
https://combustion.llnl.gov/archived-mechanisms/alkanes/c8c16-nalkanes

**Permitted role:** authoritative external candidate for a future n-decane
kinetics/thermochemistry branch.

**Not permitted:** treating LLNL coefficients as though they were supplied by
the teacher source, or silently mixing their reference-state convention with the
current GRI-based teacher H2/C2H4 database.

### Honnet et al. (2009)

S. Honnet, K. Seshadri, U. Niemann, N. Peters,
“A surrogate fuel for kerosene,” *Proceedings of the Combustion Institute*,
32(1), 485--492, 2009.
DOI: https://doi.org/10.1016/j.proci.2008.06.218

The study uses an Aachen kerosene surrogate containing 80 wt% n-decane and
20 wt% 1,2,4-trimethylbenzene and validates selected combustion behavior
against kerosene experiments.

**Permitted role:** evidence that n-decane is a scientifically established
kerosene-surrogate component.

**Boundary:** real aviation kerosene is multicomponent; pure n-decane is not a
universal physical replacement for Jet-A/JP-8/RP-3.

### Singh, Nishiie & Qiao (2011)

D. Singh, T. Nishiie, L. Qiao,
“Experimental and Kinetic Modeling Study of the Combustion of n-Decane,
Jet-A, and S-8 in Laminar Premixed Flames,”
*Combustion Science and Technology*, 183(10), 1002--1026, 2011.
DOI: https://doi.org/10.1080/00102202.2011.575420

The paper reports n-decane/air flame-speed experiments and comparisons with
multiple kinetic mechanisms; JetSurF 0.2 gave the best representation of the
reported n-decane flame-speed data among the mechanisms considered.

**Permitted role:** experimental/model evidence that external n-decane
mechanisms can be quantitatively validated rather than adopted only by
convenience.

**Boundary:** flame-speed agreement does not prove compatibility with the
teacher quasi-1D composition closure, energy reference, or source-vector model.

## Decision

The project now distinguishes two questions:

1. **Teacher-path C10H22 readiness:** still **BLOCKED** because no
   source-compatible teacher/Cao thermochemical record has been recovered.
2. **External n-decane branch feasibility:** **SUPPORTED IN PRINCIPLE** by
   authoritative mechanisms and peer-reviewed experiments.

No `C10H22` NASA-polynomial coefficients are added to the production database
by this audit.

## Minimum gate for a future external C10H22 branch

Before an external n-decane model can enter production, it must:

1. freeze one exact mechanism/thermochemistry source and version;
2. record molecular-weight and NASA-polynomial coefficients with source hashes;
3. verify continuity at polynomial break temperatures;
4. independently check `cp(T)`, `h(T)`, and `e(T)` against the source;
5. define the absolute/reference enthalpy convention explicitly;
6. prove that mixing the new species data with the current O2/N2/Ar/H2O/CO2
   database does not create inconsistent reference states;
7. reproduce at least one published n-decane thermochemical/combustion
   benchmark within its documented scope;
8. keep the resulting branch labelled **EXTERNAL MODEL EXTENSION**, not
   `teacher-source reproduction`, unless the teacher/Cao source is separately
   recovered.

## Consequence for current work

H2/C2H4 remain the source-defensible integrated teacher path. `C10H22`
remains intentionally unavailable in that production path. External n-decane
literature reduces uncertainty about future extensibility, but it does not
justify filling missing teacher coefficients by analogy.
