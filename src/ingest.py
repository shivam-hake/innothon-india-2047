"""Ingest the TWO permitted datasets into tidy tables.

1. National Power Portal (npp.gov.in) - Ministry of Power / CEA. Three extracts saved in data/raw
   (each row carries its source URL; access date 2026-11-19; see data/README.md):
     * npp_history_national.csv          - Generation Dashboard "Growth of Electricity Generation of India",
                                           endpoint /dashBoard/get_generation_chart_list. All-India utility
                                           generation by hydro / thermal / RES / nuclear, GWh, FY1947-FY2024.
     * npp_18col_sub2_march_region_fy.csv- CEA monthly 18-column report, sub-report 2 (region-wise), March issue
                                           of each year 2020-2026 -> full-FY actual and previous-FY actual
                                           (thermal, nuclear, hydro, Bhutan import) by region, FY2019-FY2026.
     * npp_18col_sub16_march_region_fuel_fy.csv - CEA 18-column report, sub-report 16 (region / state / station-wise),
                                           March issues 2020-2026 -> FY coal+lignite / gas / hydro / nuclear by region.
     * npp_dgr17_fuelwise_fy.csv         - CEA Daily Generation Report 17 (fuel-wise), 31 March of each year ->
                                           FY cumulative coal / lignite / gas / diesel / nuclear / hydro / Bhutan.
2. Organiser CSV renewable_energy_dataset.csv - Population and GSDP drive the demand forecast. The 'Installed - *'
   capacity columns never drive the LEVEL of generation; their composition (shares) is used only to apportion NPP's
   single RES generation total among solar / wind / other and among regions, because NPP publishes no such split.
"""
import pandas as pd
from src.config import RAW, PROC

REG = {"NORTHERN": "NR", "WESTERN": "WR", "SOUTHERN": "SR", "EASTERN": "ER", "NORTH EASTERN": "NER"}


def fy_label_to_end(s):
    """'2023-24' -> 2024 (FY ending March)."""
    a, b = s.split("-")
    return int(a) + 1


def npp_history():
    h = pd.read_csv(RAW / "npp_history_national.csv", comment="#")
    h["FY"] = h.financial_year.map(fy_label_to_end)
    h = h.set_index("FY").sort_index()
    out = (h[["hydro", "thermal", "res", "nuclear"]] / 1000.0).rename(columns=str.capitalize)   # GWh -> TWh
    out = out.rename(columns={"Res": "RES"})
    out["source"] = "NPP generation dashboard (history)"
    return out


def npp_regional():
    r = pd.read_csv(RAW / "npp_18col_sub2_march_region_fy.csv")
    a = r.assign(FY=r.report_year, gwh=r.fy_actual_gwh)
    # FY2019 = 'previous FY actual' column of the March-2020 report
    b = r[r.report_year == r.report_year.min()].assign(FY=lambda x: x.report_year - 1, gwh=lambda x: x.prev_fy_actual_gwh)
    d = pd.concat([a, b])
    d["region"] = d.region.map(REG).fillna("BHUTAN")
    p = d.pivot_table(index=["FY", "region"], columns="category", values="gwh", aggfunc="sum").fillna(0.0) / 1000.0
    p = p.rename(columns=str.capitalize).reset_index()
    p.columns.name = None
    for c in ("Thermal", "Nuclear", "Hydro", "Bhutan"):
        if c not in p:
            p[c] = 0.0
    p["complete"] = True                      # March issue = full fiscal year
    return p


def npp_fuelwise():
    f = pd.read_csv(RAW / "npp_dgr17_fuelwise_fy.csv").set_index("fy")
    f.index.name = "FY"
    cols = [c for c in f.columns if c.endswith("_gwh")]
    out = f[cols] / 1000.0
    out.columns = [c.replace("_gwh", "") for c in cols]
    return out


def npp_region_fuel():
    d = pd.read_csv(RAW / "npp_18col_sub16_march_region_fuel_fy.csv", comment="#")
    p = d.pivot_table(index=["fy", "region"], columns="category", values="gwh", aggfunc="sum") / 1000.0
    p = p.rename(columns={"COAL_LIGNITE": "Coal", "GAS": "Gas", "HYDRO": "Hydro", "NUCLEAR": "Nuclear"}).reset_index()
    p.columns.name = None
    return p.rename(columns={"fy": "FY"})


def run():
    h, r, f = npp_history(), npp_regional(), npp_fuelwise()
    rf = npp_region_fuel()
    rf.to_csv(PROC / "npp_region_fuel_fy.csv", index=False)
    h.to_csv(PROC / "npp_history_national_twh.csv")
    r.to_csv(PROC / "npp_region_fy_conventional.csv", index=False)
    f.to_csv(PROC / "npp_fuelwise_fy_twh.csv")
    print(f"[ingest] NPP history FY{h.index.min()}-FY{h.index.max()}; NPP regional FY{r.FY.min()}-FY{r.FY.max()}; "
          f"DGR17 fuel-wise FY {list(f.index)}")
    return h, r, f


if __name__ == "__main__":
    run()
