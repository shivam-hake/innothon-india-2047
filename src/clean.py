"""Clean the organiser CSV (Population + GSDP only), build the 5-region state panel, build the national
generation target series from the National Power Portal, run NPP internal-consistency checks, and write
the data-quality report.

DATA POLICY: only (1) npp.gov.in extracts and (2) the organiser CSV; no assumed values.
COMPLIANCE: the CSV 'Installed - *' columns are installed CAPACITY (MW). They never enter the demand models or any
comparison. Their composition (dimensionless shares) is saved separately (csv_re_composition.csv) and used only to
apportion NPP's single RES generation total among solar / wind / other and among regions.
"""
import numpy as np
import pandas as pd
from src.config import RAW, PROC, OUT, STATE_REGION, BASE_FY, REGIONS, TECHS

CAP_COLS_PREFIX = "Installed - "
DQ = []


def log(msg):
    DQ.append(msg)


# ------------------------------------------------------------------ organiser CSV
def load_csv():
    d = pd.read_csv(RAW / "renewable_energy_dataset.csv")
    log(f"Organiser CSV: {len(d)} rows, {d.State.nunique()} states/UTs, calendar years {d.Year.min()}-{d.Year.max()} "
        f"(treated as FY{d.Year.min()+1}-FY{d.Year.max()+1}, i.e. CSV year Y = fiscal year Y-(Y+1)).")
    cap_cols = [c for c in d.columns if c.startswith(CAP_COLS_PREFIX)]
    log(f"Columns {cap_cols} are INSTALLED CAPACITY (MW) -> never used for the level of generation or any comparison; "
        f"only their composition (shares) apportions NPP's RES total among solar / wind / other and regions.")
    re_composition(d, cap_cols)
    a = d[d.Year == 2023].set_index("State")[cap_cols]
    b = d[d.Year == 2024].set_index("State")[cap_cols]
    same = (a.reindex(b.index) - b).abs().sum(axis=1) < 1e-6
    log(f"2024 capacity rows identical to 2023 (carry-forward): {int(same.sum())} of {len(b)} -> 2024 rows flagged PROVISIONAL.")
    zone = d.drop_duplicates("State")[["State", "Zone"]]
    zmap = {"North": "NR", "West": "WR", "South": "SR", "East": "ER", "North-East": "NER", "Central": "WR*"}
    diff = zone[zone.Zone.map(zmap) != zone.State.map(STATE_REGION)]
    log("CSV 'Zone' differs from the official CEA 5-region grid mapping for: " +
        ", ".join(f"{r.State} ({r.Zone}->{STATE_REGION[r.State]})" for r in diff.itertuples()) +
        ". 'Central' is not a grid region. Remapped to NR/WR/SR/ER/NER.")
    d = d.drop(columns=cap_cols + ["Zone"])
    return d.rename(columns={"Population": "pop", "GSDP (crore INR)": "gsdp_csv"})


def re_composition(d, cap_cols):
    """Dimensionless composition of the CSV RE fleet: (a) solar / wind / other share of national RE, (b) each region's
    share of national solar, wind, other. CSV year Y -> FY Y+1. MW values are NOT saved."""
    x = d.copy()
    x["region"] = x.State.map(STATE_REGION)
    x["Solar"] = x["Installed - Solar Power"]; x["Wind"] = x["Installed - Wind Power"]
    x["Other RE"] = x["Installed - Bio-Mass Power"] + x["Installed - Small Hydro Power"] + x["Installed - Waste to Energy"]
    g = x.groupby(["Year", "region"])[["Solar", "Wind", "Other RE"]].sum()
    nat = g.groupby("Year").sum()
    rows = []
    for t in ("Solar", "Wind", "Other RE"):
        sh = nat[t] / nat.sum(axis=1)
        rows += [dict(FY=y + 1, kind="tech_share_of_national_RE", region="India", tech=t, share=v) for y, v in sh.items()]
        rs = g[t].unstack("region").div(nat[t], axis=0)
        rows += [dict(FY=y + 1, kind="region_share_of_tech", region=r, tech=t, share=rs.loc[y, r])
                 for y in rs.index for r in rs.columns]
    tot = nat.sum(axis=1)
    rows += [dict(FY=y + 1, kind="fleet_index", region="India", tech="All RE", share=v / tot.loc[d.Year.max() - 1])
             for y, v in tot.items()]          # dimensionless index (FY2024 = 1), used only for incremental composition
    c = pd.DataFrame(rows)
    c["provisional"] = c.FY == d.Year.max() + 1
    c.to_csv(PROC / "csv_re_composition.csv", index=False)


