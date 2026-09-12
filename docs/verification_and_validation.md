# Verification and validation evidence

Verification asks whether the implementation solves its declared equations correctly. Validation asks whether those equations and assumptions represent a real physical system and requires experimental or authoritative reference data.

| Stage | Case | Type | Reference/metric | Status | Limitation |
| --- | --- | --- | --- | --- | --- |
| P3 | Euler identities and shock smoke tests | exact-identity | conservation and finite states | complete | not experimental validation |
| P4 | isentropic area case | analytic benchmark | area-Mach relation | complete | ideal inviscid model |
| P5 | flux comparison | cross-scheme | controlled residual/transient metrics | complete | first-order reconstruction |
| P6 | wall source | controlled-source verification | Fanno/Rayleigh references | complete | prescribed source |
| P7 | fuel injection | controlled source-term verification | prescribed integral mapping | complete | no species/mixing |
| P8 | combustion heat release | controlled source-term verification | prescribed heat mapping | complete | no chemistry |
| P9 | physical boundaries and steady diagnostics | integration robustness | characteristic and residual contracts | complete | no engine experiment |
| P10.1 | conservation ledger | conservation-balance | discrete global closure | complete | exact-SHA CI, not experimental validation |
| P10.2 | smooth isentropic nozzle | analytical solution convergence | relative L1/Linf and observed order | long-run evidence pending | first-order smooth benchmark only |

The project currently verifies numerical identities, discretized transport, source mappings, boundary semantics, global discrete balances, and convergence diagnostics. It does not validate real scramjet combustion, LBW/YBW engine performance, chemistry, ignition, mixing, or flameholding against experiments.

For cell content `Q=sum(A U dx)`, the ledger uses `dQ_RHS=sum(A R dx)`, `dQ_boundary=A_L F_L-A_R F_R`, and `dQ_source=sum(A S dx)`. Its absolute closure is `dQ_RHS-(dQ_boundary+dQ_source)`. Variable-area momentum includes the discrete pressure-area source; area mass and energy sources are zero.

P10.1 was formally accepted at SHA `32eb50cd687da6e23a4cb2269bc31120fbff2b3e` by Test workflow run `34638173666` (`706 passed in 35.21 s`). P10.2 now has a reproducible formal runner and strict lightweight aggregation tests, but remains incomplete until the dedicated exact-SHA long-run workflow produces a passing twelve-run artifact. P10.3 will study CFL/temporal/scheme sensitivity, and P10.4 will integrate evidence and audit claims.

## P10.1 V1-V8 evidence matrix

| Case | Verification type | Reference identity | Schemes | Acceptance | Status | Limitation |
| --- | --- | --- | --- | --- | --- | --- |
| V1 | exact free stream | uniform RHS, boundary and source equal zero | Rusanov, SW | machine precision | local pass | instantaneous identity |
| V2 | conservation balance | RHS integral equals boundary contribution | Rusanov, SW | machine precision | local pass | one smooth state |
| V3 | geometry source | momentum equals `p(A_R-A_L)` | Rusanov, SW | machine precision | local pass | uniform pressure |
| V4 | wall mapping | analytic friction and heat integrals | Rusanov, SW | machine precision | local pass | prescribed source |
| V5 | fuel mapping | analytic mass, momentum and energy integrals | Rusanov, SW | machine precision | local pass | no species |
| V6 | combustion mapping | analytic burned-fuel/LHV energy integral | Rusanov, SW | machine precision | local pass | no chemistry |
| V7 | source superposition | total equals area+wall+fuel+combustion | Rusanov, SW | machine precision | local pass | instantaneous ledger |
| V8 | physical boundaries | characteristic flux global balance | Rusanov, SW | machine precision | local pass | controlled subsonic state |

The tracked JSON is a reproducible repository snapshot, not self-referential proof of its containing commit. Formal exact-SHA provenance is established by regenerating the artifact during pytest/CI at the checked-out commit and comparing its runtime `head_sha` with that checkout.

## P10.2 grid/spatial convergence protocol

P10.2 compares converged discrete steady solutions with the independent `isentropic_nozzle_reference` on the smooth linear area profile from 1.0 to 1.2 m² over a 1 m domain. The formal grids are `N = 40, 80, 160`; all represent that same continuous geometry. Stagnation conditions are 300000 Pa and 500 K. The subsonic branch uses reference Mach 0.5, a total-condition inlet, and the analytical outlet-face static pressure. The supersonic branch uses reference Mach 2.0, the analytical left-face state, and supersonic outflow. Wall, heat, fuel, and combustion sources are disabled.

Both Rusanov and Steger-Warming use `CFL = 0.2`, normalized steady tolerance `1e-8`, maximum pseudo-time 0.05 s, and maximum 200000 steps. Pseudo-time RK3 is only the iterative method for the discrete steady equations; this stage does not measure RK3 temporal order. Every run must take at least one step, terminate as converged, remain finite and positive, and preserve its Mach branch.

The primary metrics for density, velocity, pressure, temperature, and Mach are full-domain relative L1 and Linf errors. Cells `[2:-2]` provide boundary diagnostics only. Normalization is grid-independent: branch-specific density, velocity, and Mach scales come from a 2001-point analytical reference, while pressure and temperature use 300000 Pa and 500 K. For halved spacing, `p = log(E_coarse/E_fine)/log(2)`. Every primary error sequence must decrease strictly; final L1 order must be at least 0.75 and final Linf order at least 0.5.

`cases/verification/p10_2_grid_convergence.py` generates the exact-SHA JSON source of truth, an auxiliary CSV, and L1/Linf plots under `artifacts/p10_2/`. The full 2 branches × 2 schemes × 3 grids matrix exceeds the standard-CI runtime budget, so `.github/workflows/p10_2_grid_convergence.yml` runs it separately by explicit manual dispatch and uploads the runtime evidence. Standard Test CI validates builders, a reduced real solver path, strict positive and negative aggregation gates, serialization, and artifact contracts; it does not substitute reduced grids for the formal study.
