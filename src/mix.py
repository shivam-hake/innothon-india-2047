"""Step 02 - Regional generation mix from NPP + CSV data only (no assumed values, no cost or resource parameters).

The mix is built as nested SHARES, each forecast by a model family chosen by out-of-sample back-test:

  level 1  national source shares          Thermal / Hydro / Nuclear / RES      NPP history FY2007-FY2024
  level 2a coal vs gas inside thermal      Coal / Gas                           NPP sub-report 16, FY2019-FY2026
  level 2b solar / wind / other inside RES Solar / Wind / Other RE              CSV RE-fleet composition FY2007-FY2024 *
  level 3  regional share of each source   NR / WR / SR / ER / NER              NPP sub-report 16 (conventional),
                                                                                CSV RE-fleet composition (RE) *
  * NPP publishes RES only as one all-India total. The CSV installed-capacity columns are used here ONLY as a
    composition (dimensionless shares) to apportion that NPP total - never for the level of generation.

Model families (candidate windows fixed in advance):
  const(w)  mean share of the last w training years                    (no change)
  logit(s)  multinomial-logit trend: ln(share_k / share_ref) linear in FY, fitted from year s   (diffusion)
  incr(w)   increments of each source = OLS slopes of its last w years; future growth of the total is split in
            those proportions                                         (recent additions continue)
For each panel the best window of each family is chosen on a hold-out; families are blended with inverse-MAE weights.
Generation by technology = national total (forecast) x level-1 share x level-2 share; by region x level-3 share.
"""
import numpy as np
import pandas as pd
from src.config import PROC, OUT, REGIONS, TECHS, BASE_FY, HORIZON, SCENARIOS

YEARS = np.arange(BASE_FY, HORIZON + 1)
SEL = []


# ------------------------------------------------------------------ share model families
def _norm(df):
    return df.div(df.sum(axis=1), axis=0)


def f_const(levels, train_end, years, w, **_):
    sh = _norm(levels.loc[:train_end]).iloc[-w:].mean()
    return pd.DataFrame([sh.values] * len(years), index=years, columns=levels.columns)


def f_logit(levels, train_end, years, start, **_):
    x = _norm(levels.loc[start:train_end])
    live = [c for c in x.columns if (x[c] > 0).all()]
    dead = [c for c in x.columns if c not in live]
    ref = x[live].mean().idxmax()
    out = pd.DataFrame(index=years, columns=x.columns, dtype=float)
    for y in years:
        v = {c: np.exp(np.polyval(np.polyfit(x.index, np.log(x[c] / x[ref]), 1), y)) for c in live}
        tot = sum(v.values())
        fixed = x[dead].iloc[-1].sum() if dead else 0.0
        for c in live:
            out.loc[y, c] = v[c] / tot * (1 - fixed)
        for c in dead:
            out.loc[y, c] = x[c].iloc[-1]
    return out


def f_incr(levels, train_end, years, w, totals, **_):
    x = levels.loc[train_end - w + 1:train_end]
    fit = {c: np.polyfit(x.index, x[c], 1) for c in x.columns}
    slope = pd.Series({c: fit[c][0] for c in x.columns})
    lev_T = pd.Series({c: np.polyval(fit[c], train_end) for c in x.columns}).clip(lower=0)
    a = slope.clip(lower=0)
    a = a / a.sum()
    out = []
    for y in years:
        X = totals[y] * lev_T.sum() / totals[train_end] if y != train_end else lev_T.sum()
        v = lev_T + max(X - lev_T.sum(), 0.0) * a
        out.append(v / v.sum())
    return pd.DataFrame(out, index=years, columns=levels.columns)


FAMILIES = {"const": f_const, "logit": f_logit, "incr": f_incr}


def select(name, levels, train_end, test_years, cands, totals=None):
    """Back-test every candidate, keep the best per family, inverse-MAE weights across families."""
    act = _norm(levels).loc[test_years]
    res = []
    for fam, args in cands:
        for a in args:
            kw = {"w": a} if fam in ("const", "incr") else {"start": a}
            p = FAMILIES[fam](levels, train_end, test_years, totals=totals, **kw)
            mae = 100 * float((p - act).abs().values.mean())
            res.append(dict(panel=name, family=fam, param=a, MAE_pp=mae))
    r = pd.DataFrame(res)
    best = r.loc[r.groupby("family").MAE_pp.idxmin()].copy()
    best["weight"] = (1 / best.MAE_pp.clip(lower=0.05)) / (1 / best.MAE_pp.clip(lower=0.05)).sum()
    r = r.merge(best[["family", "param", "weight"]], on=["family", "param"], how="left").fillna({"weight": 0.0})
    r["train_end"], r["test"] = train_end, f"{min(test_years)}-{max(test_years)}"
    SEL.append(r)
    return best


def blend(levels, best, years, totals=None):
    last = levels.index.max()
    out = 0
    for b in best.itertuples():
        kw = {"w": b.param} if b.family in ("const", "incr") else {"start": b.param}
        out = out + b.weight * FAMILIES[b.family](levels, last, years, totals=totals, **kw)
    return _norm(out.astype(float))


