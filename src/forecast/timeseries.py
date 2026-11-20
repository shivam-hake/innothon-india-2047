"""Model 3 - Statistical time-series baseline (explains WHAT HISTORY SAYS).

Regression with AR(1) errors (ARIMAX(1,0,0) with exogenous regressors), estimated by exact MLE
(statsmodels SARIMAX):
    ln G_t = c + b_y ln GDP_t + g COVID_t + n_t,    n_t = phi n_{t-1} + e_t      (FY2007 - train_end)
b_y is the historical (constant) GDP elasticity of generation - i.e. 'history repeats'.
G = NPP all-India generation; GDP = CSV real GSDP.
Forecast: ln G_T+h = c + b_y ln GDP_T+h + phi^h n_T  (analytic -> vectorised for MC).
A pure-history ETS (damped additive trend on ln G, no drivers) is reported as a reference line only.
"""
import warnings
import numpy as np
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from src.config import BASE_FY


class TimeSeriesARX:
    name = "M3 Time-series ARIMAX"

    def __init__(self, train_end=BASE_FY):
        self.train_end = train_end

    def fit(self, nat):
        d = nat.loc[2007:self.train_end].copy()
        y = np.log(d.Total)
        X = pd.DataFrame({"const": 1.0, "lngdp": np.log(d.gdp)}, index=d.index)
        if d.covid.sum() > 0:
            X["covid"] = d.covid
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.m = SARIMAX(y.values, exog=X.values, order=(1, 0, 0), trend="n").fit(disp=False)
        names = list(X.columns) + ["ar1", "sigma2"]
        self.params = dict(zip(names, self.m.params))
        self.bse = dict(zip(names, self.m.bse))
        fitted_mean = X.values @ np.array([self.params[c] for c in X.columns])
        self.n_last = float(y.values[-1] - fitted_mean[-1])
        self.last_year = self.train_end
        self.d = d
        return self

    def summary(self):
        p, s = self.params, self.bse
        return dict(const=p["const"], b_gdp=p["lngdp"], se_gdp=s["lngdp"], phi=p["ar1"],
                    sigma=float(np.sqrt(p["sigma2"])), aic=float(self.m.aic), n=int(self.m.nobs))

    def predict(self, drv, b_gdp=None):
        p = self.params
        bg = p["lngdp"] if b_gdp is None else np.asarray(b_gdp)[:, None]
        steps = np.clip(np.asarray(drv["years"]) - self.last_year, 0, None)
        lng = np.log(drv["gdp"])
        lng0 = np.log(float(self.d.gdp.iloc[-1]))
        base = p["const"] + p["lngdp"] * lng0
        mean = base + bg * (lng - lng0)
        return np.exp(mean + self.n_last * np.power(p["ar1"], steps))


def ets_reference(nat, train_end=BASE_FY, horizon=None):
    horizon = horizon or (2047 - train_end)
    y = np.log(nat.loc[2007:train_end, "Total"].values)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        m = ExponentialSmoothing(y, trend="add", damped_trend=True).fit(optimized=True)
    return np.exp(m.forecast(horizon))
