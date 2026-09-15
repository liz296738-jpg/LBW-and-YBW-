# P11.3 — dual-mode combustion definition evidence

## Decision

P11.3 begins **definition-first**. No LBW/YBW classifier or regime map is implemented in this step.

Five peer-reviewed sources have now been frozen to define the general dual-mode combustion taxonomy and transition physics. They support a physically meaningful future classifier, but they do **not** resolve the project-specific literal labels `LBW` and `YBW`. The repository name is not evidence for what those acronyms mean.

Machine-readable ledger:

`cases/studies/data/p11_3_mode_definition_source.json`

Readiness gate:

`cases/studies/p11_3_mode_definition_readiness.py`

## 1. Quasi-one-dimensional multimode definition

Tian et al. (2014), *Quasi-One-Dimensional Multimodes Analysis for Dual-Mode Scramjet*, Journal of Propulsion and Power, DOI `10.2514/1.B35177`, is the most directly applicable definition source for this project.

The paper distinguishes the flow states using both the precombustion shock system and averaged Mach state. In project terminology, the important distinction is:

- weak/no meaningful precombustion shock system + supersonic flow → supersonic-combustion family;
- obvious precombustion shock train + post-shock Mach > 1 → dual-mode supersonic-combustion state;
- obvious precombustion shock train + post-shock Mach < 1 → dual-mode subsonic-combustion state;
- sufficiently strong shock system with subsonic combustor state → subsonic-combustion family;
- shock-train length exceeding the isolator capacity → inlet unstart rather than another combustion mode.

This is much stronger than a rule such as `min(M) < 1 => ram mode`: it ties the Mach observation to a specific location/topology in the isolator–combustor system.

## 2. Experimental three-mode taxonomy

Zhang et al. (2014), *Influencing factors on the mode transition in a dual-mode scramjet*, Acta Astronautica, DOI `10.1016/j.actaastro.2014.06.006`, experimentally classifies:

1. Pure Scram Mode;
2. Dual-Mode Scram Mode;
3. Dual-Mode Ram Mode.

The classification uses wall-pressure distributions, one-dimensional analysis and optical visualization. The reported physical interpretation is consistent with Tian's later quasi-1D taxonomy: pure scram has no precombustion shock train; dual-mode scram has a weaker shock train while combustor-entry averaged Mach remains above one; dual-mode ram has a sufficiently strong shock train that makes the combustor-entry flow subsonic.

The paper reports normalized wall-pressure transition values of roughly `0.23` and `0.34` at one station for one stated experiment. These numbers are **not universal thresholds** and are therefore recorded only as condition-specific evidence, not project constants.

The same study reports transition hysteresis, so a future map may require direction/history information if it attempts to represent the transition region rather than only steady end states.

## 3. Thermal-choking mechanism

Liu et al. (2019), *Dual-Mode Operation and Transition in Axisymmetric Scramjets*, AIAA Journal, DOI `10.2514/1.J058391`, shows that transition initiation depends on the balance between heat addition and area relief. In the reported configuration thermal choking begins near a pressure inflection where those effects become comparable.

Crucially, after a scram-to-ram transition the flow may reaccelerate to supersonic speed downstream. Therefore a downstream `Mach > 1` observation does not prove that the upstream combustion mode is scram.

## 4. Transition dynamics and hysteresis

Fotia & Driscoll (2013), *Ram-Scram Transition and Flame/Shock-Train Interactions in a Model Scramjet Experiment*, DOI `10.2514/1.B34486`, reports sudden wall-pressure/flame-position changes, a measured transition boundary and low-frequency flame/precombustion-pseudoshock oscillations in part of the transition region.

This supports an explicit `transition/uncertain` state when observables are insufficient or dynamically oscillatory, rather than forcing every operating point into a binary label.

## 5. Why no universal scalar threshold is frozen

Cao et al. (2020), *Study on influencing factors of combustion mode transition boundary for a scramjet engine based on one-dimensional model*, Aerospace Science and Technology, DOI `10.1016/j.ast.2019.105590`, shows that a one-dimensional transition boundary depends on geometry, heat-release distribution, wall state/roughness and incoming-flow composition.

Therefore a future project classifier may use a source-backed physical criterion, but it cannot copy one equivalence ratio, wall-pressure ratio, or Mach threshold from a different combustor and treat it as geometry-independent truth.

## Frozen P11.3 rules

1. Do not classify mode from the minimum Mach anywhere in the domain alone.
2. The precombustion shock system / isolator state and combustor-entry flow state are central observables in the cited literature.
3. Downstream supersonic reacceleration is compatible with a ram-mode state upstream.
4. Facility-specific pressure/equivalence-ratio transition values remain facility-specific unless transferability is demonstrated.
5. Hysteresis/oscillation may require a transition or uncertain band rather than a forced binary label.

## Current blocker: `LBW` and `YBW`

The project-specific meaning of `LBW` and `YBW` is currently unresolved.

Checks performed so far:

- current repository: no authoritative literal expansion/definition found;
- prior project initialization material: describes the scramjet/dual-mode quasi-1D CFD goal but does not define `LBW` or `YBW`;
- public exact-string searches: no credible aerospace source found that establishes `LBW` and `YBW` as standard dual-mode scramjet mode names.

Therefore this project must **not** silently map `LBW` or `YBW` onto any of the literature modes above. The general taxonomy is ready; the project label mapping is not.

## Promotion gate

Current machine-readable state:

- `general_mode_taxonomy_ready = true`
- `transition_mechanism_evidence_ready = true`
- `condition_specific_threshold_evidence_ready = true`
- `lbw_ybw_label_mapping_ready = false`
- `solver_observable_mapping_ready = false`
- `classifier_ready = false`
- `regime_map_ready = false`

The next P11.3 task is to resolve the project labels and then decide exactly which of the current solver outputs can represent the cited isolator/combustor-entry observables. Only after that mapping is source-backed should code for classification be added.
