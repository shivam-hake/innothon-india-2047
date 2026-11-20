"""Model 1 - Per-capita econometric driver model (explains WHY generation grows).

    ln(kWh per person)_t = a + b ln(GSDP per person)_t + g COVID_t + u_t,     OLS, HAC (Newey-West, 2 lags) SEs
kWh per person = NPP all-India generation / CSV population; GSDP per person = CSV real GSDP / CSV population
(INR, constant 2011-12 prices); FY2007 - train_end. b is the income elasticity of per-capita generation.
A log-quadratic term (declining elasticity) is estimated as a diagnostic: with 19 annual points spanning a narrow
income band its coefficient is not identified (|t| < 0.5, sign flips between samples), so the model keeps the
constant elasticity and saturation risk is handled by the efficiency wedge and the scenario range (stated
limitation). Forecast = per-capita path x projected population x urbanisation index; the last-year residual
decays at the residuals' own estimated AR(1) rate, so the path starts on the last actual.
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm
from src.config import BASE_FY

START = 2007


class Econometric:
    name = "M1 Econometric (per capita)"

    def __init__(self, train_end=BASE_FY):
        self.train_end = train_end

    def fit(self, nat):
        d = nat.loc[START:self.train_end].copy()
        d["lny"] = np.log(d.gdp_pc)
        d["lne"] = np.log(d.gen_pc_kwh)
        cols = ["lny"] + (["covid"] if d.covid.sum() > 0 else [])
        self.m = sm.OLS(d.lne, sm.add_constant(d[cols])).fit(cov_type="HAC", cov_kwds={"maxlags": 2})
        c = d.lny - d.lny.mean()
        q = sm.OLS(d.lne, sm.add_constant(pd.DataFrame({"lny": c, "lny2": c ** 2, **({"covid": d.covid} if d.covid.sum() else {})}))).fit()
        self.quad = dict(b2=float(q.params["lny2"]), se_b2=float(q.bse["lny2"]), t_b2=float(q.tvalues["lny2"]))
        self.last_resid = float(self.m.resid.iloc[-1])
        r = self.m.resid.values
        self.rho = float(np.clip(np.dot(r[1:], r[:-1]) / np.dot(r[:-1], r[:-1]), 0.0, 0.99))   # estimated AR(1)
        self.last_year = int(d.index[-1])
        self.d = d
        return self

    def summary(self):
        m = self.m
        return dict(alpha=m.params["const"], beta_lny=m.params["lny"], se_lny=m.bse["lny"],
                    gamma_covid=m.params.get("covid", 0.0), elasticity_last=m.params["lny"], r2=m.rsquared,
                    dw=float(sm.stats.durbin_watson(m.resid)), n=int(m.nobs), sample=f"FY{START}-FY{self.train_end}",
                    quadratic_test=self.quad, resid_ar1=self.rho)

    def predict_pc(self, gdp_pc, years, beta_lny=None):
        decay = self.rho
        prm = self.m.params
        bl = prm["lny"] if beta_lny is None else (np.asarray(beta_lny)[:, None] if np.ndim(beta_lny) else beta_lny)
        lny = np.log(gdp_pc)
        lny0 = np.log(self.d.gdp_pc.iloc[-1])
        z = prm["const"] + prm["lny"] * lny0 + bl * (lny - lny0)
        steps = np.clip(np.asarray(years) - self.last_year, 0, None)
        return np.exp(z + self.last_resid * decay ** steps)

    def predict(self, drv, beta_lny=None):
        return self.predict_pc(drv["gdp_pc"], drv["years"], beta_lny) * drv["pop"] / 1e9

    def fitted(self):
        return np.exp(self.m.fittedvalues) * self.d.population / 1e9
