# P11.2 Authoritative Source and Baseline Gap Report

## Status

`P11.2A FORMALLY VERIFIED — SOURCE-BACKED PUBLIC COLD-FLOW SURROGATE`

`P11.2B REACTIVE / HEAT-RELEASE BASELINE STILL EVIDENCE-GATED`

The original P11.2 blocker was an absence of enough source-grounded geometry and axial source data to construct a complete reactive baseline without inventing inputs. That all-or-nothing blocker has now been split into two tracks. P11.2A has been completed with a publicly accessible, dimensioned experiment; P11.2B remains gated by the reactive closure.

The public surrogate does **not** replace the teacher-designated Cao Ruifeng material and must not be cited as a Cao-thesis reproduction.

## Source inventory

| ID | Source | Authority / role | Current use |
| --- | --- | --- | --- |
| SRC01 | teacher instruction screenshots | project instruction | establishes that the Cao Ruifeng material is the ultimate teacher-designated reference |
| SRC02 | Cao Ruifeng doctoral thesis (2016) | project-designated thesis | candidate inlet records, kerosene LHV, combustion-mode research context |
| SRC03 | Cao Ruifeng master's thesis (2011), *面向控制的超燃冲压发动机一维建模研究* | project-designated modelling reference | one-dimensional modelling context; no complete solver-ready case frozen yet |
| SRC04 | *Theory and Application of Hypersonic Aerodynamic Layout*, Ch. 11 | project-provided technical reference | generalized one-dimensional source-term semantics |
| SRC05 | repository solver / P3–P10 verification evidence | implementation authority | accepted numerical capability |
| SRC06 | Li et al. (2025), DOI `10.7527/S1000-6893.2024.30944` | peer-reviewed public experiment | P11.2A geometry, inflow, operating points, and Table-4 factor levels |

Machine-readable SRC06 ledger:

`cases/studies/data/p11_2_public_surrogate_source.json`

## P11.2A closure

SRC06 supplies:

- Table 1: `Ma=2.52`, `T0=1650 K`, `P0=1.34 MPa`, and vitiated-air composition;
- Fig. 2 / Table 2: `L1=560 mm`, `L2=140 mm`, `L3=490 mm`, `W=50 mm`, `H1=35 mm`, `H2=42 mm`, cavity and injector dimensions;
- Table 3: total ethylene flow, injector total pressure, equivalence ratio, and active injector-module sets;
- Table 4: isolator-length, injection-distance, cavity-depth, and throat-size variations.

P11.2A freezes an explicit reduced-order core-flow mapping from the dimensioned main passage and keeps cavity recirculation outside `A(x)`. It converts the source total inlet state to a primitive supersonic inlet with the existing perfect-gas assumptions `gamma=1.4` and `R=287 J/(kg K)`. Fuel, burn, wall-friction, and wall-heat source terms remain disabled.

Formal acceptance:

- source/code SHA: `9032d5e8304ac6022ba7c4f185b170c6ba9cddd2`
- standard Test run `34880624298`: `801 passed in 47.01 s`
- dedicated formal run `34880624357`: success
- runtime artifact `10362683519`
- artifact SHA-256 `364ea31e3395e0080ad7a426f20e4fc53dc438efb4b53147ed3dcc3fcb759789`
- tracked evidence: `artifacts/p11_2a/p11_2a_formal_evidence.json`

Baseline `P11A-PUBLIC-COLD-BASE` converged to `9.83971e-9`; the short-isolator case `P11A-ISO-L280` converged to `9.65361e-9`. Both remain fully supersonic.

## Important P11.2A scientific finding

The source-backed `L1=560 -> 280 mm` variation produces no material change in the overlapping cold-flow solution after the expected `0.280 m` coordinate shift: field differences are about `1e-10` relative.

This is not experimental agreement. It shows that the current inviscid, source-free, constant-area isolator contains no mechanism for the experimentally observed reactive isolator-length sensitivity. The missing sensitivity can only emerge after relevant physics such as heat release, friction/boundary-layer/shock-train interaction, or another justified closure is represented.

Therefore P11.2A is complete as a physical-scale **cold-flow surrogate and model-scope diagnostic**, but it cannot answer the teacher's reactive LBW/YBW question by itself.

## Confirmed Cao-thesis evidence retained

SRC02 still provides useful, locatable numerical records:

- Chapter 2, Table 2-1: `Ma2=2`, `rho2=0.7736 kg/m^3`, `p2=156.522 kPa`, `T2=705 K`, `u2=1038 m/s`, `k=1.33`, `phi=0.3` for an idealized case;
- Chapter 3, Table 3-2: `gamma=1.4` and kerosene `Hf=42,000 kJ/kg` for that cycle-analysis model;
- Chapter 5, Table 5-1: isolator-entry Mach, pressure, total temperature, and air mass flow for ground-test flight-Mach settings 4–7.

They remain evidence records, not permission to invent missing axial geometry or source profiles.

## Primary remaining blocker for P11.2B

The **minimum** missing element for a prescribed-energy reactive surrogate is a defensible axial heat-release / burned-fuel distribution or an explicit source-backed reduced-order law from which it can be derived.

If P7 fuel mass addition is also activated, the model additionally requires:

- axial fuel mass-source distribution;
- fuel axial velocity;
- fuel specific total enthalpy.

Total fuel flow alone is insufficient. The project will not silently replace it with a uniform `d(mdot_f)/dx`, equal per-injector split, zero fuel velocity, or arbitrary fuel enthalpy.

## Additional deferred physics / mapping issues

- cavity depth cannot be promoted to a quasi-1D area change without a documented reduced-order cavity closure;
- injection-distance sensitivity is meaningless while injection is inactive;
- the Table-4 throat-size variation is source-backed, but its exact local one-dimensional passage mapping must be frozen before formal use;
- wall friction / heat transfer require sourced or explicitly approved closure values if enabled;
- P11.3 still requires a literature/teacher-backed LBW/YBW discrimination criterion.

## Next development decision

P11.2B should first target the smallest scientifically defensible energy-addition closure. A prescribed total-temperature / heat-release law from a traceable one-dimensional scramjet modelling source is acceptable only if its formula, parameters, range, transformation into the existing P8 source semantics, and limitations are all recorded. It must be labelled a reduced-order prescribed-heat-release surrogate rather than detailed chemistry or exact experiment reproduction.

No formal reactive curve will be created until that closure passes this evidence rule.