# ------------------------------------------------------------------ data panels
def panels():
    h = pd.read_csv(PROC / "national_series_fy.csv", index_col=0)
    rf = pd.read_csv(PROC / "npp_region_fuel_fy.csv")
    rf = rf[rf.region.isin(REGIONS)]
    comp = pd.read_csv(PROC / "csv_re_composition.csv")
    comp = comp[~comp.provisional]
    nat4 = h[["Thermal", "Hydro", "Nuclear", "RES"]]
    cg = rf.groupby("FY")[["Coal", "Gas"]].sum()
    reg_fuel = {f: rf.pivot(index="FY", columns="region", values=f)[REGIONS] for f in ("Coal", "Gas", "Hydro", "Nuclear")}
    fleet = comp[comp.kind == "fleet_index"].set_index("FY").share
    tech = comp[comp.kind == "tech_share_of_national_RE"].pivot(index="FY", columns="tech", values="share")[["Solar", "Wind", "Other RE"]]
    tech_lev = tech.mul(fleet, axis=0)                          # dimensionless (FY2024 fleet = 1)
    reg_re = {t: comp[(comp.kind == "region_share_of_tech") & (comp.tech == t)].pivot(index="FY", columns="region", values="share")[REGIONS].fillna(0)
              for t in ("Solar", "Wind", "Other RE")}
    return dict(h=h, nat4=nat4, cg=cg, reg_fuel=reg_fuel, tech_lev=tech_lev, fleet=fleet, reg_re=reg_re)


def fit_all(P):
    tot = P["nat4"].sum(axis=1)
    M = {}
    M["nat4"] = select("L1 national sources (NPP)", P["nat4"], 2018, list(range(2019, 2025)),
                       [("const", [1, 3]), ("logit", [2007, 2010, 2013]), ("incr", [5, 8, 10])], totals=tot)
    M["cg"] = select("L2a coal vs gas (NPP sub-16)", P["cg"], 2022, list(range(2023, 2027)), [("const", [1, 3]), ("logit", [2019])])
    M["tech"] = select("L2b solar/wind/other in RES (CSV composition)", P["tech_lev"], 2019, list(range(2020, 2025)),
                       [("const", [1, 3]), ("logit", [2007, 2012, 2016]), ("incr", [3, 5, 8])], totals=P["fleet"])
    for f, lev in P["reg_fuel"].items():
        M["reg_" + f] = select(f"L3 regional share of {f} (NPP sub-16)", lev, 2023, [2024, 2025, 2026], [("const", [1, 3]), ("logit", [2019])])
    for t, sh in P["reg_re"].items():
        M["reg_" + t] = select(f"L3 regional share of {t} (CSV composition)", sh, 2019, list(range(2020, 2025)),
                               [("const", [1, 3]), ("logit", [2012, 2016])])
    return M


# ------------------------------------------------------------------ build the mix
def build(totals_by_scen, P=None, M=None):
    """totals_by_scen: {scenario: pd.Series(FY -> national TWh)} including BASE_FY actual."""
    P = P or panels()
    M = M or fit_all(P)
    h = P["h"]
    rows, shares = [], []
    fyears = YEARS[1:]
    for scen, tot in totals_by_scen.items():
        tot_all = pd.concat([P["nat4"].sum(axis=1).loc[:BASE_FY - 1], tot])
        s4 = blend(P["nat4"], M["nat4"], fyears, totals=tot_all)
        s4.loc[BASE_FY] = _norm(P["nat4"]).loc[BASE_FY]
        s4 = s4.sort_index()
        cg = blend(P["cg"], M["cg"], [y for y in fyears if y > P["cg"].index.max()])
        cg = pd.concat([_norm(P["cg"]), cg]).loc[BASE_FY:]
        res_tot = (tot * s4.RES).reindex(YEARS)
        fl = pd.concat([P["fleet"], res_tot.loc[BASE_FY + 1:] / res_tot.loc[BASE_FY] * P["fleet"].loc[BASE_FY]])
        tech = blend(P["tech_lev"], M["tech"], fyears, totals=fl)
        tech.loc[BASE_FY] = _norm(P["tech_lev"]).loc[BASE_FY]
        tech = tech.sort_index()
        nat = pd.DataFrame(index=YEARS, columns=TECHS, dtype=float)
        nat["Coal"] = tot * s4.Thermal * cg.Coal
        nat["Gas"] = tot * s4.Thermal * cg.Gas
        nat["Hydro"] = tot * s4.Hydro
        nat["Nuclear"] = tot * s4.Nuclear
        for t in ("Solar", "Wind", "Other RE"):
            nat[t] = tot * s4.RES * tech[t]
        regsh = {}
        for f in ("Coal", "Gas", "Hydro", "Nuclear"):
            lev = P["reg_fuel"][f]
            fut = blend(lev, M["reg_" + f], [y for y in fyears if y > lev.index.max()])
            regsh[f] = pd.concat([_norm(lev), fut]).loc[BASE_FY:]
        for t in ("Solar", "Wind", "Other RE"):
            lev = P["reg_re"][t]
            fut = blend(lev, M["reg_" + t], [y for y in fyears if y > lev.index.max()])
            regsh[t] = pd.concat([_norm(lev), fut]).loc[BASE_FY:]
        for y in YEARS:
            for t in TECHS:
                for r in REGIONS:
                    rows.append(dict(scenario=scen, year=int(y), region=r, tech=t, twh=float(nat.loc[y, t] * regsh[t].loc[y, r])))
        sh = pd.concat([s4.add_prefix("L1_"), cg.add_prefix("L2a_"), tech.add_prefix("L2b_")], axis=1).loc[YEARS]
        sh["scenario"] = scen
        shares.append(sh)
    mp = pd.DataFrame(rows)
    # anchor the base year to the clean FY2024 regional mix (identical by construction, guards rounding)
    return mp, pd.concat(shares).rename_axis("year").reset_index(), M


