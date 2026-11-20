"""Regional disaggregation and reconciliation (regions sum exactly to the national forecast). No assumed values.

1. Base-year regional requirement shares from CSV drivers only:
       share_r ~ sum_s Pop_s * (GSDP per person_s)^e,   e = Model 1 income elasticity (estimated on NPP + CSV).
2. Bottom-up regional path: y_r,t = R_r,base (P_r,t / P_r,base) (ypc_r,t / ypc_r,base)^eps_t, with each region's CSV
   population and GSDP-share trends and eps_t the national ensemble's implied elasticity.
3. MinT/WLS reconciliation with national variance -> 0 (the national series is back-tested) and regional variance
   proportional to level, which reduces to proportional allocation; mint() is general and unit-tested.
4. Regional uncertainty: national Monte Carlo draws x regional shares re-computed with each state's log-share trend
   slopes perturbed by their own regression standard errors.
"""
import numpy as np
import pandas as pd
from src.config import PROC, REGIONS, BASE_FY, SEED
from src.features import regional_drivers, YEARS_ALL


def e_cs():
    from src.forecast.ensemble import fitted_models
    return float(fitted_models()[0].summary()["beta_lny"])


def mint(y_nat, y_reg, w_nat, w_reg):
    """General MinT/WLS reconciliation for a 1-level hierarchy. Returns coherent bottom forecasts."""
    S = np.vstack([np.ones((1, len(y_reg))), np.eye(len(y_reg))])
    W_inv = np.diag(1 / np.r_[w_nat, w_reg])
    yhat = np.r_[y_nat, y_reg]
    G = np.linalg.solve(S.T @ W_inv @ S, S.T @ W_inv)
    return G @ yhat


def base_shares(st_base):
    s = st_base
    idx = s["pop"] * (s.gsdp / s["pop"]) ** e_cs()
    r = idx.groupby(s.region).sum()
    return (r / r.sum()).reindex(REGIONS)


def regional_point(nat_fc):
    nd = {k: (v if k == "years" else v[:1]) for k, v in nat_fc["drivers"].items()}
    st, reg = regional_drivers(nd)
    sh0 = base_shares(st[st.FY == BASE_FY])
    total = nat_fc["total"][0]
    P, Y = nd["pop"][0], nd["gdp_pc"][0]
    I = total / P
    with np.errstate(divide="ignore", invalid="ignore"):
        eps = np.where(np.arange(len(YEARS_ALL)) == 0, 0.0, np.log(I / I[0]) / np.log(Y / Y[0]))
    R0 = sh0 * total[0]
    reg = reg.set_index(["region", "FY"])
    bu = pd.DataFrame({r: R0[r] * (reg.loc[r]["pop"].values / reg.loc[r]["pop"].values[0]) *
                          (reg.loc[r]["gsdp_pc"].values / reg.loc[r]["gsdp_pc"].values[0]) ** eps for r in REGIONS}, index=YEARS_ALL)
    rec = pd.DataFrame(index=YEARS_ALL, columns=REGIONS, dtype=float)
    for i, y in enumerate(YEARS_ALL):
        rec.loc[y] = mint(total[i], bu.loc[y].values, 1e-9, bu.loc[y].values)
    return dict(shares_base=sh0, bottom_up=bu, reconciled=rec, adjustment_pct=(rec / bu - 1) * 100,
                region_drivers=reg.reset_index())


def share_draws(nat_fc, n=400, seed=SEED):
    """Regional share paths with state log-share slopes perturbed by their own regression SEs."""
    rng = np.random.default_rng(seed + 11)
    sp = pd.read_csv(PROC / "state_panel.csv")
    hist = sp[sp.FY.between(2016, 2025)]
    base = sp[sp.FY == BASE_FY].set_index("State")
    states = sorted(sp.State.unique())
    nd = {k: (v if k == "years" else v[:1]) for k, v in nat_fc["drivers"].items()}
    P, G = nd["pop"][0], nd["gdp"][0]
    t = YEARS_ALL - BASE_FY
    fits = {}
    for col in ("pop", "gsdp_real"):
        x = hist.assign(sh=hist[col] / hist.groupby("FY")[col].transform("sum"))
        for s_ in states:
            z = x[x.State == s_]
            c, V = np.polyfit(z.FY, np.log(z.sh), 1, cov=True)
            fits[(col, s_)] = (c[0], np.sqrt(V[0, 0]))
    e = e_cs()
    reg_of = base.region.reindex(states).values
    out = np.zeros((n, len(YEARS_ALL), len(REGIONS)))
    for k in range(n):
        ps = np.array([base.loc[s_, "pop"] * np.exp((fits[("pop", s_)][0] + rng.standard_normal() * fits[("pop", s_)][1]) * t) for s_ in states])
        gs = np.array([base.loc[s_, "gsdp_real"] * np.exp((fits[("gsdp_real", s_)][0] + rng.standard_normal() * fits[("gsdp_real", s_)][1]) * t) for s_ in states])
        ps = ps / ps.sum(axis=0) * P; gs = gs / gs.sum(axis=0) * G
        idx = ps * (gs / ps) ** e
        for j, r in enumerate(REGIONS):
            out[k, :, j] = idx[reg_of == r].sum(axis=0)
        out[k] /= out[k].sum(axis=1, keepdims=True)
    return out


def regional_quantiles(rec, mc_total, nat_fc, seed=SEED):
    """P10/P90 from national draws x share draws; P50 := reconciled share x national P50 (coherent)."""
    rng = np.random.default_rng(seed + 7)
    sd = share_draws(nat_fc)
    base_sh = rec.div(rec.sum(axis=1), axis=0).values
    # share draws are re-centred on the reconciled shares (they carry only the share uncertainty)
    centre = sd.mean(axis=0)
    pick = rng.integers(0, sd.shape[0], size=mc_total.shape[0])
    sh = base_sh[None] * sd[pick] / centre[None]
    sh = sh / sh.sum(axis=2, keepdims=True)
    draws = sh * mc_total[:, :, None]
    q10 = np.percentile(draws, 10, axis=0); q90 = np.percentile(draws, 90, axis=0)
    p50 = base_sh * np.percentile(mc_total, 50, axis=0)[:, None]
    return q10, p50, q90, draws
