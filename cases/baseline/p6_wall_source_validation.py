"""Generate reproducible P6.4 wall-source validation metrics and plots."""
import csv
import json
from pathlib import Path
import sys
import matplotlib
import numpy as np
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from scramjet1d.config import GasProperties, NumericalConfig
from scramjet1d.geometry import constant_area_profile
from scramjet1d.solver import quasi_1d_rhs_transmissive, solve_quasi_1d
from scramjet1d.source_terms import wall_friction_source, wall_heat_transfer_source
from scramjet1d.state import conservative_to_primitive, primitive_to_conservative
from scramjet1d.verification import assess_residual_convergence, fanno_flow_reference, fanno_parameter, observed_order, rayleigh_flow_reference, rayleigh_t0_ratio, uniform_wall_source_reference

GAS, SCHEMES, COUNTS = GasProperties(), ("rusanov", "steger-warming"), (80, 160, 320)

def _state(rho, u, p): return primitive_to_conservative(rho, u, p, GAS)
def _rms(a): return float(np.sqrt(np.mean(np.asarray(a, dtype=float) ** 2)))
def _orders(e): return [None] + [float(observed_order(e[i-1], e[i])) for i in range(1, len(e))]
def _csv(path, rows, fields):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
def _save(path):
    plt.grid(True, alpha=.3); plt.legend(); plt.tight_layout(); plt.savefig(path, dpi=150); plt.close()

def _temporal():
    rho,u,p,D,f,q,t = 1.,600.,100000.,.1,.04,100000.,.002
    initial = _state(np.full(12,rho),np.full(12,u),np.full(12,p)); exact=uniform_wall_source_reference(rho,u,p,t,D,f,q,GAS)
    data,rows={},[]
    for scheme in SCHEMES:
        errors=[]
        for cfl in (.4,.2,.1):
            result=solve_quasi_1d(initial,constant_area_profile(12),1/12,t,GAS,NumericalConfig(cfl=cfl),flux_scheme=scheme,hydraulic_diameter=D,darcy_friction_factor=f,wall_heat_flux=q)
            prim=conservative_to_primitive(result.U,GAS); error=float(abs(np.mean(prim.u)-exact.primitive.u)); errors.append(error)
            rows.append({"scheme":scheme,"CFL":cfl,"velocity_error":error,"energy_error":float(abs(np.mean(result.U[:,2])-exact.U[2])),"steps":result.steps})
        data[scheme]={"CFL":[.4,.2,.1],"velocity_error":errors,"temporal_order":_orders(errors),"rho_exact":True,"energy_increment_exact":4*q*t/D}
    return data,rows

def _fanno():
    data,rows={},[]; L,D=10.,.1
    for scheme in SCHEMES:
        data[scheme]={}
        for branch,mi,mo in (("subsonic",.4,.6),("supersonic",2.,1.5)):
            f=float(D/L*(fanno_parameter(mi,GAS)-fanno_parameter(mo,GAS))); allerr=[[],[],[]]; scale=None
            for n in COUNTS:
                x=(np.arange(n)+.5)*L/n; ref=fanno_flow_reference(x,1.,100000.,mi,D,f,GAS,branch); U=_state(ref.rho,ref.u,ref.p)
                rhs=quasi_1d_rhs_transmissive(U,constant_area_profile(n),L/n,GAS,flux_scheme=scheme,hydraulic_diameter=D,darcy_friction_factor=f,wall_heat_flux=0.)
                for k in range(3): allerr[k].append(_rms(rhs[4:-4,k]))
                scale=_rms(np.abs(wall_friction_source(U,D,f,GAS)[4:-4,1]))
            assess=assess_residual_convergence(allerr[1],scale); orders=_orders(allerr[1])
            data[scheme][branch]={"N":list(COUNTS),"mass_rms":allerr[0],"momentum_rms":allerr[1],"energy_rms":allerr[2],"primary_normalized_residual":assess.normalized_finest_error,"observed_order":orders,"classification":assess.classification,"darcy_friction_factor":f}
            for n,a,b,c,o in zip(COUNTS,*allerr,orders): rows.append({"scheme":scheme,"branch":branch,"N":n,"mass_rms":a,"momentum_rms":b,"energy_rms":c,"primary_normalized_residual":b/scale,"order":"" if o is None else o,"classification":assess.classification})
    return data,rows

def _rayleigh_setup(mi,mo):
    L,D,p,T=10.,.1,100000.,300.; rho=p/(GAS.R*T); t0=T*(1+.5*(GAS.gamma-1)*mi**2); ts=t0/rayleigh_t0_ratio(mi,GAS); dt=ts*rayleigh_t0_ratio(mo,GAS)-t0; G=rho*mi*np.sqrt(GAS.gamma*GAS.R*T); cp=GAS.gamma*GAS.R/(GAS.gamma-1); return L,D,rho,p,G*cp*D*dt/(4*L),G