def fix_panel(d):
    states = sorted(d.State.unique())
    years = list(range(2006, 2025))
    d = d.set_index(["State", "Year"]).reindex(pd.MultiIndex.from_product([states, years], names=["State", "Year"])).reset_index()
    d["imputed_pop"] = d["pop"].isna()
    # interior gaps (Telangana 2013) -> log-linear interpolation
    d["pop"] = d.groupby("State")["pop"].transform(lambda s: np.exp(np.log(s).interpolate(limit_area="inside")))
    # leading gaps (Delhi pre-2009, Chandigarh pre-2013) -> backcast at the state's own first-3-year CSV growth
    for st, g in d.groupby("State"):
        s = g.set_index("Year")["pop"]
        fv = s.first_valid_index()
        if fv > 2006:
            gr = (s[fv + 3] / s[fv]) ** (1 / 3) - 1
            for y in range(fv - 1, 2005, -1):
                s[y] = s[y + 1] / (1 + gr)
            d.loc[g.index, "pop"] = s.values
            log(f"{st}: CSV starts {fv}; population backcast to 2006 at its own {100*gr:.2f}%/yr (CSV {fv}-{fv+3}).")
    log("Telangana 2013 row missing -> log-linear interpolation (this row causes the dip in the raw CSV all-India "
        "population for 2013: 1.206 bn vs 1.225 bn in 2012).")
    return d


def real_gsdp(d):
    """CSV GSDP has a base break at 2011 (2011 all-state total = 2.20x 2010). 2011+ is one constant-price series
    (constant 2011-12 prices); pre-2011 is a different base. We splice: pre-2011 levels are rebuilt backwards from
    2011 using each state's OWN CSV growth rates; states whose pre-2011 GSDP is constant (imputed: Telangana, J&K,
    A&N, Lakshadweep) use the CSV aggregate growth of the other states. 2024 repeats 2023 (-0.2%, carry-forward)
    -> replaced by 2023 x (1 + CSV 2023 growth)."""
    d = d.copy()
    piv = d.pivot(index="Year", columns="State", values="gsdp_csv")
    pre = piv.loc[2006:2010]
    varying = [c for c in piv.columns if pre[c].notna().sum() >= 3 and pre[c].dropna().nunique() > 1]
    agg_gr = pre[varying].sum(axis=1).pct_change()           # aggregate growth of states with real pre-2011 data
    out = piv.copy()
    for st in piv.columns:
        s = piv[st].copy()
        for y in range(2010, 2005, -1):
            if st in varying and not np.isnan(pre[st].get(y, np.nan)) and not np.isnan(pre[st].get(y + 1, np.nan)) and y + 1 <= 2010:
                gr = pre[st][y + 1] / pre[st][y] - 1
            elif st in varying and y == 2010:
                gr = pre[st][2010] / pre[st][2009] - 1
            else:
                gr = agg_gr.get(y + 1, agg_gr.mean())
            s[y] = s[y + 1] / (1 + gr)
        out[st] = s
    log(f"GSDP base break at 2011 spliced with the CSV's own pre-2011 growth rates ({len(varying)} states) or CSV "
        f"aggregate growth (constant/imputed series: {', '.join(c for c in piv.columns if c not in varying)}).")
    # Delhi/Chandigarh leading gaps are now filled by the backward loop (they use the aggregate growth)
    tot = out.sum(axis=1)
    g23 = tot[2023] / tot[2022] - 1
    out.loc[2024] = out.loc[2023] * (1 + g23)
    log(f"GSDP 2022-2024 show imputation (linear 2021->2023 increments, fractional values); 2024 total = 2023 x 0.998 "
        f"(carry-forward) -> 2024 set to 2023 x (1 + {100*g23:.2f}%) (the CSV's own 2023 growth). Flagged PROVISIONAL.")
    long = out.stack().rename("gsdp_real").reset_index()
    d = d.drop(columns=["gsdp_csv"]).merge(long, on=["Year", "State"])
    return d


def build_state_panel():
    d = fix_panel(load_csv())
    d = real_gsdp(d)
    d["region"] = d.State.map(STATE_REGION)
    assert d.region.notna().all(), d[d.region.isna()].State.unique()
    log("Coverage: Ladakh and Dadra & Nagar Haveli and Daman & Diu are not in the CSV (J&K rows include Ladakh before "
        "2019); together <0.1% of population. No external data is added to fill them.")
    d["FY"] = d.Year + 1
    d["gsdp_pc"] = d.gsdp_real * 1e7 / d["pop"]           # INR per person, constant 2011-12 prices
    d["provisional"] = d.FY >= 2023
    keep = ["State", "region", "FY", "pop", "gsdp_real", "gsdp_pc", "provisional", "imputed_pop"]
    d = d[keep].sort_values(["State", "FY"]).reset_index(drop=True)
    d.to_csv(PROC / "state_panel.csv", index=False)
    r = d.groupby(["region", "FY"]).agg(pop=("pop", "sum"), gsdp_real=("gsdp_real", "sum")).reset_index()
    r["gsdp_pc"] = r.gsdp_real * 1e7 / r["pop"]
    r.to_csv(PROC / "region_panel.csv", index=False)
    return d, r


