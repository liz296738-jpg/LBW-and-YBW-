# Mathematical Model

## Assumptions for Current Model

The implemented baseline model is one-dimensional, compressible, inviscid, and adiabatic. It uses an ideal, calorically perfect gas with constant `gamma` and constant `R`; it excludes combustion and fuel injection. These are staged assumptions, not claims about the final model.

## Primitive Variables

`rho`, `u`, `p`, `T`, `Mach`

## Conservative Variables

`rho`, `rho*u`, `rho*E`

## Equation of State

`p = rho R T`

## Energy Relation

`E = e + u^2 / 2`  
`e = p / [rho (gamma - 1)]`

## Speed of Sound and Mach Number

`a = sqrt(gamma R T)`  
`M = u / a`

## Governing Equation

`∂U/∂t + ∂F/∂x = S`

For the current source-free, one-dimensional Euler baseline, `∂U/∂t + ∂F/∂x = 0`.

`U = [rho, rho*u, rho*E]`

`F = [rho*u, rho*u^2 + p, u*(rho*E + p)]`

**P3.1 implements the physical Euler flux `F(U)`.** P3 also implements the first-order finite-volume spatial discretization, SSP-RK3 time integration, and the constant-area solver.

P3.2 implements the separate Rusanov baseline numerical interface flux `F_hat(U_L, U_R)` for conservative states on either side of an interface. This numerical flux is not part of the governing physical law.

P3.3 constructs the source-free semi-discrete finite-volume system `dU/dt = L(U)`, where `L_i(U) = -(F_hat_(i+1/2) - F_hat_(i-1/2)) / dx`. This is numerical discretization, not a new physical equation.

P3.4 applies SSP-RK3 to this semi-discrete system as numerical time discretization. P3.5 solves the source-free, constant-area 1D Euler system with transmissive boundaries; it does not yet represent a quasi-1D scramjet combustor with area or source terms.

The implemented quasi-1D formulation is

`∂(A U)/∂t + ∂(A F)/∂x = [0, p dA/dx, 0]`.

P4.1 implements the geometry representation required by this equation. P4.2 implements the semi-discrete quasi-1D spatial operator while retaining the conservative state as `U`, rather than changing the state API to `A U`:

`dU_i/dt = -[A_(i+1/2) F_hat_(i+1/2) - A_(i-1/2) F_hat_(i-1/2)] / (A_i dx) + [0, p_i (A_(i+1/2) - A_(i-1/2)) / (A_i dx), 0]`.

The two terms use the same face-area difference. Consequently, a static state with constant pressure has zero residual for arbitrary valid area profiles.

P4.3 introduces no governing equation. It advances the existing semi-discrete relation `dU/dt = L_quasi1D(U)` with SSP-RK3 while the supplied `AreaProfile` remains time-independent. This is a baseline transient solver integration, not controlled nozzle validation.

P5 changes only numerical flux construction methodology; it does not alter the governing equations or physical model.

## Wall Friction Model — P6.1

P6.1 defines an independent, prescribed wall-friction source using the **Darcy friction factor** `f_D` (not the Fanning factor; `f_D = 4 f_F`). The hydraulic diameter is an explicit input,

`D_h = 4 A / P_w`,

where `P_w` is wetted perimeter. The Darcy wall shear stress is

`tau_w = (f_D / 8) rho u |u|`.

The source contribution is

`S_f = [0, -f_D rho u |u| / (2 D_h), 0]`.

The signed `u |u|` factor ensures drag opposes either flow direction. The mass source is exactly zero. For the stationary, adiabatic wall assumed here, the total-energy source is also exactly zero: friction redistributes kinetic and internal energy without net wall energy transfer.

Cross-sectional area alone does not determine wetted perimeter or hydraulic diameter. Therefore `D_h` is prescribed explicitly and is not inferred from `AreaProfile`; this avoids making an unsupported circular-duct assumption. The Darcy factor is likewise prescribed, with no Reynolds-number or roughness correlation. The source is composed with wall heat and evaluated at every SSP-RK3 stage in the quasi-1D solver.

## Wall Heat-Transfer Model — P6.2

P6.2 defines an independent, prescribed wall-heat-flux source. The signed wall heat flux `q''_w` is measured in W/m²: `q''_w > 0` transfers heat from the wall into the gas, while `q''_w < 0` transfers heat from the gas to the wall.

