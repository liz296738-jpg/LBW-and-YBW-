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
| P10.1 | conservation ledger | conservation-balance | discrete global closure | complete locally | CI required for formal acceptance |

The project currently verifies numerical identities, discretized transport, source mappings, boundary semantics, global discrete balances, and convergence diagnostics. It does not validate real scramjet combustion, LBW/YBW engine performance, chemistry, ignition, mixing, or flameholding against experiments.

For cell content `Q=sum(A U dx)`, the ledger uses `dQ_RHS=sum(A R dx)`, `dQ_boundary=A_L F_L-A_R F_R`, and `dQ_source=sum(A S dx)`. Its absolute closure is `dQ_RHS-(dQ_boundary+dQ_source)`. Variable-area momentum includes the discrete pressure-area source; area mass and energy sources are zero.

P10.2 will study grid/spatial convergence, P10.3 CFL/temporal/scheme sensitivity, and P10.4 will integrate evidence and audit claims.

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
