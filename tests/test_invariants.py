"""Invariants the jury can check (run: python -m pytest -q)."""
import re
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
PROC = ROOT / "data" / "processed"
REGIONS = ["NR", "WR", "SR", "ER", "NER"]


def test_regions_sum_to_national():
    t = pd.read_csv(OUT / "forecast_region_year.csv")
    for (scen, yr), g in t.groupby(["scenario", "year"]):
        nat = g[g.region == "India"].p50.iloc[0]
        assert abs(g[g.region.isin(REGIONS)].p50.sum() - nat) < 1e-6 * nat, (scen, yr)


def test_central_paths_reconciled():
    t = pd.read_csv(OUT / "forecast_region_year.csv")
    for (scen, yr), g in t.groupby(["scenario", "year"]):
        nat = g[g.region == "India"].central_path.iloc[0]
        assert abs(g[g.region.isin(REGIONS)].central_path.sum() - nat) < 1e-6 * nat


def test_mix_sums_to_national_forecast():
    """Generation by region x technology adds up to the national forecast in every scenario and year."""
    mp = pd.read_csv(OUT / "mix_pathway.csv")
    fr = pd.read_csv(OUT / "forecast_region_year.csv")
    h = pd.read_csv(PROC / "national_series_fy.csv", index_col=0)
    for (scen, yr), g in mp.groupby(["scenario", "year"]):
        nat = h.loc[yr, "Total"] if yr == h.index.max() else fr[(fr.region == "India") & (fr.scenario == scen) & (fr.year == yr)].p50.iloc[0]
        assert abs(g.twh.sum() - nat) < 1e-6 * nat, (scen, yr)
        assert (g.twh >= -1e-9).all()


def test_base_year_mix_matches_npp():
    """FY2024 coal, gas, hydro, nuclear by region = NPP sub-report 16 (scaled to the NPP national series, <1% apart);
    national RES = NPP actual."""
    mix = pd.read_csv(PROC / "mix_region_base.csv", index_col=0)
    n = pd.read_csv(PROC / "npp_region_fuel_fy.csv")
    n = n[(n.FY == 2024) & n.region.isin(REGIONS)].set_index("region").reindex(REGIONS)
    h = pd.read_csv(PROC / "national_series_fy.csv", index_col=0)
    for f in ("Coal", "Gas", "Hydro", "Nuclear"):
        assert np.allclose(mix[f], n[f] * mix[f].sum() / n[f].sum())
        assert abs(mix[f].sum() / n[f].sum() - 1) < 0.01
    assert abs(mix[["Solar", "Wind", "Other RE"]].values.sum() - h.loc[2024, "RES"]) < 1e-6


def test_npp_internal_consistency_within_2pct():
    c = pd.read_csv(OUT / "npp_consistency_check.csv")
    core = c[c.item != "Gas"]
    assert len(core) >= 30 and core.diff_pct.abs().max() <= 2.0


def test_only_permitted_datasets():
    """Data policy: National Power Portal extracts + organiser CSV (+ map geometry for display only)."""
    allowed = {"renewable_energy_dataset.csv", "npp_history_national.csv", "npp_18col_sub2_march_region_fy.csv",
               "npp_18col_sub16_march_region_fuel_fy.csv", "npp_dgr17_fuelwise_fy.csv", "india_states_datta07.geojson"}
    assert {p.name for p in (ROOT / "data" / "raw").iterdir() if p.is_file()} <= allowed
    for f in ("npp_18col_sub2_march_region_fy.csv", "npp_18col_sub16_march_region_fuel_fy.csv", "npp_dgr17_fuelwise_fy.csv"):
        urls = pd.read_csv(ROOT / "data" / "raw" / f, comment="#").source_url
        assert urls.str.startswith("https://npp.gov.in/").all()


def test_no_assumed_values():
    """No assumptions register, no assumption ids, no cost / resource / new-load modules in the pipeline."""
    assert not (ROOT / "docs" / "assumptions.csv").exists()
    for gone in ("optimize_mix.py", "run_strategy.py", "kpis.py", "forecast/newloads.py"):
        assert not (ROOT / "src" / gone).exists(), gone
    for p in (ROOT / "src").rglob("*.py"):
        txt = p.read_text()
        assert "ASSUMPTION" not in txt.upper().replace("NO ASSUMED", ""), p
    par = pd.read_csv(ROOT / "docs" / "parameters.csv")
    assert par.source.str.contains("CSV|NPP").all()


def test_capacity_never_drives_generation_level():
    """CSV capacity columns: absent from every processed panel; only dimensionless composition shares are stored."""
    for f in PROC.glob("*.csv"):
        cols = pd.read_csv(f, nrows=1).columns
        assert not any(str(c).startswith("Installed") for c in cols), f
    comp = pd.read_csv(PROC / "csv_re_composition.csv")
    assert comp.share.between(0, 2.0).all()           # shares and a FY2024 = 1 index, never MW
    for p in ["features.py", "forecast/econometric.py", "forecast/intensity.py", "forecast/timeseries.py",
              "forecast/ensemble.py", "forecast/reconcile.py", "uncertainty.py"]:
        txt = (ROOT / "src" / p).read_text()
        assert "Installed" not in txt and "re_composition" not in txt, p


def test_generation_only_targets():
    h = pd.read_csv(PROC / "national_series_fy.csv", index_col=0)
    assert {"Total", "Thermal", "Hydro", "Nuclear", "RES"} <= set(h.columns)
    assert not any("consumption" in c.lower() or "requirement" in c.lower() for c in h.columns)


def test_mint_reduces_to_proportional():
    from src.forecast.reconcile import mint
    y = np.array([10.0, 20.0, 30.0])
    r = mint(70.0, y, 1e-9, y)
    assert abs(r.sum() - 70) < 1e-6 and np.allclose(r / r.sum(), y / y.sum(), atol=1e-4)
