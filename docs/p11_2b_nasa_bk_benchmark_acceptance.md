# P11.2B NASA Burrows–Kurkov reduced-order benchmark acceptance

## Decision

The NASA Burrows–Kurkov route is accepted as a **formal reduced-order computational-reference benchmark**, not as an independent experimental validation of a one-dimensional bulk state.

The public NASA experiment and exit probe profiles remain independently ingested and checksum-tracked, but they are intentionally not collapsed into an unsupported single Mach/temperature acceptance scalar. The formal acceptance target is instead the conservative one-dimensional moment match implied by the public NASA Wind-US reference solution that also supplies the signed net-energy and net-momentum closures.

## Accepted evidence chain

- Public Burrows–Kurkov experiment and NASA Glenn validation archive are reproducibly acquired from official NASA hosts.
- The legacy Wind-US Common File solution is checksum-frozen, parsed with repository-owned tooling, dimensionalized from file scaling metadata, and reduced over the source-backed main duct.
- The reduced domain starts at the injection station `x=0`; its inlet is a conservative moment match of NASA reference mass flow, axial momentum flux, and effective total enthalpy.
- Signed net-energy and net-momentum histories are derived only from the NASA computational reference. Experimental probe profiles are not used to tune either source.
- A conservative exit target is reconstructed from the same frozen mass-flow, axial-momentum-flux, total-enthalpy, and source-backed exit-area moments.

## Numerical acceptance

**Threshold provenance.** The numerical thresholds used below (the <2% conservative-target discrepancy gate and the <0.5% 160-to-320 refinement-change gate) are **project-defined regression/benchmark gates**. They are not uncertainty bounds reported by Burrows--Kurkov, not NASA experimental acceptance criteria, and not ASME validation thresholds. They are retained only to make this reduced-order computational-reference benchmark deterministic and auditable. Experimental validation claims require experimental uncertainty and compatible measured quantities; this benchmark explicitly does not make that claim.


Reference effective-gas model:

- `gamma = 1.2779315953440815`
- `R = 329.4821420180208 J/(kg K)`

Primary 80-cell run:

- converged, residual `< 1e-7`
- minimum Mach `2.4065` (supersonic throughout)
- exit Mach `2.41720`
- exit static pressure `87.923 kPa`
- exit static temperature `1269.74 K`
- signed energy integral mismatch `1.46e-11 W`
- signed momentum integral mismatch `0 N`

Conservative exit target:

- Mach `2.43106`
- static pressure `87.198 kPa`
- static temperature `1263.23 K`

A 40/80/160/320-cell convergence study passed. On 320 cells, the relative errors versus the conservative target are approximately:

- Mach: `-0.567%`
- pressure: `+0.827%`
- temperature: `+0.512%`

The 160-to-320 refinement changes are approximately `1e-5` relative for all three quantities, so the remaining ~0.5–0.8% difference is a stable reduced-order/model-closure discrepancy rather than unresolved mesh error.

## Thermodynamic sensitivity

A lower-gamma sensitivity run (`gamma = 1.246731797999899`) also converges and remains supersonic, but produces a materially different exit state. Therefore the accepted benchmark claim is conditional on the frozen calorically-perfect effective-gas reduction and must not be generalized to variable-composition or finite-rate reacting thermodynamics.

## Explicitly not claimed

This acceptance does **not** claim:

- independent experimental validation of a single one-dimensional exit Mach or temperature scalar;
- finite-rate chemistry validation;
- H2/H2O species-profile validation;
- experimentally measured axial chemical heat release;
- identification of a wall-friction coefficient from the effective momentum residual;
- LBW/YBW classification.

The experimental profiles remain valuable independent context, but their strong nonuniformity makes an unsupported scalar average inappropriate for a formal 1D acceptance gate.

## Gate to P11.3

P11.3 may now begin, but only definition-first. Before implementing any LBW/YBW classifier or regime map, freeze from authoritative literature/project evidence:

1. the exact meaning of LBW and YBW;
2. the observable(s) used to distinguish them;
3. any threshold or transition criterion;
4. operating-condition applicability;
5. uncertainty and limitations.

A sonic crossing or `Mach < 1` must not be silently equated with an LBW/YBW label unless the source definition explicitly supports that mapping.
