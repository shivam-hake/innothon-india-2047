"""Model 2 - Energy-intensity (decomposition) model (explains HOW BIG, from the economy's side).

    ln(G_t / GDP_t) = a + c (t - 2007) + g COVID_t + u_t                       OLS, HAC SEs, FY2007 - train_end
G = NPP all-India generation, GDP = CSV real GSDP (sum of states). c is the autonomous drift of generation per unit
of output (c < 0: the economy needs slightly less electricity per rupee each year - efficiency and structural
change net of electrification). Forecast: G_t = GDP_t x I_T x exp(c (t - T)), starting on the last actual.
decompose() splits any G path into population, urbanisation-index and intensity (income) effects (additive LMDI)
for the 'Trace the number' waterfall.
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm
from src.config import BASE_FY

START = 2007


class Intensity:
    name = "M2 Intensity (decomposition)"

    def __init__(self, train_end=BASE_FY):
        self.train_end = train_end

    def fit(self, nat):
        d = nat.loc[START:self.train_end].copy()
        y = np.log(d.Total / d.gdp)
        X = pd.DataFrame({"const": 1.0, "t": d.index - START}, index=d.index)
        if d.covid.sum() > 0:
            X["covid"] = d.covid
        self.m = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 2})
        self.I_last = float(np.exp(y.iloc[-1]))
        self.last_year = int(d.index[-1])
        self.gdp_last = float(d.gdp.iloc[-1])
        self.d = d
        return self

    def summary(self):
        m = self.m
        return dict(a=m.params["const"], c=m.params["t"], se_c=m.bse["t"], r2=m.rsquared, n=int(m.nobs),
                    implied_elasticity_note="G grows at GDP growth + c", sample=f"FY{START}-FY{self.train_end}")

    def predict(self, drv, c=None):
        c = self.m.params["t"] if c is None else (np.asarray(c)[:, None] if np.ndim(c) else c)
        steps = np.clip(np.asarray(drv["years"]) - self.last_year, 0, None)
        return drv["gdp"] * self.I_last * np.exp(c * steps)


def decompose(G0, G1, P0, P1, u0, u1):
    """Additive LMDI: G = P x U x I  (U = urbanisation index, I = generation per person per unit of U)."""
    I0, I1 = G0 / (P0 * u0), G1 / (P1 * u1)
    L = (G1 - G0) / (np.log(G1) - np.log(G0))
    return dict(population=L * np.log(P1 / P0), urbanization=L * np.log(u1 / u0), income=L * np.log(I1 / I0))