For a control volume of length `dx`, wall heating is `dQdot = q''_w P_w dx` and the control-volume size is `dV = A dx`. Therefore the energy source density is `S_E = q''_w P_w / A`. With `D_h = 4 A / P_w`, the complete source vector is

`S_q = [0, 0, 4 q''_w / D_h]`.

Mass and direct momentum sources are exactly zero; only the total-energy equation receives the prescribed heat contribution. The function accepts explicit hydraulic diameter because area alone does not determine wetted perimeter. It is deliberately not a wall-temperature, heat-transfer-coefficient, Stanton/Nusselt, radiation, or Reynolds-correlation model: `q''_w` is the prescribed output of any future constitutive or boundary model.

## P6.3 Coupled Wall-Source Integration

P6.3 retains the P4/P5 quasi-1D residual and adds the already-defined wall contributions:

`dU_i/dt = -[A_R Fhat_R - A_L Fhat_L] / (A_i dx) + S_area,i + S_f,i + S_q,i`.

Here `S_area = [0, p Delta_A / (A dx), 0]`, `S_f = [0, -f_D rho u |u| / (2 D_h), 0]`, and `S_q = [0, 0, 4 q''_w / D_h]`. The independent source functions are composed without duplicating their formulas. `hydraulic_diameter=None` means wall physics is disabled only when both prescribed wall inputs are zero; enabling either source without a hydraulic diameter is an error.

All active physical sources are evaluated from the current SSP-RK3 stage state rather than being frozen once per timestep. The existing Euler-wave-speed CFL formula is unchanged. No source-stiffness limiter, clipping, new boundary condition, friction correlation, or heat-transfer correlation is introduced.

P6.4 validates exact uniform-source temporal evolution and Fanno/Rayleigh continuum steady residual consistency. Primary residuals are normalized by the RMS magnitude of their prescribed source. Monotone first-order-or-better paths are classified as convergent or superconvergent; a normalized finest residual at or below `1e-10` is roundoff-limited. Rusanov Fanno paths are valid superconvergent residuals, while the fully rightgoing supersonic Steger-Warming Rayleigh energy residual is roundoff-limited because the corresponding discrete flux/source balance is exact for the linear energy flux. This is not a general higher-order claim for Steger-Warming.

## Fuel Injection Model — P7.1

P7.1 introduces an independent prescribed local volumetric fuel source, with fuel mass source rate `rho_dot_f` [kg/(m^3 s)], axial injection velocity `u_f,x` [m/s], and injected-stream specific total enthalpy `h_t,f` [J/kg]:

`S_fuel = [rho_dot_f, rho_dot_f u_f,x, rho_dot_f h_t,f]`.

The components have units kg/(m^3 s), N/m^3, and W/m^3 respectively. The injected energy source uses specific total enthalpy because fuel enters the control volume as a mass flux. The supplied total enthalpy already includes the injected stream kinetic contribution, so `fuel_injection_source` adds no additional `u_f^2/2` term.

`S_fuel` is not a combustion source: P7.1 includes no LHV, heat release, combustion efficiency, reaction progress, mixing-loss model, injector pressure force, spray model, or phase-change model. Fuel is represented only as added mass, axial momentum, and total enthalpy in the existing three-equation homogenized perfect-gas state. No fuel mass fraction or species transport equation is present, and this standalone source is not yet connected to `solve_quasi_1d`.

## Isentropic Area Validation

P4.4 uses the isentropic reference relation `A/A* = (1/M) [2/(gamma+1) * (1 + (gamma-1) M^2 / 2)]^((gamma+1)/(2(gamma-1)))` and `dA/A = (M^2 - 1) du/u`. These relations are validation references, not replacements for the solver governing equation. Validation remains on separate subsonic and supersonic branches and does not cross the sonic point.

## P2 Implemented Relations

P2 implements and tests the ideal-gas relation `p = rho R T`, the energy relations `e = p / [rho (gamma - 1)]` and `E = e + u^2 / 2`, the sound speed `a = sqrt(gamma R T)`, and `Mach = u / a`.

The implemented conservative state is `U = [rho, rho*u, rho*E]`. P3--P5 implement numerical solvers for the frozen inviscid, adiabatic governing equation. P5 changes numerical flux construction only; it does not change the governing equation or physical model.
