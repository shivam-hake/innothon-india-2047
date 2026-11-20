"""Driver trajectories to 2047 from the organiser CSV only - every parameter estimated from the CSV, no assumed values.

Population: the all-India CSV growth rate falls geometrically (FY2008-FY2025); ln(growth) = a + b*FY is fitted by OLS and
            extrapolated. Uncertainty = the slope's standard error (z-shock).
GDP:        CSV real GSDP CAGR FY2012-FY2024 (one constant-price base). Uncertainty = bootstrap distribution of the
            mean of 23 resampled CSV annual growth rates FY2013-FY2025 (P10 / P50 / P90 define the Low / Base / High
            scenarios).
State shares: each state's CSV log-share trend in population and in real GSDP (FY2016-FY2025), extrapolated.
Urbanisation: neither NPP nor the CSV contains urbanisation data, so it is not modelled separately; its effect is
            inside the income term (GSDP per person). Stated as a limitation.
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm
from src.config import PROC, BASE_FY, HORIZON, SEED

YEARS_F = np.arange(BASE_FY + 1, HORIZON + 1)
YEARS_ALL = np.arange(BASE_FY, HORIZON + 1)
NAT = None
_TR = {}
N_BOOT = 20000


def nat():
    global NAT
    if NAT is None:
        NAT = pd.read_csv(PROC / "national_series_fy.csv", index_col=0)
    return NAT


def csv_national():
    """All-India CSV population and real GSDP for every CSV year (FY2007-FY2025)."""
    sp = pd.read_csv(PROC / "state_panel.csv")
    return sp.groupby("FY").agg(population=("pop", "sum"), gdp=("gsdp_real", "sum"))


def csv_trends():
    if not _TR:
        c = csv_national()
        g = c.population.pct_change().dropna()
        m = sm.OLS(np.log(g.values), sm.add_constant(g.index.values.astype(float))).fit()
        _TR["pop_a"], _TR["pop_b"] = float(m.params[0]), float(m.params[1])
        _TR["pop_se_b"] = float(m.bse[1])
        _TR["pop_decay"] = float(np.expm1(m.params[1]))
        _TR["pop_growth_base"] = float(g.loc[BASE_FY])
        _TR["gdp_cagr"] = float((c.loc[BASE_FY, "gdp"] / c.loc[2012, "gdp"]) ** (1 / (BASE_FY - 2012)) - 1)
        gg = c.gdp.loc[2012:].pct_change().dropna()            # FY2013-FY2025, constant-price base
        rng = np.random.default_rng(SEED)
        H = HORIZON - BASE_FY
        boot = np.exp(np.log1p(rng.choice(gg.values, size=(N_BOOT, H))).mean(axis=1)) - 1
        _TR["gdp_growth_obs"] = gg.round(5).to_dict()
        _TR["gdp_boot_p10"], _TR["gdp_boot_p50"], _TR["gdp_boot_p90"] = (float(np.percentile(boot, q)) for q in (10, 50, 90))
        _TR["gdp_boot"] = boot
    return _TR


def scenario_cagr(case="base"):
    t = csv_trends()
    return {"low": t["gdp_boot_p10"], "base": t["gdp_cagr"], "high": t["gdp_boot_p90"]}[case]


def pop_path(z=0.0):
    t = csv_trends()
    z = np.atleast_1d(np.asarray(z, float))
    b = t["pop_b"] + z[:, None] * t["pop_se_b"]
    # keep the fitted growth at the base year, perturb only the slope
    lg0 = t["pop_a"] + t["pop_b"] * BASE_FY
    g = np.exp(lg0 + b * (YEARS_ALL[None, 1:] - BASE_FY))
    P0 = nat().loc[BASE_FY, "population"]
    return P0 * np.c_[np.ones((len(z), 1)), np.cumprod(1 + g, axis=1)]


def gdp_path(cagr):
    g = np.atleast_1d(np.asarray(cagr, float))
    return nat().loc[BASE_FY, "gdp"] * (1 + g[:, None]) ** (YEARS_ALL - BASE_FY)[None, :]


def national_drivers(cagr=None, pop_z=0.0, case="base"):
    cagr = scenario_cagr(case) if cagr is None else cagr
    P, G = pop_path(pop_z), gdp_path(cagr)
    if P.shape[0] != G.shape[0]:
        n = max(P.shape[0], G.shape[0])
        P = np.broadcast_to(P, (n, P.shape[1])).copy(); G = np.broadcast_to(G, (n, G.shape[1])).copy()
    return dict(years=YEARS_ALL, pop=P, gdp=G, gdp_pc=G * 1e7 / P)


def regional_drivers(nd):
    """Project state population and GSDP shares with their CSV log-share trends (FY2016-FY2025) and aggregate to
    the 5 grid regions. nd: national_drivers output (single path)."""
    sp = pd.read_csv(PROC / "state_panel.csv")
    hist = sp[sp.FY.between(2016, 2025)]
    P, G = nd["pop"][0], nd["gdp"][0]
    states = sorted(sp.State.unique())
    base = sp[sp.FY == BASE_FY].set_index("State")
    ps = hist.assign(sh=hist["pop"] / hist.groupby("FY")["pop"].transform("sum"))
    gs = hist.assign(sh=hist.gsdp_real / hist.groupby("FY").gsdp_real.transform("sum"))

    def slope(df, st):
        x = df[df.State == st]
        return np.polyfit(x.FY, np.log(x.sh), 1)[0]
    t = YEARS_ALL - BASE_FY
    pop_sh = pd.DataFrame({st: base.loc[st, "pop"] / base["pop"].sum() * np.exp(slope(ps, st) * t) for st in states}, index=YEARS_ALL)
    gsdp_sh = pd.DataFrame({st: base.loc[st, "gsdp_real"] / base["gsdp_real"].sum() * np.exp(slope(gs, st) * t) for st in states}, index=YEARS_ALL)
    pop_sh = pop_sh.div(pop_sh.sum(axis=1), axis=0); gsdp_sh = gsdp_sh.div(gsdp_sh.sum(axis=1), axis=0)
    rows = [pd.DataFrame({"State": states, "FY": y, "pop": pop_sh.loc[y].values * P[i], "gsdp": gsdp_sh.loc[y].values * G[i]})
            for i, y in enumerate(YEARS_ALL)]
    st = pd.concat(rows)
    st["region"] = st.State.map(base["region"])
    reg = st.groupby(["region", "FY"]).agg(pop=("pop", "sum"), gsdp=("gsdp", "sum")).reset_index()
    reg["gsdp_pc"] = reg.gsdp * 1e7 / reg["pop"]
    return st, reg
