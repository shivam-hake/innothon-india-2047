---
title: "India 2047 – Generation Forecast and Regional Mix: Transparent Methodology (D4)"
subtitle: "ExxonMobil Innothon 2026 · Forecast demand. Match regional strengths. Explain the mix."
---

# 1. Scope, data policy and compliance

**Target.** Annual *electricity generated* (TWh), national and for the five CEA grid regions (Northern NR, Western WR, Southern SR, Eastern ER, North-Eastern NER), every fiscal year FY2025–FY2047 (FY = April–March), with the mix across coal, gas, hydro, nuclear, solar, wind and other renewables.

**Data policy – two datasets, no assumed values.**

1. **National Power Portal (npp.gov.in)**, accessed 19–20 November 2026:
   * Generation Dashboard history (`/dashBoard/get_generation_chart_list`): all-India generation by hydro / thermal / RES / nuclear, FY1947–FY2024.
   * CEA monthly 18-column report, **sub-report 16** (region / state / station-wise), March issues 2020–2026: full-year coal + lignite, gas (incl. liquid fuel), hydro and nuclear by state and region, FY2019–FY2026.
   * Sub-report 2 (region-wise) and Daily Generation Report 17 (fuel-wise), used for consistency checks.
2. **Organiser CSV** `renewable_energy_dataset.csv`: population and GSDP by state (demand drivers); the installed solar / wind / bio / small-hydro / waste-to-energy columns, used **only as composition shares** to split NPP's single RES total (§5).

Every number the pipeline uses is estimated from these data and listed, with how it was estimated, in `docs/parameters.csv`. There are no cost, resource-potential, policy-target or new-load inputs. Unit tests (`tests/test_invariants.py`) assert the data policy (`test_only_permitted_datasets`), the absence of assumption inputs (`test_no_assumed_values`) and that capacity never sets the level of generation (`test_capacity_never_drives_generation_level`).

**Boundary.** NPP all-India utility generation (thermal + hydro + nuclear + RES), excluding Bhutan imports; captive plants are not on NPP and are outside the boundary in history and forecast alike.

**Compliance.** Energy generated (TWh) is the only basis for forecasting and comparison. No consumption, sales or requirement series is used. The CSV capacity columns never drive the level of generation: they only apportion NPP's RES total among solar / wind / other and among regions, because NPP publishes no such split. Only dimensionless shares are saved (`data/processed/csv_re_composition.csv`).

# 2. Pipeline

1. `ingest.py` – read the NPP extracts and the CSV.
2. `clean.py` – CSV quirks and GSDP splice; 5-region map; NPP four-way consistency check; CSV RE-fleet composition (shares); FY2024 regional base mix.
3. `features.py` – CSV population and GDP trends to 2047 with data-derived uncertainty; state → region drivers.
4. `forecast/` – M1 per-capita econometric, M2 intensity, M3 ARIMAX → inverse-MAPE ensemble; MinT reconciliation to regions.
5. `uncertainty.py` – 5,000-draw Monte Carlo and tornado, every distribution estimated from data.
6. `mix.py` – nested share models chosen by back-test → generation by region × technology; out-of-sample validation; KPIs.
7. `dashboard/app.py`, `deck/`, `docs/` read the cached outputs.

`python run_all.py` (or `make all`) regenerates everything in ~10 s; seeds are fixed (`SEED = 2047`).

# 3. Data and cleaning

**National series.** FY2007–FY2024 from the NPP history endpoint: every year an NPP actual. NPP publishes no RES figure after FY2024, so **FY2024 is the base year** (1,698 TWh). NPP's FY2025–FY2026 conventional actuals (sub-report 16) are kept back for out-of-sample validation.

**NPP internal consistency.** Four NPP products are compiled separately; on 48 overlapping year × fuel comparisons (thermal, hydro, nuclear, coal) they agree within **0.13%** (median 0.000%). Gas differs by up to 1.3% because DGR17 books liquid fuel under "diesel" (`outputs/npp_consistency_check.csv`).

**CSV quirks found and fixed with the CSV's own information** (`outputs/data_quality_report.md`):