def validate(mp):
    """Out of sample: FY2025-26 conventional (coal, gas, hydro, nuclear) forecast vs NPP actuals, by region and fuel."""
    act = pd.read_csv(PROC / "npp_region_fuel_fy.csv")
    act = act[act.region.isin(REGIONS) & (act.FY > BASE_FY)].melt(id_vars=["FY", "region"], var_name="tech", value_name="actual")
    f = mp[(mp.scenario == "Base") & mp.tech.isin(["Coal", "Gas", "Hydro", "Nuclear"])].rename(columns={"year": "FY", "twh": "forecast"})
    v = act.merge(f[["FY", "region", "tech", "forecast"]], on=["FY", "region", "tech"])
    nat = v.groupby(["FY", "tech"])[["actual", "forecast"]].sum().reset_index().assign(region="India")
    tot = v.groupby("FY")[["actual", "forecast"]].sum().reset_index().assign(region="India", tech="All conventional")
    v = pd.concat([v, nat, tot], ignore_index=True)
    v["diff_pct"] = 100 * (v.forecast / v.actual - 1)
    return v


def kpis(mp, req):
    g = mp.groupby(["scenario", "year", "region"]).twh.sum().rename("generation_twh").reset_index()
    nf = mp[~mp.tech.isin(["Coal", "Gas"])].groupby(["scenario", "year", "region"]).twh.sum().rename("nonfossil")
    re = mp[mp.tech.isin(["Solar", "Wind", "Other RE"])].groupby(["scenario", "year", "region"]).twh.sum().rename("res")
    k = g.merge(nf.reset_index(), on=["scenario", "year", "region"]).merge(re.reset_index(), on=["scenario", "year", "region"])
    k = k.merge(req, on=["scenario", "year", "region"], how="left")
    nat = k.groupby(["scenario", "year"])[["generation_twh", "nonfossil", "res", "requirement_twh"]].sum().reset_index().assign(region="India")
    k = pd.concat([k, nat], ignore_index=True)
    k["nonfossil_share"] = k.nonfossil / k.generation_twh
    k["res_share"] = k.res / k.generation_twh
    k["net_export_twh"] = k.generation_twh - k.requirement_twh
    return k


def run():
    SEL.clear()
    fr = pd.read_csv(OUT / "forecast_region_year.csv")
    h = pd.read_csv(PROC / "national_series_fy.csv", index_col=0)
    tots = {}
    for scen in SCENARIOS:
        s = fr[(fr.region == "India") & (fr.scenario == scen)].set_index("year").p50
        s.loc[BASE_FY] = h.loc[BASE_FY, "Total"]
        tots[scen] = s.sort_index()
    mp, sh, M = build(tots)
    mp.to_csv(OUT / "mix_pathway.csv", index=False)
    sh.to_csv(OUT / "mix_shares_national.csv", index=False)
    mp[(mp.scenario == "Base") & (mp.year == 2047)].drop(columns=["scenario", "year"]).to_csv(OUT / "mix_region_2047.csv", index=False)
    sel = pd.concat(SEL, ignore_index=True)
    sel.to_csv(OUT / "mix_model_selection.csv", index=False)
    v = validate(mp)
    v.to_csv(OUT / "mix_validation.csv", index=False)
    req = fr[fr.region != "India"][["scenario", "year", "region", "p50"]].rename(columns={"p50": "requirement_twh"})
    k = kpis(mp, req)
    k.to_csv(OUT / "kpis.csv", index=False)
    kb = k[(k.scenario == "Base") & (k.region == "India")].set_index("year")
    vv = v[(v.region == "India") & (v.tech == "All conventional")]
    print(f"[mix] Base 2047: non-fossil {100*kb.loc[2047,'nonfossil_share']:.0f}% (FY{BASE_FY} {100*kb.loc[BASE_FY,'nonfossil_share']:.0f}%), "
          f"RES {100*kb.loc[2047,'res_share']:.0f}%; FY2025-26 conventional out-of-sample error "
          f"{', '.join(f'{r.diff_pct:+.1f}%' for r in vv.itertuples())}")
    return mp, k


if __name__ == "__main__":
    run()