# ------------------------------------------------------------------ national generation (NPP)
def build_national(sp):
    h = pd.read_csv(PROC / "npp_history_national_twh.csv", index_col=0)
    rf = pd.read_csv(PROC / "npp_region_fuel_fy.csv")
    fy = h.loc[2007:BASE_FY, ["Hydro", "Thermal", "RES", "Nuclear"]].copy()
    fy["Total"] = fy.sum(axis=1)
    reg = rf[rf.region.isin(REGIONS)].groupby("FY")[["Coal", "Gas", "Hydro", "Nuclear"]].sum()
    fy["Coal"] = np.nan; fy["Gas"] = np.nan
    for y in reg.index:
        if y in fy.index:
            gs = reg.loc[y, "Gas"] / (reg.loc[y, "Coal"] + reg.loc[y, "Gas"])
            fy.loc[y, "Gas"] = fy.loc[y, "Thermal"] * gs
            fy.loc[y, "Coal"] = fy.loc[y, "Thermal"] * (1 - gs)
    nat = sp.groupby("FY").agg(population=("pop", "sum"), gdp=("gsdp_real", "sum"))
    d = fy.join(nat, how="left")
    d["gen_pc_kwh"] = d.Total * 1e9 / d.population
    d["gdp_pc"] = d.gdp * 1e7 / d.population
    d["covid"] = (d.index == 2021).astype(int)
    d.to_csv(PROC / "national_series_fy.csv")
    # conventional actuals after BASE_FY (validation only; NPP has no RES after FY2024)
    v = reg.loc[BASE_FY + 1:].copy()
    v["Thermal"] = v.Coal + v.Gas
    v.to_csv(PROC / "npp_conventional_after_base.csv")
    log(f"National target = NPP all-India utility generation (hydro + thermal + RES + nuclear, excl. Bhutan import), "
        f"FY2007-FY{BASE_FY} from the NPP history endpoint - every year an NPP actual. NPP publishes no RES after FY{BASE_FY}, "
        f"so FY{BASE_FY} is the base year; FY{BASE_FY+1}-FY{reg.index.max()} conventional actuals (NPP sub-report 16) are kept "
        f"for out-of-sample validation.")
    log(f"Estimation sample FY2007-FY{BASE_FY} ({len(d)} years): generation {d.Total.iloc[0]:,.0f} -> {d.Total.iloc[-1]:,.0f} TWh "
        f"({100*((d.Total.iloc[-1]/d.Total.iloc[0])**(1/(len(d)-1))-1):.1f}%/yr); CSV population {d.population.iloc[0]/1e9:.3f} -> "
        f"{d.population.iloc[-1]/1e9:.3f} bn; CSV real GSDP {100*((d.gdp.iloc[-1]/d.gdp.iloc[0])**(1/(len(d)-1))-1):.1f}%/yr.")
    return d, rf


