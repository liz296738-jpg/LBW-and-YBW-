# P11.3N — Teacher/Cao Steger–Warming compatibility source audit

## Question

P11.3M reproduced the teacher Chapter 11 Eq. (11.42)–(11.44) Steger–Warming formulas, but full CI exposed a real compatibility gap: the classical closed-form split exactly reduces to the calorically-perfect implementation, while its energy component does not reconstruct the project's physical Euler energy flux when temperature-dependent heat capacity and absolute species energy are used.

P11.3N asks a narrow evidence question before any solver modification:

> Do the teacher-provided Cao references specify how variable thermochemistry / absolute species enthalpy is reconciled with Steger–Warming flux-vector splitting?

## Cao doctoral thesis

Source: **《超燃冲压发动机燃烧模态转换及其控制方法研究》— 曹瑞峰**.

The Chapter 2 one-dimensional-flow derivation explicitly includes the physics that matter to the present energy convention:

- Eq. (2-28)–(2-29): mixture molecular weight from species mass fractions;
- Eq. (2-30): mixture static enthalpy `h = sum(h_i Y_i)`;
- Eq. (2-31): species enthalpy polynomial;
- the text immediately following Eq. (2-31) states that the species enthalpy contains **thermal/sensible enthalpy plus chemical energy**;
- Eq. (2-32)–(2-34): temperature-dependent species/mixture `cp` and heat-capacity ratio;
- Eq. (2-41)–(2-44): total-enthalpy energy balance including chemical energy and kinetic energy;
- Eq. (2-51) onward: the model is solved as a coupled set of spatial ordinary differential equations / Mach-number influence relations.

This is strong support for the project's use of composition-dependent absolute enthalpy. However, this thesis does **not** provide a Steger–Warming/FVS discretization for those equations, so it does not supply the missing energy-split reconciliation.

## Cao master's thesis

Source: **《面向控制的超燃冲压发动机一维建模研究》— 曹瑞峰**.

In the combustion-chamber one-dimensional model section, the text explicitly states that the gas is assumed both thermally perfect and calorically perfect and that the specific heats are constants. The model is then developed as an ODE-based reduced-order formulation.

That constant-property assumption is compatible with the classical Steger–Warming algebraic limit, but the thesis does not provide a variable-`cp`, absolute-enthalpy Steger–Warming extension.

## Audit result

The two Cao references support two different pieces of the overall project:

1. the doctoral thesis strongly supports variable composition, variable heat capacity, and absolute chemical+sensible enthalpy accounting;
2. the master's reduced-order model explicitly uses constant specific heat in the relevant one-dimensional derivation.

Neither reference found in the teacher package gives a source-backed rule that modifies Eq. (11.42) so that classical Steger–Warming remains exactly energy-consistent with the project's variable-thermochemistry conservative state.

Therefore **no correction is introduced**. In particular, P11.3N does not:

- subtract formation enthalpy before flux splitting;
- invent a reference-energy correction flux;
- replace the physical Euler energy flux by the literal Eq. (11.42) recombination;
- choose an undocumented smoothing epsilon;
- claim the variable-thermochemistry Steger–Warming solver is ready.

## Project decision

The already verified boundary-complete **Rusanov + variable thermochemistry + teacher algebraic composition + Eq. (11.38) source** path remains the defensible integrated compatibility solver.

The literal teacher Steger–Warming implementation remains valuable as:

- a source transcription;
- a constant-property regression path;
- a diagnostic for future source recovery;
- a clearly documented unresolved numerical-model compatibility item.

If a later teacher note, original implementation, or other authoritative source gives the missing variable-thermochemistry FVS convention, it can reopen the gate. Until then the project should continue with the accepted Rusanov path rather than inventing a correction.