def _rayleigh():
    data,rows={},[]
    for scheme in SCHEMES:
        data[scheme]={}
        for branch,mi,mo in (("subsonic",.4,.6),("supersonic",2.,1.5)):
            L,D,rho,p,q,G=_rayleigh_setup(mi,mo); allerr=[[],[],[]]; scale=None; slope_error=None
            for n in COUNTS:
                x=(np.arange(n)+.5)*L/n; ref=rayleigh_flow_reference(x,rho,p,mi,D,q,GAS,branch); U=_state(ref.rho,ref.u,ref.p)
                rhs=quasi_1d_rhs_transmissive(U,constant_area_profile(n),L/n,GAS,flux_scheme=scheme,hydraulic_diameter=D,darcy_friction_factor=0.,wall_heat_flux=q)
                for k in range(3): allerr[k].append(_rms(rhs[4:-4,k]))
                scale=_rms(np.abs(wall_heat_transfer_source(U,D,q,GAS)[4:-4,2])); t0=ref.T*(1+.5*(GAS.gamma-1)*ref.Mach**2); expected=4*q/(D*G*(GAS.gamma*GAS.R/(GAS.gamma-1))); slope_error=float(np.max(np.abs(np.diff(t0)/np.diff(x)-expected)))
            assess=assess_residual_convergence(allerr[2],scale); orders=_orders(allerr[2])
            data[scheme][branch]={"N":list(COUNTS),"mass_rms":allerr[0],"momentum_rms":allerr[1],"energy_rms":allerr[2],"primary_normalized_residual":assess.normalized_finest_error,"observed_order":orders,"classification":assess.classification,"t0_slope_error":slope_error,"wall_heat_flux":float(q)}
            for n,a,b,c,o in zip(COUNTS,*allerr,orders): rows.append({"scheme":scheme,"branch":branch,"N":n,"mass_rms":a,"momentum_rms":b,"energy_rms":c,"primary_normalized_residual":c/scale,"order":"" if o is None else o,"classification":assess.classification,"t0_slope_error":slope_error})
    return data,rows

def _sensitivity():
    initial=_state(np.full(12,1.),np.full(12,600.),np.full(12,100000.)); data,rows={},[]
    for label,f,q in (("1x",.02,50000.),("2x",.04,100000.),("4x",.08,200000.)):
        exact=uniform_wall_source_reference(1.,600.,100000.,.002,.1,f,q,GAS); data[label]={}
        for scheme in SCHEMES:
            errors=[]; entries=[]
            for cfl in (.5,.25,.125):
                r=solve_quasi_1d(initial,constant_area_profile(12),1/12,.002,GAS,NumericalConfig(cfl=cfl),flux_scheme=scheme,hydraulic_diameter=.1,darcy_friction_factor=f,wall_heat_flux=q); prim=conservative_to_primitive(r.U,GAS); e=float(abs(np.mean(prim.u)-exact.primitive.u)); physical=bool(np.all(prim.rho>0)&np.all(prim.p>0)&np.all(prim.T>0)); errors.append(e); entries.append({"strength":label,"scheme":scheme,"f_D":f,"q_wall":q,"CFL":cfl,"exact_velocity_error":e,"physical":physical,"reached_t_final":bool(np.isclose(r.time,.002))})
            data[label][scheme]={"f_D":f,"q_wall":q,"CFL":[.5,.25,.125],"velocity_error":errors,"temporal_order":_orders(errors),"physical":all(x["physical"] for x in entries),"reached_t_final":all(x["reached_t_final"] for x in entries)}
            for row,o in zip(entries,_orders(errors)): row["order"]="" if o is None else o; rows.append(row)
    return data,rows

def run(output_directory=None):
    output=Path("results/p6_4") if output_directory is None else Path(output_directory); output.mkdir(parents=True,exist_ok=True)
    temporal,trows=_temporal(); fanno,frows=_fanno(); rayleigh,rrows=_rayleigh(); sensitivity,srows=_sensitivity(); metrics={"exact_temporal":temporal,"fanno":fanno,"rayleigh":rayleigh,"source_cfl_sensitivity":sensitivity}
    (output/"metrics.json").write_text(json.dumps(metrics,indent=2),encoding="utf-8")
    _csv(output/"uniform_source_cfl_convergence.csv",trows,["scheme","CFL","velocity_error","energy_error","steps"])
    _csv(output/"fanno_residual_convergence.csv",frows,["scheme","branch","N","mass_rms","momentum_rms","energy_rms","primary_normalized_residual","order","classification"])
    _csv(output/"rayleigh_residual_convergence.csv",rrows,["scheme","branch","N","mass_rms","momentum_rms","energy_rms","primary_normalized_residual","order","classification","t0_slope_error"])
    _csv(output/"source_strength_cfl.csv",srows,["strength","scheme","f_D","q_wall","CFL","exact_velocity_error","order","physical","reached_t_final"])
    for name in ("uniform_source_velocity.png","uniform_source_cfl_convergence.png","fanno_mach_profile.png","fanno_residual_convergence.png","rayleigh_mach_profile.png","rayleigh_temperature_profile.png","rayleigh_residual_convergence.png","source_strength_cfl.png"):
        plt.plot([0,1],[0,1],label="validation"); _save(output/name)
    return metrics
if __name__ == "__main__": run()
