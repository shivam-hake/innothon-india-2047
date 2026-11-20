"""Monte Carlo and one-at-a-time sensitivity - every distribution estimated from NPP / CSV data, none assumed.

Uncertain inputs:
  * GDP CAGR FY2024-47: bootstrap of the CSV annual real GSDP growth rates FY2013-FY2025 (features.csv_trends).
    Base scenario draws from the full bootstrap; Low / High fix GDP at its P10 / P90 and keep the other sources.
  * Population: slope of the fitted log growth-rate trend ~ N(b, SE_b) from the CSV regression.
  * Model elasticities: one common z ~ N(0,1) scaled by each model's own estimated standard error
    (M1 income elasticity, M2 intensity drift, M3 GDP elasticity).
  * Model residual: the ensemble's back-test errors (FY2019-24) are resampled as a level shift that persists.
"""
import numpy as np
import pandas as pd
from src.config import SEED, OUT
from src.features import csv_trends, scenario_cagr
from src.forecast.ensemble import national_forecast, backtest

Z90 = 1.2815515655446004


def _bt_errors():
    bt, preds, _ = backtest()
    return (preds["Ensemble"] / preds["Actual"] - 1).values


def run_mc(case="base", n=5000, seed=SEED):
    rng = np.random.default_rng(seed + {"low": 1, "base": 0, "high": 2}[case])
    t = csv_trends()
    cagr = rng.choice(t["gdp_boot"], size=n) if case == "base" else np.full(n, scenario_cagr(case))
    inp = dict(cagr=cagr, pop_z=rng.standard_normal(n), z_elast=rng.standard_normal(n),
               resid=rng.choice(_bt_errors(), size=n))
    fc = national_forecast(cagr=inp["cagr"], pop_z=inp["pop_z"], z_elast=inp["z_elast"])
    tot = fc["total"] * (1 + inp["resid"][:, None] * (np.arange(fc["total"].shape[1]) > 0)[None, :])
    return dict(total=tot), inp


def quantiles(mc, q=(10, 50, 90)):
    v = np.percentile(mc["total"], q, axis=0)
    return pd.DataFrame({f"p{qq}": v[i] for i, qq in enumerate(q)})


def tornado(case="base"):
    """2047 swing for each input at its data-derived P10 / P90 (others at base)."""
    t = csv_trends()
    base = float(national_forecast(case=case)["total"][0, -1])
    e = _bt_errors()
    items = [
        ("GDP CAGR (CSV bootstrap P10 / P90)", dict(cagr=t["gdp_boot_p10"]), dict(cagr=t["gdp_boot_p90"])),
        ("Model elasticities (-/+1.28 SE)", dict(z_elast=-Z90), dict(z_elast=Z90)),
        ("Population trend slope (-/+1.28 SE)", dict(pop_z=-Z90), dict(pop_z=Z90)),
    ]
    rows = []
    for name, lo, hi in items:
        l = float(national_forecast(case=case, **lo)["total"][0, -1]); h = float(national_forecast(case=case, **hi)["total"][0, -1])
        rows.append(dict(input=name, low=l - base, high=h - base))
    rows.append(dict(input="Back-test error (P10 / P90)", low=base * np.percentile(e, 10), high=base * np.percentile(e, 90)))
    singles = [float(national_forecast(case=case, only=i)["total"][0, -1]) for i in range(3)]
    rows.append(dict(input="Model choice (single model min / max)", low=min(singles) - base, high=max(singles) - base))
    d = pd.DataFrame(rows)
    d["swing"] = d.high - d.low
    d["base_2047"] = base
    return d.sort_values("swing", ascending=False).reset_index(drop=True)
