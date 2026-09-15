# P11.3I — Teacher Eq. (11.38) source-vector adapters

The teacher source writes the quasi-one-dimensional governing equation in area-weighted form and gives the full source vector in Eq. (11.38). The project already handles the geometric `p dA/dx` term inside the accepted quasi-1D operator, so P11.3I adds only the remaining terms after division by cell area.

## Fuel injection

For a localized finite-volume injector, the textbook discrete statement `Delta(mdot_s)/Delta x` is represented exactly by placing the total prescribed fuel addition in one chosen cell:

\[
\left(\frac{d\dot m_s}{dx}\right)_j=\frac{\Delta\dot m_s}{\Delta x}.
\]

The integrated source therefore returns the prescribed fuel mass flow exactly.

The injected total enthalpy is

\[
h_{ts}=h_s(T_s)+\frac{u_{sx}^2}{2},
\]

using the same absolute source-backed species enthalpy convention as the variable-composition model. H2 and C2H4 are supported; C10H22 remains thermochemistry-gated.

After division by area the injected contributions are

\[
S_\rho=\frac{d\dot m_s/dx}{A},\qquad
S_m=u_{sx}\frac{d\dot m_s/dx}{A},\qquad
S_E=h_{ts}\frac{d\dot m_s/dx}{A}.
\]

## Friction

Eq. (11.38) gives

\[
S_{m,f}=-\frac12\rho u^2\frac{4f}{D_e}.
\]

The previously verified Eq. (11.25) correlation supplies `f(phi,eta)`. This stage retains the teacher forward-flow convention and rejects `u<0` rather than silently changing the source equation.

## Wall heat

Eq. (11.38) uses

\[
S_{E,q}=\rho u\frac{d(\delta q)}{dx}.
\]

P11.3I accepts this **dimensional gradient** directly when supplied. It still does not convert the empirical Eq. (11.26) coefficient into `d(delta q)/dx`, because that dimensional relation has not been frozen from the available teacher evidence.

## Chemical energy

No independent combustion `Qdot` is added. The teacher text explicitly states that absolute fitted species enthalpy includes zero-point/chemical energy and that reaction heat is already represented when composition changes. Adding a separate reaction heat source would therefore double count chemical energy.

## Remaining integration gate

The source primitives are ready, but a formal integrated teacher case is not yet promoted. In particular, a domain that starts at the injector cannot use a fuel-containing transmissive inlet and also add the same fuel with an injector source. The injector/upstream boundary treatment must be frozen first.