* 6 non-standard zones remapped to the 5 grid regions (Rajasthan West→NR; "Central" MP / Chhattisgarh→WR; Sikkim→ER; A&N→ER).
* Telangana's missing 2013 row (cause of the raw 2013 population dip) log-interpolated; Delhi (from 2009) and Chandigarh (from 2013) backcast at their own first-three-year CSV growth.
* GSDP base break at 2011 (2011 total = 2.2× 2010): pre-2011 levels rebuilt from 2011 with each state's own CSV growth, or the CSV aggregate growth for states whose pre-2011 values are constant.
* GSDP 2024 is a carry-forward (−0.2%): set to 2023 × (1 + the CSV's own 2023 growth). 19 of 34 states repeat their 2023 capacity in 2024, so FY2025 composition rows are excluded from estimation.
* Ladakh and DNH&DD are absent (<0.1% of population); nothing external is added.

**FY2024 regional base mix.** Coal, gas, hydro and nuclear by region = NPP sub-report 16 actuals (scaled to the NPP national series, <1% apart; tested). RES = NPP national actual (189.5 TWh) split by the CSV RE-fleet composition of that year: solar 63%, wind 27%, other 10%, and each region's share of each.

# 4. Step 01 – Forecast (D1)

Estimation sample: FY2007–FY2024, 18 annual points (NPP generation; CSV population and real GSDP).

* **M1 – per-capita econometric ("why").** ln(kWh per person) = α + β ln(GSDP per person) + γ COVID: β = **0.859 (HAC SE 0.041)**, R² 0.979. A quadratic income term is not identified (t = −0.32), so the elasticity is constant. The last residual decays at the residuals' own AR(1) rate (0.48).
* **M2 – energy intensity ("how big").** ln(G / GDP) = a + c·t + γ COVID: drift c = **−0.60%/yr (SE 0.22)**.
* **M3 – ARIMAX ("what history says").** ln G = c + b ln GDP + γ COVID + AR(1) errors: b = **0.889 (SE 0.072)**, φ = 0.69. A damped ETS on history only is the reference line.

**Back-test** (train FY2007–2018, test FY2019–2024, actual CSV drivers, COVID included):

| Model | MAPE | RMSE (TWh) | Bias |
|---|---|---|---|
| M1 | 4.93% | 76 | +2.6% |
| M2 | 4.38% | 82 | −0.4% |
| M3 | 4.81% | 75 | +1.8% |
| ETS (history only) | 9.87% | 155 | +9.9% |
| **Ensemble** | **4.69%** | **75** | +1.3% |

Weights = inverse hold-out MAPE: **M1 31.7%, M2 35.7%, M3 32.6%**. Rolling-origin CV (origins FY2013–2021, h ≤ 4): M1 4.5%, M2 5.0%, M3 5.2%.

**Drivers (CSV only).** Population: the CSV growth rate falls geometrically by 3.5% a year (OLS on FY2008–2025); extrapolated → **1,601 M in FY2047**. GDP: CSV real GSDP CAGR FY2012–FY2024 = **5.42%/yr**. Urbanisation: neither NPP nor the CSV contains it; its effect is inside income per person.

**Scenarios and uncertainty (all data-derived).** GDP growth distribution = bootstrap of the CSV's 13 annual growth rates FY2013–2025, averaged over 23 years: P10 4.42%, P90 6.17%. **Low / High scenarios** fix GDP at these values. The Monte Carlo (5,000 draws) adds model-elasticity uncertainty (common z × each model's own SE), population-slope uncertainty (its regression SE) and a residual drawn from the ensemble's own back-test errors.

**Result.** FY2047 Base **P50 4,737 TWh (P10 3,849 – P90 5,769)**, 2.8× FY2024, 4.6%/yr (NPP FY2007–24: 5.6%/yr). FY2030 2,188 · FY2035 2,736 · FY2040 3,438. Low 3,948 / High 5,625 TWh. Generation per person 1,225 → 2,959 kWh.

**Trace the number (Base central path, additive LMDI):** FY2024 1,698 → population +427 → generation per person (income) +2,646 → FY2047 4,772.

**Tornado (2047 swing):** GDP CAGR 1,651 TWh > model elasticities 735 > back-test error 550 > model choice 370 > population slope 1.

**Regions.** Base-year requirement shares from CSV drivers only: share ∝ Σ_states Pop × (GSDP per person)^0.859 → NR 26.8%, WR 26.7%, SR 29.1%, ER 14.3%, NER 3.0%. Regions follow their states' CSV population and GSDP-share trends at the national implied elasticity and are MinT-reconciled to the national forecast (exact sums; tested). Regional bands combine the national draws with share uncertainty from the state-trend standard errors. FY2047 Base P50: NR 1,203; WR 1,096; SR 1,483; ER 767; NER 189 TWh. Regional back-test on NPP conventional generation (train FY2019–23, test FY2024–26): NR 2.3%, SR 10.3%, ER 10.5%, WR 12.1%, NER 22.4% MAPE.

