# Jury Q&A preparation

All numbers are Base-scenario outputs in `outputs/`; re-run `python run_all.py` before the jury and re-check.

**1. Which data did you use?**
Only the National Power Portal (history endpoint, CEA 18-column sub-reports 2 and 16, DGR17) and the organiser CSV. `test_only_permitted_datasets` checks `data/raw` and every NPP source URL.

**2. Did you assume anything?**
No numerical value is assumed. Every number is estimated from the two datasets and listed with its method in `docs/parameters.csv`; `test_no_assumed_values` checks that no cost, resource, policy or new-load input exists. Methodological choices (model families, candidate windows) are fixed in advance, and the data chooses among them by out-of-sample error.

**3. How do you know your NPP numbers are right?**
Four NPP products, compiled separately, agree within 0.13% on 48 overlapping year × fuel comparisons. Regional sub-report 16 sums match the region-wise sub-report 2 within 0.6%.

**4. Why is your base year FY2024, not FY2025?**
NPP's RES series ends at FY2024. Rather than estimate FY2025 RES, we stop at the last complete actual and use NPP's FY2025–26 conventional actuals as an out-of-sample test: FY2025 +1.0%, FY2026 +6.9%.

**5. Why is the forecast (4,737 TWh) lower than many published outlooks?**
It contains only what the data supports: CSV population (1,601 M) and the CSV's own GDP trend (5.4%/yr), applied through elasticities estimated on NPP history. Add-on loads such as hydrogen or data centres would need assumed sizes. The High scenario (GDP at the bootstrap P90, 6.2%/yr) gives 5,625 TWh.

**6. Where is urbanisation?**
Neither NPP nor the CSV has an urbanisation series, so we do not invent one. Its effect is inside income per person (M1), which rises with urbanisation.

**7. Why does population barely move the tornado?**
The tornado moves the *uncertainty* of the population trend, and the CSV trend is so regular that its slope standard error is tiny. The population trend itself adds +427 TWh in the waterfall.

**8. Your back-test MAPE is 4.7%. Is that good?**
It is out of sample on FY2019–24, including COVID, with 12 training years. A history-only ETS misses by 9.9%. The three models score alike (4.4–4.9%), so the ensemble gives robustness rather than a lower error.

**9. How did you get solar and wind separately if NPP only has 'RES'?**
NPP publishes RES as one all-India number. The CSV's installed solar / wind / other columns give the composition of the RE fleet, which we use only as shares to split that NPP total and to locate it by region. Capacity never sets the amount of generation. The simplification is equal output per MW across RE types; we state it.

**10. Why does coal still grow to ~3,000 TWh?**
Because NPP's thermal share has barely moved (79% → 78% over FY2007–24). A data-only trend cannot see future policy. That is the honest answer to "where does history lead", and it is the main limitation.

**11. How are the mix shares chosen?**
Three families compete on a hold-out for every share panel: constant, multinomial-logit trend, and recent increments. The best window of each family is kept, and families are blended by inverse error. For the national sources: logit 0.38, constant 0.33, increments 0.28.

**12. Isn't the solar share of RES just extrapolated?**
The recent-increments family won that back-test by far (MAE 1.7 pp vs 8–10 pp). Future RES growth is split like the recent additions to the CSV fleet, which are mostly solar. So solar rises to 23% of generation and wind stays near 3%.

**13. What are the regional strengths?**
They are computed as location quotients:
- NR: hydro (42% of India's hydro in 2047)
- WR and SR: wind (51% and 41%)
- ER: coal (96% of its own generation)
- NER: gas (40% of India's gas, from the Assam and Tripura plants in sub-report 16)

**14. Who exports and imports?**
Implied net position = generation located in a region − its requirement. In 2047, WR exports 546 TWh; SR imports 348, NER 106, ER 48 and NR 43.

**15. How sure are you about 2047?**
80% interval 3,849–5,769 TWh (±20%). GDP growth dominates: its CSV bootstrap P10/P90 moves 2047 by −878 / +773 TWh.

**16. Why no CO₂, cost or land numbers?**
Each needs factors that NPP and the CSV do not contain (emission factors, costs, land per MW). Under a strict data-only rule they would be assumptions. We report the non-fossil share, which needs none.

**17. Do regions add up?**
Yes, exactly, in every scenario and year: MinT reconciliation and unit tests. The mix also sums exactly to the national forecast.

**18. What would change the answer?**
- NPP publishing a solar/wind or regional RES split (replaces the CSV composition).
- A few more years of data showing the thermal share falling, which the logit and increments families would pick up immediately.
- A GDP path outside the CSV's own historical range.