def consistency_checks():
    """Four NPP products are compiled separately; their agreement on overlapping years tests our extraction."""
    h = pd.read_csv(PROC / "npp_history_national_twh.csv", index_col=0)
    reg = pd.read_csv(PROC / "npp_region_fy_conventional.csv")
    rf = pd.read_csv(PROC / "npp_region_fuel_fy.csv")
    fuel = pd.read_csv(PROC / "npp_fuelwise_fy_twh.csv", index_col=0)
    s2 = reg[reg.region.isin(REGIONS)].groupby("FY")[["Thermal", "Hydro", "Nuclear"]].sum()
    s16 = rf[rf.region.isin(REGIONS)].groupby("FY")[["Coal", "Gas", "Hydro", "Nuclear"]].sum()
    s16["Thermal"] = s16.Coal + s16.Gas
    S2, S16, HIST, DGR = ("NPP 18-col sub-report 2 (region-wise)", "NPP 18-col sub-report 16 (state/station-wise)",
                          "NPP history endpoint", "NPP DGR17 fuel-wise (31 Mar cumulative)")
    rows = []
    for y in range(2019, BASE_FY + 1):
        for c in ("Thermal", "Hydro", "Nuclear"):
            rows.append(dict(FY=y, item=c, a_source=HIST, a=h.loc[y, c], b_source=S2, b=s2.loc[y, c]))
    for y in s16.index:
        for c in ("Thermal", "Hydro", "Nuclear"):
            rows.append(dict(FY=y, item=c, a_source=S16, a=s16.loc[y, c], b_source=S2, b=s2.loc[y, c]))
    for y in fuel.index:
        rows.append(dict(FY=y, item="Gas", a_source=DGR, a=fuel.loc[y, "gas"] + fuel.loc[y, "diesel_naphtha"], b_source=S16, b=s16.loc[y, "Gas"]))
        rows.append(dict(FY=y, item="Coal + lignite", a_source=DGR, a=fuel.loc[y, "coal"] + fuel.loc[y, "lignite"], b_source=S16, b=s16.loc[y, "Coal"]))
    c = pd.DataFrame(rows)
    c["diff_pct"] = 100 * (c.a / c.b - 1)
    c.to_csv(OUT / "npp_consistency_check.csv", index=False)
    core = c[~c.item.isin(["Gas"])]
    log(f"NPP INTERNAL CONSISTENCY ({len(core)} overlapping FY x fuel comparisons across four NPP products): "
        f"max |difference| {core.diff_pct.abs().max():.2f}%, median {core.diff_pct.abs().median():.3f}% -> "
        f"{'PASS' if core.diff_pct.abs().max() <= 2 else 'CHECK'} vs +/-2% bar. Gas (small, {c[c.item=='Gas'].diff_pct.abs().max():.1f}% "
        f"max) differs because DGR17 counts liquid fuel as 'diesel'.")
    return c


def regional_base_mix(d, rf):
    """FY{BASE_FY} generation by region x technology (TWh). Coal, gas, hydro, nuclear: NPP sub-report 16 regional actuals,
    scaled to the NPP national series (differences < 1%). RES: NPP national actual, apportioned by the CSV RE-fleet
    composition of that year (solar / wind / other share, then each region's share of each)."""
    r = rf[(rf.FY == BASE_FY) & rf.region.isin(REGIONS)].set_index("region").reindex(REGIONS)
    comp = pd.read_csv(PROC / "csv_re_composition.csv")
    c = comp[comp.FY == BASE_FY]
    tsh = c[c.kind == "tech_share_of_national_RE"].set_index("tech").share
    rsh = c[c.kind == "region_share_of_tech"].pivot(index="region", columns="tech", values="share").reindex(REGIONS).fillna(0)
    mix = pd.DataFrame(0.0, index=REGIONS, columns=TECHS)
    th = d.loc[BASE_FY, "Thermal"]
    mix["Coal"] = r.Coal * d.loc[BASE_FY, "Coal"] / r.Coal.sum()
    mix["Gas"] = r.Gas * d.loc[BASE_FY, "Gas"] / r.Gas.sum()
    mix["Hydro"] = r.Hydro * d.loc[BASE_FY, "Hydro"] / r.Hydro.sum()
    mix["Nuclear"] = r.Nuclear * d.loc[BASE_FY, "Nuclear"] / r.Nuclear.sum()
    res = d.loc[BASE_FY, "RES"]
    for t in ("Solar", "Wind", "Other RE"):
        mix[t] = res * tsh[t] * rsh[t].values
    mix.index.name = "region"
    assert abs(mix.values.sum() - d.loc[BASE_FY, "Total"]) < 1e-6
    mix.to_csv(PROC / "mix_region_base.csv")
    log(f"FY{BASE_FY} regional mix: coal, gas, hydro, nuclear = NPP sub-report 16 regional actuals; RES = NPP national actual "
        f"({res:,.1f} TWh) apportioned by the CSV RE-fleet composition (solar {100*tsh['Solar']:.0f}% / wind {100*tsh['Wind']:.0f}% / "
        f"other {100*tsh['Other RE']:.0f}%; regional shares of each). NPP publishes no solar/wind or regional RES split.")
    return mix


def run():
    from src import ingest
    ingest.run()
    sp, rp = build_state_panel()
    d, rf = build_national(sp)
    cc = consistency_checks()
    mix = regional_base_mix(d, rf)
    rep = ["# Data-quality report", "", "Generated by `src/clean.py`. Datasets: National Power Portal (npp.gov.in) and the "
           "organiser CSV only; no assumed values.", ""] + [f"- {l}" for l in DQ]
    rep += ["", "## NPP internal-consistency check (TWh)", "", cc.round(2).to_markdown(index=False),
            "", f"## FY{BASE_FY} regional generation mix (TWh)", "", mix.round(1).to_markdown()]
    (OUT / "data_quality_report.md").write_text("\n".join(rep))
    print("\n".join(DQ))


if __name__ == "__main__":
    run()