# 5. Step 02 – Regional generation mix (D2)

With no assumed costs or potentials, the mix answers: *where does the data say generation is heading, and where is each source strong?* It is built as nested shares, each forecast by the model family that predicted best out of sample:

| Level | Shares | Data | Hold-out |
|---|---|---|---|
| 1 | Thermal / hydro / nuclear / RES in national generation | NPP history FY2007–24 | train ≤2018, test 2019–24 |
| 2a | Coal vs gas inside thermal | NPP sub-report 16, FY2019–26 | train ≤2022, test 2023–26 |
| 2b | Solar / wind / other inside RES | CSV RE-fleet composition FY2007–24 | train ≤2019, test 2020–24 |
| 3 | Each region's share of each source | NPP sub-report 16 (coal, gas, hydro, nuclear); CSV composition (solar, wind, other) | NPP: test 2024–26; CSV: test 2020–24 |

**Model families (candidate windows fixed in advance):** `const(w)` – mean share of the last w years (no change); `logit(s)` – multinomial-logit trend, ln(share_k / share_ref) linear in time from year s (diffusion); `incr(w)` – the future change of the total is split like each source's OLS slope over the last w years (recent additions continue). The best window of each family is kept and families are blended with inverse-MAE weights (`outputs/mix_model_selection.csv`). For example, level 1 blends logit(2007) 0.38, const(1) 0.33 and incr(10) 0.28 (hold-out MAE 1.23 / 1.42 / 1.66 pp); level 2b is dominated by incr(3) (MAE 1.7 pp vs 8–10 pp for the others, weight 0.74).

Generation by technology = national total × level-1 share × level-2 share; by region × level-3 share. Mix sums equal the national forecast exactly (tested).

**Out-of-sample validation.** Forecast conventional generation (coal + gas + hydro + nuclear) vs NPP actuals: **FY2025 +1.0%**, FY2026 +6.9% (a mild year in which thermal fell 4%).

**Result (Base, FY2047):** coal 3,038 TWh (64%), solar 1,110 (23%), hydro 270 (6%), nuclear 130 (3%), wind 122 (3%), other RE 42 (1%), gas 26 (1%). Non-fossil **35%** (FY2024 22%), RES 27% (11%). The percentages barely change across scenarios (Low 64 / 23 / 3, High 64 / 24 / 3) because the shares are trends in time, not functions of the total.

**Regional strengths (location quotient = region's share of India's output of a source ÷ its share of generation):** NR hydro (42% of India's hydro in 2047), WR wind (51% of wind), SR wind (41%), ER coal (23% of coal, 96% of its own generation), NER gas (40% of gas). Implied net position 2047 (generation located − requirement): WR exports 546 TWh; SR imports 348, NER 106, ER 48, NR 43.

# 6. Parameter register

`docs/parameters.csv` lists all 41 numbers the pipeline estimates (drivers, model coefficients, ensemble weights, regional shares, share-model weights) with the data and method behind each. Nothing in it is set by hand.

# 7. Uncertainty statement

The FY2047 generation forecast is uncertain by about **±20% (80% interval 3,849–5,769 TWh)**, dominated by GDP growth (CSV bootstrap) and model elasticities (18 annual points). The mix percentages carry additional model uncertainty visible in the spread between families (e.g. the level-1 logit family alone gives a much higher RES share than the constant family).

# 8. Limitations

* **Trend, not plan.** The mix is where NPP history leads if recent trends continue. Costs, resource potentials, policy targets (e.g. non-fossil goals) and new loads (hydrogen, EVs, data centres) would all require assumed values and are deliberately excluded; any effect they had on FY2007–24 is already inside the trends.
* **Coal grows in TWh** because NPP's thermal share has moved only from 79% to 78% since FY2007; a trend model cannot anticipate future policy.
* **NPP publishes RES as one all-India number.** The solar / wind / other split and its regional location come from the CSV RE-fleet composition (shares only), which implies equal output per MW across RE types – a stated simplification.
* **No urbanisation series** in either dataset; its effect sits inside income per person.
* **Short history.** 18 annual points; a declining income elasticity cannot be estimated (tested, not identified). FY2024 was a dry hydro year; shares inherit that.
