"""Step 01 pipeline: fit, back-test, forecast the three scenarios, Monte Carlo, tornado, regional reconciliation
-> outputs/*.csv (cached artefacts used by the dashboard). Data: NPP + organiser CSV only; no assumed values."""
import json
import numpy as np
import pandas as pd
from src.config import OUT, PROC, REGIONS, BASE_FY, SCENARIOS
from src.features import nat, YEARS_ALL, csv_trends, scenario_cagr
from src.forecast.ensemble import backtest, rolling_cv, national_forecast, waterfall, fitted_models
from src.forecast.timeseries import ets_reference
from src.forecast.reconcile import regional_point, regional_quantiles
from src.uncertainty import run_mc, quantiles, tornado


def regional_backtest():
    """Regional check on NPP region-wise conventional generation (sub-report 16): train FY2019-23, test FY2024-26."""
    n = pd.read_csv(PROC / "npp_region_fuel_fy.csv")
    n = n[n.region.isin(REGIONS)].copy()
    n["conv"] = n[["Coal", "Gas", "Hydro", "Nuclear"]].sum(axis=1)
    rows = []
    for r, g in n.groupby("region"):
        g = g.set_index("FY").conv
        b = np.polyfit(g.loc[:2023].index, np.log(g.loc[:2023].values), 1)
        for y in (2024, 2025, 2026):
            p = np.exp(np.polyval(b, y))
            rows.append(dict(region=r, FY=y, actual=g[y], predicted=p, ape=100 * abs(p / g[y] - 1)))
    df = pd.DataFrame(rows)
    return df, df.groupby("region").ape.mean().rename("MAPE").reset_index()


def run(n_mc=5000):
    d = nat()
    bt, preds, w = backtest()
    cv = rolling_cv()
    bt.to_csv(OUT / "backtest_metrics.csv", index=False)
    preds.to_csv(OUT / "backtest_predictions.csv", index=False)
    cv.to_csv(OUT / "rolling_cv.csv", index=False)
    rb, rbm = regional_backtest()
    rb.to_csv(OUT / "regional_backtest.csv", index=False)
    rbm.to_csv(OUT / "regional_backtest_metrics.csv", index=False)

    m1, m2, m3 = fitted_models()
    tr = csv_trends()
    summ = {m1.name: m1.summary(), m2.name: m2.summary(), m3.name: m3.summary(), "weights": w.to_dict(),
            "cv_mean_mape": cv.groupby("model").MAPE.mean().to_dict(),
            "drivers": {k: v for k, v in tr.items() if k != "gdp_boot"},
            "scenario_cagr": {c: scenario_cagr(c) for c in ("low", "base", "high")}}
    (OUT / "model_summary.json").write_text(json.dumps(summ, indent=2, default=float))
    pd.DataFrame({"FY": m1.d.index, "resid": m1.m.resid.values, "fitted_twh": m1.fitted().values,
                  "actual_twh": m1.d.Total.values}).to_csv(OUT / "m1_residuals.csv", index=False)

    nat_rows, reg_rows, wf_all = [], [], {}
    ets = ets_reference(d)
    for scen in SCENARIOS:
        case = scen.lower()
        fc = national_forecast(case=case)
        mcf, inp = run_mc(case, n=n_mc)
        q = quantiles(mcf)
        wf_all[scen] = waterfall(fc)
        df = pd.DataFrame({"FY": YEARS_ALL, "scenario": scen, "gdp_cagr": scenario_cagr(case),
                           "m1_econometric": fc["m1"][0], "m2_intensity": fc["m2"][0], "m3_timeseries": fc["m3"][0],
                           "ets_reference": np.r_[d.loc[BASE_FY, "Total"], ets], "central_path": fc["total"][0],
                           "p10": q.p10.values, "p50": q.p50.values, "p90": q.p90.values,
                           "population_m": fc["drivers"]["pop"][0] / 1e6,
                           "gdp_index": fc["drivers"]["gdp"][0] / fc["drivers"]["gdp"][0, 0]})
        df["kwh_per_capita_p50"] = df.p50 * 1e9 / (df.population_m * 1e6)
        nat_rows.append(df)
        rp = regional_point(fc)
        q10, p50, q90, draws = regional_quantiles(rp["reconciled"], mcf["total"], fc)
        for j, r in enumerate(REGIONS):
            rd = rp["region_drivers"].query("region == @r")
            reg_rows.append(pd.DataFrame({"region": r, "FY": YEARS_ALL, "scenario": scen, "p10": q10[:, j], "p50": p50[:, j],
                                          "p90": q90[:, j], "central_path": rp["reconciled"][r].values,
                                          "bottom_up": rp["bottom_up"][r].values, "reconcile_adj_pct": rp["adjustment_pct"][r].values,
                                          "pop_m": rd["pop"].values / 1e6, "gsdp_index": rd["gsdp"].values / rd["gsdp"].values[0]}))
        if scen == "Base":
            mc_store = dict(total=mcf["total"][:, -1], draws=draws[:, -1, :], inp=inp)
            pd.Series(rp["shares_base"], name="share").to_csv(OUT / "regional_requirement_shares_base.csv")
    natdf = pd.concat(nat_rows)
    natdf.to_csv(OUT / "forecast_national.csv", index=False)
    regdf = pd.concat(reg_rows)
    nat_tidy = natdf[["FY", "scenario", "p10", "p50", "p90", "central_path"]].assign(region="India")
    tidy = pd.concat([regdf, nat_tidy], ignore_index=True).rename(columns={"FY": "year"})
    tidy.to_csv(OUT / "forecast_region_year.csv", index=False)
    pd.concat(wf_all, names=["scenario"]).reset_index(level=0).to_csv(OUT / "waterfall.csv", index=False)
    tornado("base").to_csv(OUT / "tornado.csv", index=False)
    pd.DataFrame({"national_2047": mc_store["total"], **{f"{r}_2047": mc_store["draws"][:, j] for j, r in enumerate(REGIONS)},
                  **{k: v for k, v in mc_store["inp"].items()}}).to_csv(OUT / "mc_2047_draws.csv", index=False)
    hist = d[["Total", "Thermal", "Coal", "Gas", "Nuclear", "Hydro", "RES", "population", "gen_pc_kwh", "gdp", "gdp_pc"]].copy()
    hist.index.name = "FY"
    hist.to_csv(OUT / "history_national.csv")
    b = natdf[natdf.scenario == "Base"].set_index("FY")
    print(f"[forecast] Base FY2047 P50 {b.loc[2047,'p50']:,.0f} TWh (P10 {b.loc[2047,'p10']:,.0f} - P90 {b.loc[2047,'p90']:,.0f}); "
          f"weights {w.round(3).to_dict()}; ensemble back-test MAPE {bt.set_index('model').loc['Ensemble','MAPE']:.2f}%")
    return natdf, tidy


if __name__ == "__main__":
    run()
