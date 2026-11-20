"""Static figures for the deck (maps are images; everything else is a native PowerPoint chart) and the
deck_data.json consumed by deck/build_deck.js."""
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MPoly, FancyArrowPatch
from src.config import OUT, PROC, FIG, ROOT, REGIONS, REGION_NAME, TECHS, TECH_COLOR, NAVY, RED

POS = {"NR": (73.0, 26.8), "WR": (71.8, 22.4), "SR": (77.6, 12.6), "ER": (85.6, 23.2), "NER": (93.2, 26.6)}
REG_FILL = {"NR": "#0B2D6B", "WR": "#3C6BC4", "SR": "#7FA7E8", "ER": "#E1251B", "NER": "#F08A84"}


def _draw_states(ax, fill_fn):
    g = json.loads((PROC / "india_states_simplified.geojson").read_text())
    for f in g["features"]:
        gm = f["geometry"]; r = f["properties"]["region"]
        polys = [gm["coordinates"]] if gm["type"] == "Polygon" else gm["coordinates"]
        for p in polys:
            ax.add_patch(MPoly(np.array(p[0]), closed=True, facecolor=fill_fn(r), edgecolor="white", lw=0.6))
    ax.set_xlim(67.5, 98); ax.set_ylim(6, 37.5); ax.set_aspect(1.08); ax.axis("off")


def map_regions(path, label_fn, dot_color=None):
    fig, ax = plt.subplots(figsize=(6.2, 6.6), dpi=200)
    _draw_states(ax, lambda r: REG_FILL[r])
    for r, (x, y) in POS.items():
        ax.scatter([x], [y], s=380, color=(dot_color(r) if dot_color else "white"), edgecolor="white", lw=2.5, zorder=5)
        ax.text(x, y + 1.25, label_fn(r), ha="center", va="bottom", fontsize=10.5, fontweight="bold", color="#111",
                bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=0.92), zorder=6)
    fig.tight_layout(pad=0.1); fig.savefig(path, transparent=True); plt.close(fig)


def map_net(path, net):
    """Implied net position 2047 = generation located in the region - its requirement (TWh)."""
    fig, ax = plt.subplots(figsize=(6.2, 6.6), dpi=200)
    _draw_states(ax, lambda r: "#DCE4F1")
    mx = max(abs(v) for v in net.values())
    for r, (x, y) in POS.items():
        v = net[r]
        ax.scatter([x], [y], s=150 + 2400 * abs(v) / mx, color=(NAVY if v >= 0 else RED), alpha=0.85, edgecolor="white", lw=2, zorder=5)
        ax.text(x, y - 2.0, f"{REGION_NAME[r]}\n{'exports' if v >= 0 else 'imports'} {abs(v):,.0f} TWh", ha="center", va="top",
                fontsize=9.5, fontweight="bold", color=(NAVY if v >= 0 else RED),
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.9), zorder=6)
    fig.tight_layout(pad=0.1); fig.savefig(path, transparent=True); plt.close(fig)


def anchors(m):
    """Data-revealed regional strength = technology with the highest location quotient
    (region's share of national output of that technology / region's share of national generation)."""
    lq = m.div(m.sum(axis=0), axis=1).div(m.sum(axis=1) / m.values.sum(), axis=0)
    return {r: lq.loc[r].idxmax() for r in m.index}


