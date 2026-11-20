"""Ensemble of the three national models = national generation forecast (no add-on modules, no assumed values).

Weights = inverse hold-out MAPE (train FY2007-FY2018, test FY2019-FY2024 = the last six NPP years, incl. COVID).
Rolling-origin CV is also reported. national_forecast() is vectorised: inputs may be arrays of Monte Carlo draws.
"""
import numpy as np
import pandas as pd
from src.config import BASE_FY, HORIZON
from src.features import nat, national_drivers, YEARS_ALL
from src.forecast.econometric import Econometric
from src.forecast.intensity import Intensity, decompose
from src.forecast.timeseries import TimeSeriesARX, ets_reference

MODELS = [Econometric, Intensity, TimeSeriesARX]
_FITTED = {}


def fitted_models(train_end=BASE_FY):
    if train_end not in _FITTED:
        d = nat()
        _FITTED[train_end] = [M(train_end).fit(d) for M in MODELS]
    return _FITTED[train_end]


def _hist_drivers(years):
    d = nat()
    return dict(years=np.asarray(years), gdp_pc=d.loc[years, "gdp_pc"].values[None],
                pop=d.loc[years, "population"].values[None],
                gdp=d.loc[years, "gdp"].values[None])


def backtest(train_end=2018, test_end=2024):
    d = nat()
    yrs = np.arange(train_end, test_end + 1)
    drv = _hist_drivers(yrs)
    act = d.loc[yrs[1:], "Total"].values
    rows, preds = [], {"FY": yrs[1:], "Actual": act}
    for m in fitted_models(train_end):
        p = m.predict(drv)[0][1:]
        preds[m.name] = p
        rows.append(dict(model=m.name, MAPE=100 * np.mean(np.abs(p / act - 1)),
                         RMSE=float(np.sqrt(np.mean((p - act) ** 2))), bias_pct=100 * np.mean(p / act - 1)))
    e = ets_reference(d, train_end, len(act))
    preds["ETS (history only, reference)"] = e
    rows.append(dict(model="ETS (history only, reference)", MAPE=100 * np.mean(np.abs(e / act - 1)),
                     RMSE=float(np.sqrt(np.mean((e - act) ** 2))), bias_pct=100 * np.mean(e / act - 1)))
    bt = pd.DataFrame(rows)
    w = 1 / bt.set_index("model").MAPE.iloc[:3]
    w = w / w.sum()
    ens = sum(w[m.name] * preds[m.name] for m in fitted_models(train_end))
    preds["Ensemble"] = ens
    bt = pd.concat([bt, pd.DataFrame([dict(model="Ensemble", MAPE=100 * np.mean(np.abs(ens / act - 1)),
                                            RMSE=float(np.sqrt(np.mean((ens - act) ** 2))),
                                            bias_pct=100 * np.mean(ens / act - 1))])], ignore_index=True)
    return bt, pd.DataFrame(preds), w


def rolling_cv(origins=(2013, 2015, 2017, 2019, 2021), h=4):
    d = nat()
    rows = []
    for o in origins:
        yrs = np.arange(o, min(o + h, BASE_FY) + 1)
        drv = _hist_drivers(yrs)
        act = d.loc[yrs[1:], "Total"].values
        for M in MODELS:
            m = M(o).fit(d)
            p = m.predict(drv)[0][1:]
            rows.append(dict(origin=o, model=M.name, horizon=len(act), MAPE=100 * np.mean(np.abs(p / act - 1))))
    cv = pd.DataFrame(rows)
    return cv


WEIGHTS = None


def weights():
    global WEIGHTS
    if WEIGHTS is None:
        _, _, WEIGHTS = backtest()
    return WEIGHTS


def national_forecast(cagr=None, pop_z=0.0, z_elast=0.0, case="base", only=None):
    """Return dict of (n, T) arrays over YEARS_ALL (FY2024..FY2047). only = model index to use alone (tornado)."""
    drv = national_drivers(cagr, pop_z, case)
    m1, m2, m3 = fitted_models()
    s1, s2, s3 = m1.summary(), m2.summary(), m3.summary()
    z = np.atleast_1d(z_elast).astype(float)
    n = drv["gdp"].shape[0]
    if z.size == 1 and n > 1:
        z = np.repeat(z, n)
    g1 = m1.predict(drv, beta_lny=s1["beta_lny"] + z * s1["se_lny"] if np.any(z) else None)
    g2 = m2.predict(drv, c=s2["c"] + z * s2["se_c"] if np.any(z) else None)
    g3 = m3.predict(drv, b_gdp=s3["b_gdp"] + z * s3["se_gdp"] if np.any(z) else None)
    w = weights()
    trend = w.iloc[0] * g1 + w.iloc[1] * g2 + w.iloc[2] * g3
    if only is not None:
        trend = [g1, g2, g3][only]
    return dict(years=YEARS_ALL, drivers=drv, m1=g1, m2=g2, m3=g3, total=trend)


def waterfall(fc):
    """Trace the number: FY2024 actual -> FY2047 (single path): population vs income per person (additive LMDI)."""
    drv = fc["drivers"]
    G0, G1 = fc["total"][0, 0], fc["total"][0, -1]
    one = np.ones(1)
    dec = decompose(G0, G1, drv["pop"][0, 0], drv["pop"][0, -1], 1.0, 1.0)
    steps = [(f"FY{BASE_FY} actual", G0), ("Population (CSV trend)", dec["population"]),
             ("Generation per person (income, CSV GSDP)", dec["income"]), ("FY2047 forecast", G1)]
    return pd.DataFrame(steps, columns=["component", "TWh"])
