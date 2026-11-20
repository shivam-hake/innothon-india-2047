# India 2047: Electricity Generation Forecast and Regional Mix

ExxonMobil Innothon 2026 submission.

- Dashboard: https://india2047-innothon.streamlit.app
- Repository: https://github.com/shivam-hake/innothon-india-2047

## What we did

The task was to forecast how much electricity India will need to generate in 2047, split it across the five grid regions, and explain which sources each region should rely on.

We used only two data sources:

1. **National Power Portal (npp.gov.in)**: national generation history by source (FY2007 to FY2024) and region-wise generation by fuel (FY2019 to FY2026).
2. **The CSV given by the organisers**: population and GSDP by state, plus the installed solar, wind and other renewable capacity.

We did not add any outside numbers such as cost estimates, policy targets or resource potentials. Everything in the model is estimated from these two sources. All results are in TWh of electricity generated.

## Main results (base case)

| | FY2024 (actual) | FY2047 (forecast) |
|---|---|---|
| Total generation | 1,698 TWh | 4,737 TWh |
| Range (P10 to P90) | | 3,849 to 5,769 TWh |
| Generation per person | 1,225 kWh | 2,959 kWh |
| Non-fossil share | 22% | 35% |

Generation grows about 2.8 times by 2047, or 4.6% a year. For comparison, it grew 5.6% a year between FY2007 and FY2024.

**2047 generation mix:** coal 64%, solar 23%, hydro 6%, nuclear 3%, wind 3%, gas 1%, other renewables 1%.

**Regional strengths (what each region produces more of than its size alone would suggest):**

| Region | Strength | Note |
|---|---|---|
| Northern | Hydro | 42% of India's hydro |
| Western | Wind | Largest generator overall and a net exporter |
| Southern | Wind and solar | Largest regional demand, imports from Western |
| Eastern | Coal | Coal is 96% of its generation |
| North-Eastern | Gas and hydro | 40% of India's gas generation |

## How the forecast works

**Total demand.** We built three models and combined them:

- **Per-person model**: electricity per person grows with income per person (GSDP from the CSV). We then multiply by projected population.
- **Intensity model**: electricity per rupee of GDP follows its historical trend.
- **Time-series model**: generation follows GDP, and each year's error carries over to the next year.

To check them, we trained each model on FY2007 to FY2018 and asked it to predict FY2019 to FY2024, years it had not seen (including COVID). The average error was about 4.7% for the combined model, versus 9.9% for a simple trend line that ignores population and GDP. We weighted the three models by how accurate they were in this test.

We also checked against real data after our base year. Our forecast of FY2025 coal, gas, hydro and nuclear generation was within 1% of what NPP reported.

**Regions.** Each region's share of demand comes from its population and income per person (from the CSV). Regional numbers always add up exactly to the national total.

**Generation mix.** For each share (for example, renewables as a share of total generation, or solar as a share of renewables), we tested three simple approaches on past years:

- the share stays the same,
- the share keeps following its past trend,
- future growth is split the way recent additions were split.

The approaches that predicted past years best get more weight. NPP reports renewables only as one total, so we split it into solar, wind and other using the mix of installed capacity in the CSV. Capacity is only used for this split, never to decide how much is generated.

**Uncertainty.** The range comes from the data itself: GDP growth is resampled from the CSV's own yearly growth rates, and model uncertainty comes from the models' standard errors. GDP growth has the biggest effect on the 2047 number.

## Limitations

- The mix shows where current trends lead, not an optimised plan. Without outside data on costs or targets we cannot model policy changes, which is why coal stays high.
- NPP does not split renewables into solar and wind, so we use the CSV capacity mix. This treats each MW of solar and wind as producing the same energy.
- Neither dataset has urbanisation figures, so its effect is captured through income per person.
- We have 18 years of history, which limits how complex the models can be.

## Running it yourself

You need Python 3.11 or newer.

```bash
pip install -r requirements.txt
streamlit run dashboard/app.py     # open the dashboard
python run_all.py --no-deck        # rebuild all results and run the checks
```

## Folder layout

```
data/raw/       NPP extracts and the organiser CSV
src/            data cleaning, forecast models, mix model
dashboard/      Streamlit dashboard
outputs/        all result tables (CSV)
docs/           methodology, regional notes, list of estimated parameters
deck/           presentation slides
notebooks/      step-by-step analysis notebooks
tests/          automatic checks (regions add up, only allowed data used, etc.)
```