def build():
    H = json.loads((OUT / "headline.json").read_text())
    BY = H["base_fy"]
    t = pd.read_csv(OUT / "forecast_region_year.csv")
    k = pd.read_csv(OUT / "kpis.csv")
    mp = pd.read_csv(OUT / "mix_pathway.csv")
    mb = mp[mp.scenario == "Base"]
    req47 = t[(t.scenario == "Base") & (t.year == 2047)].set_index("region")
    reqb = t[(t.scenario == "Base") & (t.year == BY)].set_index("region")
    map_regions(FIG / "map_requirement.png", lambda r: f"{REGION_NAME[r]}\n{reqb.loc[r,'p50']:,.0f} → {req47.loc[r,'p50']:,.0f} TWh")
    m47 = mb[mb.year == 2047].pivot_table(index="region", columns="tech", values="twh")[TECHS]
    mbase = mb[mb.year == BY].pivot_table(index="region", columns="tech", values="twh")[TECHS]
    anchor = anchors(m47)
    map_regions(FIG / "map_anchor.png", lambda r: f"{REGION_NAME[r]}: {anchor[r]}\n{100*m47.loc[r, anchor[r]]/m47[anchor[r]].sum():.0f}% of India's {anchor[r].lower()}",
                dot_color=lambda r: TECH_COLOR[anchor[r]])
    kb = k[k.scenario == "Base"]
    net47 = {r: float(kb[(kb.region == r) & (kb.year == 2047)].net_export_twh.iloc[0]) for r in REGIONS}
    map_net(FIG / "map_net_2047.png", net47)

    n = pd.read_csv(OUT / "forecast_national.csv")
    hist = pd.read_csv(OUT / "history_national.csv")
    b = n[n.scenario == "Base"]
    wf = pd.read_csv(OUT / "waterfall.csv"); wf = wf[wf.scenario == "Base"]
    tor = pd.read_csv(OUT / "tornado.csv")
    bt = pd.read_csv(OUT / "backtest_metrics.csv")
    val = pd.read_csv(OUT / "mix_validation.csv")
    sel = pd.read_csv(OUT / "mix_model_selection.csv")
    years = list(range(2007, 2048))
    act = hist.set_index("FY").Total.reindex(years)
    bb = b.set_index("FY")
    vr = val[val.tech == "All conventional"].set_index("FY")
    data = dict(
        head=H,
        fan=dict(years=years, actual=[None if np.isnan(v) else round(v) for v in act.values],
                 p10=[round(bb.p10.get(y)) if y in bb.index and y > BY else None for y in years],
                 p50=[round(bb.p50.get(y)) if y in bb.index and y > BY else None for y in years],
                 p90=[round(bb.p90.get(y)) if y in bb.index and y > BY else None for y in years],
                 low=[round(n[(n.scenario == "Low") & (n.FY == y)].p50.iloc[0]) if y > BY else None for y in years],
                 high=[round(n[(n.scenario == "High") & (n.FY == y)].p50.iloc[0]) if y > BY else None for y in years]),
        waterfall=[dict(c=r.component, v=round(r.TWh)) for r in wf.itertuples()],
        tornado=[dict(i=r.input, lo=round(r.low), hi=round(r.high), sw=round(r.swing)) for r in tor.itertuples()],
        backtest=[dict(m=r.model, mape=round(r.MAPE, 2)) for r in bt.itertuples()],
        validation=[dict(fy=int(y), actual=round(r.actual), forecast=round(r.forecast), diff=round(r.diff_pct, 1)) for y, r in vr.iterrows()],
        selection=[dict(p=r.panel, f=r.family, a=int(r.param), mae=round(r.MAE_pp, 2), w=round(r.weight, 2)) for r in sel[sel.weight > 0].itertuples()],
        mix47={r: {tk: round(float(m47.loc[r, tk]), 1) for tk in TECHS} for r in REGIONS},
        mixbase={r: {tk: round(float(mbase.loc[r, tk]), 1) for tk in TECHS} for r in REGIONS},
        anchor=anchor,
        nat_path={str(y): {tk: round(float(mb[(mb.year == y) & (mb.tech == tk)].twh.sum())) for tk in TECHS} for y in [BY, 2030, 2035, 2040, 2047]},
        req={r: dict(p10=round(req47.loc[r, "p10"]), p50=round(req47.loc[r, "p50"]), p90=round(req47.loc[r, "p90"]), yb=round(reqb.loc[r, "p50"])) for r in REGIONS},
        kpi_region={r: {c: round(float(kb[(kb.region == r) & (kb.year == 2047)][c].iloc[0]), 3) for c in
                        ["nonfossil_share", "res_share", "net_export_twh", "generation_twh", "requirement_twh"]} for r in REGIONS},
        nf_path={str(y): round(float(kb[(kb.region == "India") & (kb.year == y)].nonfossil_share.iloc[0]), 3) for y in [BY, 2030, 2035, 2040, 2047]},
        summary=json.loads((OUT / "model_summary.json").read_text()),
        tech_colors={tk: TECH_COLOR[tk].lstrip("#") for tk in TECHS},
        fig_dir=str(FIG),
    )
    (ROOT / "deck" / "deck_data.json").write_text(json.dumps(data, indent=1, default=float))
    print("[figs] maps + deck_data.json written")


if __name__ == "__main__":
    build()
