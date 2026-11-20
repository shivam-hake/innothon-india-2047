"""Build docs/parameters.csv (every number the pipeline uses, each estimated from NPP or the organiser CSV) and
outputs/headline.json. The pipeline has no assumed values, so this register lists estimates only."""
import json
import numpy as np
import pandas as pd
from src.config import DOCS, OUT, BASE_FY


def build():
    from src.forecast.ensemble import fitted_models
    from src.features import csv_trends, scenario_cagr
    m1, m2, m3 = (m.summary() for m in fitted_models())
    tr = csv_trends()
    summ = json.loads((OUT / "model_summary.json").read_text())
    w = summ["weights"]
    sel = pd.read_csv(OUT / "mix_model_selection.csv")
    shares = pd.read_csv(OUT / "regional_requirement_shares_base.csv", index_col=0).share
    t = pd.read_csv(OUT / "tornado.csv")
    P = []

    def add(group, name, value, unit, source, how):
        P.append(dict(group=group, parameter=name, value=value, unit=unit, source=source, estimated_how=how))
    add("Drivers", "Real GDP CAGR, Base", round(100 * tr["gdp_cagr"], 2), "%/yr", "CSV GSDP", f"CAGR of all-state real GSDP FY2012-FY{BASE_FY}")
    add("Drivers", "Real GDP CAGR, Low / High (P10 / P90)", f"{100*tr['gdp_boot_p10']:.2f} / {100*tr['gdp_boot_p90']:.2f}", "%/yr", "CSV GSDP",
        "bootstrap of CSV annual growth FY2013-FY2025, 23-year mean")
    add("Drivers", "Population growth decay", round(100 * tr["pop_decay"], 2), "% per year", "CSV population",
        f"OLS ln(growth) on FY, FY2008-FY2025 (SE of slope {tr['pop_se_b']:.4f})")
    add("Drivers", "Population growth at base year", round(100 * tr["pop_growth_base"], 3), "%/yr", "CSV population", "observed")
    add("Drivers", "State population / GSDP share trends", "per state", "log-share slope", "CSV", "OLS FY2016-FY2025, undamped")
    add("Model M1", "Income elasticity of per-capita generation", round(m1["beta_lny"], 3), "-", "NPP + CSV", f"OLS FY2007-FY{BASE_FY}, HAC SE {m1['se_lny']:.3f}")
    add("Model M1", "Residual AR(1) (decay of last residual)", round(m1["resid_ar1"], 3), "-", "NPP + CSV", "lag-1 autocorrelation of M1 residuals")
    add("Model M1", "Quadratic income term (diagnostic)", round(m1["quadratic_test"]["b2"], 3), "-", "NPP + CSV", f"t = {m1['quadratic_test']['t_b2']:.2f}: not identified, not used")
    add("Model M2", "Generation-intensity drift", round(100 * m2["c"], 3), "%/yr", "NPP + CSV", f"OLS ln(G/GDP) on time, SE {100*m2['se_c']:.3f}")
    add("Model M3", "GDP elasticity", round(m3["b_gdp"], 3), "-", "NPP + CSV", f"ARIMAX(1,0,0) MLE, SE {m3['se_gdp']:.3f}")
    add("Model M3", "AR(1) of errors", round(m3["phi"], 3), "-", "NPP + CSV", "ARIMAX MLE")
    for k, v in w.items():
        add("Ensemble", f"Weight {k}", round(v, 3), "-", "NPP + CSV", "inverse hold-out MAPE, train FY2007-18, test FY2019-24")
    for r, v in shares.items():
        add("Regions", f"Base-year requirement share {r}", round(100 * v, 2), "%", "CSV", "Pop x (GSDP per person)^e, e = M1 elasticity")
    for row in sel[sel.weight > 0].itertuples():
        add("Mix", f"{row.panel}: {row.family}({row.param})", round(row.weight, 3), "blend weight", row.panel.split("(")[-1].rstrip(")"),
            f"hold-out MAE {row.MAE_pp:.2f} pp, test {row.test}")
    df = pd.DataFrame(P)
    df.to_csv(DOCS / "parameters.csv", index=False)
    for old in DOCS.glob("assum*.csv"):          # remove a register left by the former version
        old.unlink()

    # headline numbers
    n = pd.read_csv(OUT / "forecast_national.csv")
    b = n[n.scenario == "Base"].set_index("FY")
    k = pd.read_csv(OUT / "kpis.csv")
    kp = k[(k.scenario == "Base") & (k.region == "India")].set_index("year")
    mp = pd.read_csv(OUT / "mix_pathway.csv")
    m47 = mp[(mp.scenario == "Base") & (mp.year == 2047)].groupby("tech").twh.sum()
    m24 = mp[(mp.scenario == "Base") & (mp.year == BASE_FY)].groupby("tech").twh.sum()
    v = pd.read_csv(OUT / "mix_validation.csv")
    vv = v[(v.region == "India") & (v.tech == "All conventional")].set_index("FY")
    bt = pd.read_csv(OUT / "backtest_metrics.csv").set_index("model")
    cc = pd.read_csv(OUT / "npp_consistency_check.csv")
    H = len(b) - 1
    head = dict(base_fy=BASE_FY, gdp_cagr_csv=100 * tr["gdp_cagr"], gdp_low=100 * scenario_cagr("low"), gdp_high=100 * scenario_cagr("high"),
                pop_2047_m=float(b.loc[2047, "population_m"]), pop_base_m=float(b.loc[BASE_FY, "population_m"]),
                p50_2047=b.loc[2047, "p50"], p10_2047=b.loc[2047, "p10"], p90_2047=b.loc[2047, "p90"],
                central_2047=b.loc[2047, "central_path"], actual_base=b.loc[BASE_FY, "central_path"],
                growth_x=b.loc[2047, "p50"] / b.loc[BASE_FY, "central_path"],
                cagr_pct=100 * ((b.loc[2047, "p50"] / b.loc[BASE_FY, "central_path"]) ** (1 / H) - 1),
                kwh_pc_2047=b.loc[2047, "kwh_per_capita_p50"], kwh_pc_base=b.loc[BASE_FY, "kwh_per_capita_p50"],
                p50_2030=b.loc[2030, "p50"], p50_2035=b.loc[2035, "p50"], p50_2040=b.loc[2040, "p50"],
                low_2047=n[(n.scenario == "Low") & (n.FY == 2047)].p50.iloc[0], high_2047=n[(n.scenario == "High") & (n.FY == 2047)].p50.iloc[0],
                nonfossil_2047=kp.loc[2047, "nonfossil_share"], nonfossil_base=kp.loc[BASE_FY, "nonfossil_share"],
                res_2047=kp.loc[2047, "res_share"], res_base=kp.loc[BASE_FY, "res_share"],
                mix_2047={t_: float(v_) for t_, v_ in m47.items()}, mix_base={t_: float(v_) for t_, v_ in m24.items()},
                val_2025=float(vv.loc[2025, "diff_pct"]), val_2026=float(vv.loc[2026, "diff_pct"]),
                mape_ensemble=float(bt.loc["Ensemble", "MAPE"]), mape_ets=float(bt.loc["ETS (history only, reference)", "MAPE"]),
                consistency_max=float(cc[cc.item != "Gas"].diff_pct.abs().max()), consistency_n=int((cc.item != "Gas").sum()),
                hist_cagr=100 * ((b.loc[BASE_FY, "central_path"] / pd.read_csv(OUT / "history_national.csv", index_col=0).loc[2007, "Total"]) ** (1 / (BASE_FY - 2007)) - 1),
                tornado_top=t.iloc[0].input)
    (OUT / "headline.json").write_text(json.dumps(head, indent=2, default=float))
    print(f"[docs] parameter register ({len(df)} rows, all estimated from NPP/CSV) + headline written")


if __name__ == "__main__":
    build()
