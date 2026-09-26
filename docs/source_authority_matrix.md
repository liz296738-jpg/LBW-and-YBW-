# Source Authority Matrix

## Purpose

This matrix prevents supporting literature, validation experiments, or convenient public formulas from silently replacing the teacher-requested model. Every scientific claim should state which authority class supports it.

## Authority classes

| Class | Source | Permitted role | Must not be used to do |
| --- | --- | --- | --- |
| A | Teacher-provided Chapter 11 photographs, `双模态冲压燃烧室一维数值模拟` | Primary authority for the requested second-scheme equations, equation numbering, source terms, numerical route and convergence definition | Must not be silently replaced by a different public model merely because it is easier to implement |
| B | Cao Ruifeng master's thesis (2011) and doctoral thesis (2016) | Teacher-lineage model/thermochemistry/mode-criterion corroboration and source-case evidence | Must not be treated as providing missing Chapter 11 constants or spatial inputs when they are not actually present |
| C | Standard property databases: Berkeley GRI-Mech 3.0, NIST Chemistry WebBook SRD 69 | Thermochemical polynomial/property provenance and independent data checks | Does not validate combustion/mixing/engine-mode physics |
| D | Primary experiments and official validation archives, e.g. NASA Burrows--Kurkov | Physical validation/context for compatible measured quantities and conditions | Must not be converted into teacher/Cao geometry or used to tune unsupported source terms |
| E | Analytical/verification references and standards, e.g. ASME V&V 20 and NASA grid-convergence guidance | Numerical verification methodology, error/uncertainty discipline and terminology | Does not supply missing engine physics or empirical closure parameters |

## Current equation/source mapping

| Model element | Current implementation evidence | Authority | Status |
| --- | --- | --- | --- |
| quasi-1D conservative formulation and teacher source vector | teacher-reference modules and Chapter 11 ledger | A, supported by B | implemented |
| teacher mixing/stoichiometric closures, Eqs. 11.18--11.29 | teacher closure ledgers/tests | A | implemented for supported H2/C2H4 scope |
| variable thermochemistry, Eqs. 11.30--11.35 | teacher equation ledger + Cao doctoral relations + GRI/NIST data | A+B+C | implemented for H2/C2H4 core species |
| teacher Steger--Warming, Eqs. 11.42--11.44 | source transcription and constant-property verification | A | implemented as audited path; variable-thermochemistry production integration remains source-gated |
| pseudo-time/CFL and Eq. 11.46 density-change convergence | teacher steady solver/ledger | A | implemented |
| wall friction Eq. 11.25 | teacher wall closure ledger/tests | A | implemented |
| wall heat Eq. 11.26 empirical-to-dimensional mapping | teacher record incomplete for unique dimensional mapping | A | source-gated; not guessed |
| Cao Case 2 formal reproduction | inlet/source identity frozen, exact spatial inputs incomplete | B | blocked by exact A(x), Yi(x), and source/injection spatial convention |
| NASA Burrows--Kurkov | official experiment and NASA computational-reference archive | D | supporting reduced-order V&V only; not the teacher deliverable |
| grid-convergence/GCI methodology | ASME/NASA verification guidance | E | used for claim discipline; no automatic grid-independence claim |
| project numerical tolerances / QA gates | repository acceptance policy | project-defined, not an external authority class | values such as Eq.11.46 tolerance `2e-5` and 0.5% mass-inventory QA gate are explicitly labelled project controls; they must not be attributed to the teacher, ASME, NASA, papers, or experiments |

## Public source locators

- Berkeley GRI-Mech thermodynamics: https://combustion.berkeley.edu/gri-mech/new21/data/thermo_table.html
- GRI-Mech 3.0 coefficient file: http://combustion.berkeley.edu/gri-mech/version30/files30/thermo30.dat
- NIST Chemistry WebBook SRD 69: https://webbook.nist.gov/
- ASME V&V 20: https://www.asme.org/codes-standards/find-codes-standards/standard-for-verification-and-validation-in-computational-fluid-dynamics-and-heat-transfer
- NASA spatial/grid convergence guidance: https://www.grc.nasa.gov/www/wind/valid/tutorial/spatconv.html
- NASA Burrows--Kurkov experiment, NASA-TM-X-2828: https://ntrs.nasa.gov/citations/19730023096

## Evidence rule

If a formula, coefficient, boundary condition, empirical constant, acceptance threshold, or physical classification cannot be traced to the appropriate authority class, it stays explicit as project-defined, diagnostic-only, or source-gated. A successful run or visually plausible curve is never sufficient evidence to promote it.
