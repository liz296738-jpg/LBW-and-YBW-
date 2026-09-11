"""Write a reproducible P10.1 conservation-balance JSON artifact."""
import json
from pathlib import Path
import numpy as np
from scramjet1d.config import GasProperties
from scramjet1d.geometry import constant_area_profile
from scramjet1d.state import primitive_to_conservative
from scramjet1d.verification import quasi_1d_conservation_balance

gas = GasProperties(); cells = 8; x = np.linspace(0., 1., cells)
state = primitive_to_conservative(1.2 + .01 * np.sin(x), 200. + 2. * np.cos(x), 100000. + 100. * np.sin(x), gas)
records = {}
for scheme in ("rusanov", "steger-warming"):
    balance = quasi_1d_conservation_balance(state, constant_area_profile(cells), .1, gas, flux_scheme=scheme)
    records[scheme] = {"rhs_integral": balance.rhs_integral.tolist(), "boundary_flux": balance.boundary_flux.tolist(), "source_integral": balance.source_integral.tolist(), "closure_error": balance.closure_error.tolist(), "passed": bool(np.allclose(balance.closure_error, 0., rtol=0., atol=1e-8))}
artifact = {"baseline_sha": "4d2df6ab08649bc8701b229561b349985c410614", "cases": {"V2_constant_area_nonuniform": records}, "all_passed": all(record["passed"] for record in records.values())}
path = Path("artifacts/p10_1/p10_1_conservation_metrics.json"); path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
