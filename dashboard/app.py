"""INDIA 2047 - Forecast demand. Match regional strengths. Explain the mix.
Streamlit dashboard (ExxonMobil Innothon 2026). Data: National Power Portal (npp.gov.in) + organiser CSV only; no assumed
values. Runs from cached artefacts in outputs/; the Scenario Lab re-runs the forecast and the mix live.
Run:  streamlit run dashboard/app.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT, PROC, DOCS = ROOT / "outputs", ROOT / "data" / "processed", ROOT / "docs"

from src.config import REGIONS, REGION_NAME, TECHS, TECH_COLOR, NAVY, RED, REGION_COLOR  # noqa: E402

st.set_page_config(page_title="India 2047 | Generation forecast & regional mix", page_icon="⚡", layout="wide")
st.markdown(f"""
<style>
.block-container {{padding-top: 3.0rem; padding-bottom: 2rem; max-width: 1500px;}}
h1, h2, h3 {{color: {NAVY}; font-weight: 700;}}
.kpi {{background:#fff; border-radius:14px; padding:14px 18px; box-shadow:0 1px 6px rgba(11,45,107,.12); border-top:4px solid {NAVY}; height:100%;}}
.kpi.red {{border-top-color:{RED};}}
.kpi .v {{font-size:1.9rem; font-weight:800; color:{NAVY}; line-height:1.1;}}
.kpi .l {{font-size:.78rem; letter-spacing:.06em; text-transform:uppercase; color:#5b6475; font-weight:700;}}
.kpi .s {{font-size:.85rem; color:#39404d;}}
.take {{background:#F3F6FB; border-left:4px solid {NAVY}; padding:8px 12px; border-radius:6px; margin:4px 0 2px 0; font-size:.95rem;}}
.src {{font-size:.75rem; color:#6b7280; margin-bottom:14px;}}
.card {{background:#fff; border-radius:14px; padding:16px 20px; box-shadow:0 1px 6px rgba(11,45,107,.12);}}
.stTabs [data-baseweb="tab"] {{font-size:1.0rem; font-weight:600;}}
</style>""", unsafe_allow_html=True)
FONT = dict(family="Segoe UI, Helvetica, Arial", size=15, color="#1f2937")
SRC_NPP = "National Power Portal (npp.gov.in): history endpoint, CEA 18-column sub-reports 2 & 16, DGR17"
SRC_CSV = "Organiser CSV (population, GSDP; RE-fleet composition for the solar/wind/other split only)"


def style(fig, h=420, legend=True):
    fig.update_layout(template="plotly_white", font=FONT, height=h, margin=dict(l=10, r=10, t=40, b=10),
                      legend=dict(orientation="h", y=-0.15) if legend else dict(), hoverlabel=dict(font_size=14))
    return fig


def takeaway(text, source):
    st.markdown(f"<div class='take'>💡 {text}</div><div class='src'>Source: {source}</div>", unsafe_allow_html=True)


def kpi(col, value, label, sub="", red=False):
    col.markdown(f"<div class='kpi {'red' if red else ''}'><div class='l'>{label}</div><div class='v'>{value}</div>"
                 f"<div class='s'>{sub}</div></div>", unsafe_allow_html=True)


@st.cache_data
def load():
    d = {f: pd.read_csv(OUT / f"{f}.csv") for f in
         ["forecast_national", "forecast_region_year", "backtest_metrics", "backtest_predictions", "rolling_cv", "waterfall",
          "tornado", "mc_2047_draws", "history_national", "npp_consistency_check", "mix_pathway", "mix_shares_national",
          "mix_model_selection", "mix_validation", "kpis", "regional_backtest_metrics", "resource_scorecard"]}
    d["head"] = json.loads((OUT / "headline.json").read_text())
    d["summary"] = json.loads((OUT / "model_summary.json").read_text())
    d["params"] = pd.read_csv(DOCS / "parameters.csv")
    d["states_geo"] = json.loads((PROC / "india_states_simplified.geojson").read_text())
    d["dq"] = (OUT / "data_quality_report.md").read_text()
    cards = (DOCS / "regional_cards.md").read_text()
    d["cards"] = {}
    for blk in cards.split("\n## ")[1:]:
        first = blk.split("\n")[0]
        if "[" in first:
            d["cards"][first.split("[")[1].split("]")[0]] = "### " + blk.split("\n", 1)[0] + "\n" + blk.split("\n", 1)[1]
    return d


D = load()
H = D["head"]
BY = H["base_fy"]
MIX = D["mix_pathway"]


def mix_year(scen, year):
    return MIX[(MIX.scenario == scen) & (MIX.year == year)].pivot_table(index="region", columns="tech", values="twh").reindex(REGIONS)[TECHS]


def lq(m):
    return m.div(m.sum(axis=0), axis=1).div(m.sum(axis=1) / m.values.sum(), axis=0)


def region_map(highlight, labels):
    fig = go.Figure()
    for f in D["states_geo"]["features"]:
        rg_ = f["properties"]["region"]; gm = f["geometry"]
        polys = [gm["coordinates"]] if gm["type"] == "Polygon" else gm["coordinates"]
        for poly in polys:
            ring = np.array(poly[0])
            fig.add_trace(go.Scatter(x=ring[:, 0], y=ring[:, 1], fill="toself", mode="lines", line=dict(color="white", width=0.7),
                                     fillcolor=NAVY if rg_ == highlight else REGION_COLOR[rg_] + "55", hoverinfo="text",
                                     text=f"{f['properties']['state'].title()} – {REGION_NAME[rg_]}", showlegend=False))
    pos = {"NR": (73.0, 26.8), "WR": (71.2, 22.6), "SR": (77.6, 12.2), "ER": (85.6, 23.4), "NER": (93.4, 26.8)}
    fig.add_trace(go.Scatter(x=[pos[r][0] for r in REGIONS], y=[pos[r][1] for r in REGIONS], mode="markers+text",
                             text=[labels[r] for r in REGIONS], textposition="top center",
                             marker=dict(size=18, color="white", line=dict(color=NAVY, width=3)), textfont=dict(size=13, color="#111"),
                             hoverinfo="skip", showlegend=False))
    fig.update_xaxes(visible=False, range=[67.5, 98]); fig.update_yaxes(visible=False, range=[6, 37.5], scaleanchor="x", scaleratio=1.08)
    fig.update_layout(height=540, margin=dict(l=0, r=0, t=0, b=0), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", dragmode=False)
    return fig


# ------------------------------------------------------------------ header
c1, c2 = st.columns([0.70, 0.30])
c1.markdown(f"<h1 style='margin-bottom:0'>India 2047: generation forecast & regional mix</h1>"
            f"<div style='color:{RED};font-weight:700;font-size:1.05rem'>Forecast demand · Match regional strengths · Explain the mix</div>",
            unsafe_allow_html=True)
c2.markdown(f"<div class='card' style='font-size:.85rem'><b>Data:</b> National Power Portal + organiser CSV only – "
            f"<b>no assumed values</b>. Basis: energy <b>generated</b> (TWh), NPP all-India utility generation excl. Bhutan imports. "
            f"FY = April–March. Base year FY{BY} (last complete NPP year).</div>", unsafe_allow_html=True)

tabs = st.tabs(["🏠 Overview", "📈 Forecast", "🗺️ Regions", "⚡ Generation mix", "🎯 Regional strengths",
                "📊 Uncertainty", "🧪 Scenario Lab", "📚 Data & method"])

# ================================================================== 1. OVERVIEW
with tabs[0]:
    k = st.columns(5)
    kpi(k[0], f"{H['p50_2047']:,.0f} TWh", "FY2047 generation (P50)", f"P10 {H['p10_2047']:,.0f} – P90 {H['p90_2047']:,.0f}")
    kpi(k[1], f"{H['growth_x']:.1f}×", f"Growth vs FY{BY}", f"{H['actual_base']:,.0f} TWh → {H['cagr_pct']:.1f}%/yr", red=True)
    kpi(k[2], f"{100*H['nonfossil_2047']:.0f}%", "Non-fossil share 2047", f"from {100*H['nonfossil_base']:.0f}% in FY{BY}")
    kpi(k[3], f"{100*H['mix_2047']['Solar']/H['p50_2047']:.0f}% / {100*H['mix_2047']['Wind']/H['p50_2047']:.0f}%", "Solar / wind share 2047",
        f"from {100*H['mix_base']['Solar']/H['actual_base']:.0f}% / {100*H['mix_base']['Wind']/H['actual_base']:.0f}%", red=True)
    kpi(k[4], f"{H['val_2025']:+.1f}%", "FY2025 out-of-sample check", f"conventional gen. vs NPP actual (FY2026 {H['val_2026']:+.1f}%)")
    st.write("")
    n = D["forecast_national"]; b = n[n.scenario == "Base"]; hist = D["history_national"]
    left, right = st.columns([0.58, 0.42])
    with left:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist.FY, y=hist.Total, name="NPP actual", line=dict(color="#111", width=3)))
        fig.add_trace(go.Scatter(x=pd.concat([b.FY, b.FY[::-1]]), y=pd.concat([b.p90, b.p10[::-1]]), fill="toself",
                                 fillcolor="rgba(11,45,107,.15)", line=dict(width=0), name="P10–P90"))
        fig.add_trace(go.Scatter(x=b.FY, y=b.p50, name="P50 (Base)", line=dict(color=NAVY, width=3)))
        for sc, dash in (("Low", "dot"), ("High", "dash")):
            s = n[n.scenario == sc]
            fig.add_trace(go.Scatter(x=s.FY, y=s.p50, name=f"{sc} scenario", line=dict(color=RED, width=1.5, dash=dash)))
        for y in [2030, 2035, 2040, 2047]:
            v = b.set_index("FY").p50[y]
            fig.add_annotation(x=y, y=v, text=f"{v:,.0f}", showarrow=True, arrowhead=0, ay=-30, font=dict(color=NAVY, size=13))
        fig.update_yaxes(title="TWh generated")
        fig.update_layout(title="National generation: NPP history and forecast")
        st.plotly_chart(style(fig, 430), width="stretch")
    with right:
        nat47 = MIX[(MIX.scenario == "Base") & (MIX.year == 2047)].groupby("tech").twh.sum().reindex(TECHS)
        fig = go.Figure(go.Pie(labels=TECHS, values=nat47.values, hole=0.55, sort=False, marker=dict(colors=[TECH_COLOR[t] for t in TECHS]),
                               texttemplate="%{label}<br>%{percent:.0%}", textposition="outside"))
        fig.update_layout(title="FY2047 mix (Base, % of 100)", showlegend=False,
                          annotations=[dict(text=f"<b>{nat47.sum():,.0f}</b><br>TWh", showarrow=False, font_size=16)])
        st.plotly_chart(style(fig, 430, legend=False), width="stretch")
    takeaway(f"Generation grows from {H['actual_base']:,.0f} TWh (FY{BY}, NPP) to ~{H['p50_2047']:,.0f} TWh by FY2047 "
             f"({H['cagr_pct']:.1f}%/yr vs {H['hist_cagr']:.1f}%/yr in NPP FY2007–{BY}), driven by CSV population "
             f"(→ {H['pop_2047_m']:,.0f} M) and real GSDP ({H['gdp_cagr_csv']:.1f}%/yr). If NPP's trends continue, coal stays the "
             f"backbone while solar rises to {100*H['mix_2047']['Solar']/H['p50_2047']:.0f}%.", f"{SRC_NPP}; {SRC_CSV}")

# ================================================================== 2. FORECAST
with tabs[1]:
    st.markdown("### Three models, one ensemble")
    c = st.columns([0.62, 0.38])
    with c[0]:
        bb = b.set_index("FY")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist.FY, y=hist.Total, name="NPP actual", line=dict(color="#111", width=3)))
        for col, name, colr in [("m1_econometric", "M1 per-capita econometric", "#1F6FD1"), ("m2_intensity", "M2 intensity", "#14A39A"),
                                ("m3_timeseries", "M3 ARIMAX", "#F28C28"), ("ets_reference", "ETS (history only)", "#9CA3AF")]:
            fig.add_trace(go.Scatter(x=bb.index, y=bb[col], name=name, line=dict(color=colr, width=2, dash="dot" if "ets" in col else None)))
        fig.add_trace(go.Scatter(x=bb.index, y=bb.central_path, name="Ensemble", line=dict(color=NAVY, width=4)))
        fig.update_yaxes(title="TWh generated")
        st.plotly_chart(style(fig, 430), width="stretch")
    with c[1]:
        S = D["summary"]; s1 = S["M1 Econometric (per capita)"]; s2 = S["M2 Intensity (decomposition)"]; s3 = S["M3 Time-series ARIMAX"]
        st.markdown(f"""<div class='card'>
<b>M1 – why:</b> ln(kWh per person) on ln(GSDP per person): income elasticity <b>{s1['beta_lny']:.3f}</b> (HAC SE {s1['se_lny']:.3f}),
R² {s1['r2']:.3f}, n = {s1['n']}. Quadratic term tested, not identified (t = {s1['quadratic_test']['t_b2']:.2f}).<br><br>
<b>M2 – how big:</b> ln(generation / GDP) trend: drift <b>{100*s2['c']:+.2f}%/yr</b> (SE {100*s2['se_c']:.2f}).<br><br>
<b>M3 – what history says:</b> ln G on ln GDP, AR(1) errors: elasticity <b>{s3['b_gdp']:.3f}</b> (SE {s3['se_gdp']:.3f}), φ = {s3['phi']:.2f}.<br><br>
<b>Weights</b> (inverse hold-out MAPE): {', '.join(f"{k_.split(' (')[0]} {100*v:.0f}%" for k_, v in S['weights'].items())}.
<br><br>Sample FY2007–FY{BY}: NPP generation, CSV population and real GSDP.</div>""", unsafe_allow_html=True)
    st.markdown(f"### Back-test: train FY2007–2018, predict FY2019–{BY} with actual CSV drivers")
    c = st.columns([0.5, 0.5])
    with c[0]:
        bt = D["backtest_metrics"].set_index("model")
        cv = D["rolling_cv"].groupby("model").MAPE.mean().rename("Rolling-origin CV MAPE")
        st.dataframe(bt.join(cv).style.format("{:.2f}", na_rep="–"), width="stretch")
    with c[1]:
        bp = D["backtest_predictions"]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=bp.FY, y=bp.Actual, name="NPP actual", line=dict(color="#111", width=3)))
        fig.add_trace(go.Scatter(x=bp.FY, y=bp.Ensemble, name="Ensemble", line=dict(color=NAVY, width=3)))
        fig.add_trace(go.Scatter(x=bp.FY, y=bp["ETS (history only, reference)"], name="ETS", line=dict(color="#9CA3AF", dash="dot")))
        st.plotly_chart(style(fig, 300), width="stretch")
    takeaway(f"Ensemble hold-out MAPE {H['mape_ensemble']:.1f}% vs {H['mape_ets']:.1f}% for history-only extrapolation; the test "
             "window includes COVID.", "outputs/backtest_metrics.csv")
    st.markdown("### Out-of-sample check after the base year")
    v = D["mix_validation"]; vi = v[v.region == "India"]
    st.dataframe(vi.pivot_table(index="tech", columns="FY", values=["actual", "forecast", "diff_pct"]).round(1), width="stretch")
    takeaway(f"NPP has no RES figure after FY{BY}, but conventional generation (coal + gas + hydro + nuclear) is published: our FY2025 "
             f"forecast of it misses by {H['val_2025']:+.1f}%, FY2026 by {H['val_2026']:+.1f}% (a mild year in which thermal fell).",
             "NPP sub-report 16; outputs/mix_validation.csv")

# ================================================================== 3. REGIONS
with tabs[2]:
    scen = st.radio("Scenario", ["Low", "Base", "High"], index=1, horizontal=True, key="reg_scen")
    t = D["forecast_region_year"]; tt = t[(t.scenario == scen) & (t.region != "India")]
    c = st.columns([0.45, 0.55])
    with c[0]:
        t47 = tt[tt.year == 2047].set_index("region"); t0 = tt[tt.year == BY].set_index("region")
        st.plotly_chart(region_map(None, {r: f"{REGION_NAME[r]}<br>{t0.loc[r,'p50']:,.0f}→{t47.loc[r,'p50']:,.0f} TWh" for r in REGIONS}),
                        width="stretch")
    with c[1]:
        fig = go.Figure()
        for r in REGIONS:
            g = tt[tt.region == r]
            fig.add_trace(go.Scatter(x=g.year, y=g.p50, stackgroup="one", name=REGION_NAME[r], line=dict(color=REGION_COLOR[r], width=0.5)))
        fig.update_yaxes(title="TWh (P50)"); fig.update_layout(title=f"Regional requirement – {scen}")
        st.plotly_chart(style(fig, 380), width="stretch")
        st.dataframe(t47[["p10", "p50", "p90", "pop_m", "gsdp_index"]].rename(index=REGION_NAME).style.format(
            {"p10": "{:,.0f}", "p50": "{:,.0f}", "p90": "{:,.0f}", "pop_m": "{:,.0f}", "gsdp_index": "{:.2f}×"}), width="stretch")
    takeaway("Regional requirement = each region's CSV population × (GSDP per person)^ε (ε = M1 elasticity), reconciled so regions sum "
             "exactly to the national forecast. Where the generation is produced is the mix question (next tab).", SRC_CSV)
    st.dataframe(D["regional_backtest_metrics"].rename(columns={"MAPE": "Regional back-test MAPE (NPP conventional, FY2024-26)"}).round(1),
                 width="stretch")

# ================================================================== 4. MIX
with tabs[3]:
    scen = st.radio("Scenario", ["Low", "Base", "High"], index=1, horizontal=True, key="mix_scen")
    m = MIX[MIX.scenario == scen]
    nat = m.groupby(["year", "tech"]).twh.sum().unstack()[TECHS]
    pct = nat.div(nat.sum(axis=1), axis=0) * 100
    c = st.columns(2)
    with c[0]:
        fig = go.Figure()
        for tk in TECHS:
            fig.add_trace(go.Scatter(x=nat.index, y=nat[tk], stackgroup="one", name=tk, line=dict(color=TECH_COLOR[tk], width=0.5)))
        fig.update_yaxes(title="TWh generated"); fig.update_layout(title=f"National mix, TWh – {scen}")
        st.plotly_chart(style(fig, 400), width="stretch")
    with c[1]:
        fig = go.Figure()
        for tk in TECHS:
            fig.add_trace(go.Scatter(x=pct.index, y=pct[tk], stackgroup="one", groupnorm="percent", name=tk, line=dict(color=TECH_COLOR[tk], width=0.5)))
        fig.update_yaxes(title="% of generation", range=[0, 100]); fig.update_layout(title="National mix, % of 100")
        st.plotly_chart(style(fig, 400), width="stretch")
    st.markdown("#### Mix percentages (each row adds to 100%)")
    st.dataframe(pct.loc[[BY, 2030, 2035, 2040, 2047]].round(1).style.format("{:.1f}%"), width="stretch")
    yr = st.select_slider("Regional mix in year", options=[BY, 2030, 2035, 2040, 2047], value=2047, key="mix_year")
    mr = mix_year(scen, yr)
    fig = go.Figure()
    for tk in TECHS:
        fig.add_trace(go.Bar(x=[REGION_NAME[r] for r in REGIONS], y=mr[tk], name=tk, marker_color=TECH_COLOR[tk]))
    fig.update_layout(barmode="stack", title=f"Generation located in each region, FY{yr} (TWh)")
    st.plotly_chart(style(fig, 380), width="stretch")
    st.dataframe((mr.div(mr.sum(axis=1), axis=0) * 100).rename(index=REGION_NAME).round(1).style.format("{:.1f}%"), width="stretch")
    takeaway("Shares are trend projections of NPP history (and, for solar/wind/other inside RES, the CSV RE-fleet composition), each "
             "chosen by out-of-sample back-test – the mix 'if recent history continues', not an optimised plan.",
             f"{SRC_NPP}; {SRC_CSV}; outputs/mix_model_selection.csv")
    with st.expander("Which share model won each back-test"):
        sel = D["mix_model_selection"]
        st.dataframe(sel[sel.weight > 0][["panel", "family", "param", "MAE_pp", "weight", "test"]].round(3), width="stretch")

# ================================================================== 5. REGIONAL STRENGTHS
with tabs[4]:
    m47 = mix_year("Base", 2047); m0 = mix_year("Base", BY)
    L47 = lq(m47)
    c = st.columns([0.5, 0.5])
    with c[0]:
        fig = go.Figure(go.Heatmap(z=L47.values, x=TECHS, y=[REGION_NAME[r] for r in REGIONS], colorscale="Blues", zmin=0,
                                   text=L47.round(2).values, texttemplate="%{text}", colorbar=dict(title="LQ")))
        fig.update_layout(title="Revealed strength 2047 (location quotient; > 1 = specialises)")
        st.plotly_chart(style(fig, 380, legend=False), width="stretch")
    with c[1]:
        kb = D["kpis"]; kb = kb[(kb.scenario == "Base") & (kb.year == 2047) & (kb.region != "India")].set_index("region").reindex(REGIONS)
        fig = go.Figure(go.Bar(x=[REGION_NAME[r] for r in REGIONS], y=kb.net_export_twh,
                               marker_color=[NAVY if v >= 0 else RED for v in kb.net_export_twh], text=kb.net_export_twh.round(0), textposition="outside"))
        fig.update_layout(title="Implied net position 2047: generation located − requirement (TWh)")
        st.plotly_chart(style(fig, 380, legend=False), width="stretch")
    r = st.segmented_control("Region card", REGIONS, default="NR", format_func=lambda x: REGION_NAME[x], key="card_reg") or "NR"
    st.markdown(D["cards"].get(r, ""))

# ================================================================== 6. UNCERTAINTY
with tabs[5]:
    c = st.columns(2)
    with c[0]:
        wf = D["waterfall"]; wf = wf[wf.scenario == "Base"]
        meas = ["absolute"] + ["relative"] * (len(wf) - 2) + ["total"]
        fig = go.Figure(go.Waterfall(x=wf.component, y=wf.TWh, measure=meas, text=wf.TWh.round(0), textposition="outside",
                                     connector=dict(line=dict(color="#999"))))
        fig.update_layout(title=f"Trace the number: FY{BY} → FY2047 (Base)")
        st.plotly_chart(style(fig, 420, legend=False), width="stretch")
    with c[1]:
        tor = D["tornado"].iloc[::-1]
        fig = go.Figure()
        fig.add_trace(go.Bar(y=tor.input, x=tor.low, orientation="h", name="Low", marker_color=RED))
        fig.add_trace(go.Bar(y=tor.input, x=tor.high, orientation="h", name="High", marker_color=NAVY))
        fig.update_layout(barmode="overlay", title="2047 sensitivity (TWh vs Base)")
        st.plotly_chart(style(fig, 420), width="stretch")
    mc = D["mc_2047_draws"]
    fig = go.Figure(go.Histogram(x=mc.national_2047, nbinsx=60, marker_color=NAVY))
    for q, lab in ((10, "P10"), (50, "P50"), (90, "P90")):
        v_ = np.percentile(mc.national_2047, q)
        fig.add_vline(x=v_, line_color=RED, annotation_text=f"{lab} {v_:,.0f}")
    fig.update_layout(title="FY2047 Monte Carlo (5,000 draws, all distributions estimated from data)")
    st.plotly_chart(style(fig, 330, legend=False), width="stretch")
    takeaway(f"Largest source of uncertainty: {H['tornado_top']}. Every distribution comes from the data: GDP growth by bootstrapping "
             "the CSV's own annual growth rates, model elasticities from their standard errors, residuals from the back-test errors.",
             "outputs/tornado.csv, mc_2047_draws.csv")

# ================================================================== 7. SCENARIO LAB
with tabs[6]:
    from src.features import csv_trends
    from src.forecast.ensemble import national_forecast
    from src import mix as MX

    @st.cache_resource
    def engine():
        P = MX.panels()
        return P, MX.fit_all(P)

    tr = csv_trends()
    c = st.columns([0.3, 0.7])
    with c[0]:
        g = st.slider("Real GDP CAGR FY2024–47 (%)", 3.0, 8.0, round(100 * tr["gdp_cagr"], 1), 0.1,
                      help=f"CSV trend {100*tr['gdp_cagr']:.2f}%; bootstrap P10–P90 {100*tr['gdp_boot_p10']:.1f}–{100*tr['gdp_boot_p90']:.1f}%")
        z = st.slider("Model elasticity shock (SE units)", -2.0, 2.0, 0.0, 0.1)
        pz = st.slider("Population trend shock (SE units)", -2.0, 2.0, 0.0, 0.1)
    fc = national_forecast(cagr=g / 100, pop_z=pz, z_elast=z)
    tot = pd.Series(fc["total"][0], index=fc["years"])
    P, M = engine()
    mp_, sh_, _ = MX.build({"Lab": tot}, P=P, M=M)
    natm = mp_[mp_.year == 2047].groupby("tech").twh.sum().reindex(TECHS)
    with c[1]:
        k = st.columns(4)
        kpi(k[0], f"{tot.iloc[-1]:,.0f} TWh", "FY2047 generation", f"Base {H['central_2047']:,.0f}")
        kpi(k[1], f"{100*natm.drop(['Coal','Gas']).sum()/natm.sum():.0f}%", "Non-fossil 2047")
        kpi(k[2], f"{100*natm['Solar']/natm.sum():.0f}%", "Solar share 2047", red=True)
        kpi(k[3], f"{natm['Coal']:,.0f} TWh", "Coal 2047")
        nn = mp_.groupby(["year", "tech"]).twh.sum().unstack()[TECHS]
        fig = go.Figure()
        for tk in TECHS:
            fig.add_trace(go.Scatter(x=nn.index, y=nn[tk], stackgroup="one", name=tk, line=dict(color=TECH_COLOR[tk], width=0.5)))
        st.plotly_chart(style(fig, 380), width="stretch")
    takeaway("Moving a slider re-runs the three demand models and the back-tested share models; shares depend only weakly on the total "
             "(through the recent-increments family), so the mix percentages move less than the TWh.", "src/forecast/ensemble.py, src/mix.py")

# ================================================================== 8. DATA & METHOD
with tabs[7]:
    st.markdown(f"""
| Series | Source | Use |
|---|---|---|
| All-India generation by hydro / thermal / RES / nuclear, FY1947–FY{BY} | NPP Generation Dashboard history (`/dashBoard/get_generation_chart_list`) | Forecast target, level-1 mix shares |
| Region-wise coal / gas / hydro / nuclear by state, FY2019–FY2026 | NPP – CEA 18-column report, sub-report 16 (March issues) | Regional mix shares, coal/gas split, validation |
| Region-wise thermal / nuclear / hydro, FY2019–FY2026 | NPP – CEA 18-column report, sub-report 2 | Consistency check |
| Fuel-wise generation, FY2019, FY2021–25 | NPP – CEA Daily Generation Report 17 | Consistency check |
| Population, GSDP by state, 2006–2024 | Organiser CSV | Demand drivers |
| Installed solar / wind / bio / small-hydro / WtE by state | Organiser CSV | **Composition only**: splits NPP's single RES total into solar / wind / other and by region |
""")
    takeaway("Every number in the pipeline is estimated from these datasets (parameter register below). Energy generated (TWh) is the "
             "only basis; capacity never sets the level of generation.", "docs/parameters.csv")
    st.markdown("#### Parameter register (all estimated from NPP / CSV)")
    st.dataframe(D["params"], width="stretch", height=420)
    cc = D["npp_consistency_check"]
    st.markdown(f"#### NPP internal consistency: max |difference| {H['consistency_max']:.2f}% over {H['consistency_n']} comparisons")
    st.dataframe(cc.round(2), width="stretch", height=260)
    with st.expander("Data-quality report"):
        st.markdown(D["dq"])
    st.markdown("#### Limitations")
    st.markdown(f"""
* **Trend, not plan.** The mix shows where NPP's history leads if recent trends continue; it contains no costs, resource potentials or policy targets (these would require assumed values).
* **NPP gaps.** RES only as an all-India total, and only to FY{BY}; solar / wind / other and their regional location come from the CSV RE-fleet composition (generation per MW assumed equal across technologies by construction – a known simplification).
* **No urbanisation data** in NPP or the CSV; its effect sits inside income per person.
* **Short history** (18 annual points): declining income elasticity cannot be estimated.
""")
    for f in ["forecast_region_year.csv", "mix_pathway.csv", "kpis.csv", "mix_model_selection.csv", "backtest_metrics.csv", "npp_consistency_check.csv"]:
        st.download_button(f"⬇ {f}", (OUT / f).read_bytes(), file_name=f, key=f"dl_{f}")
