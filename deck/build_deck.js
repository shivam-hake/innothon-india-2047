// Defensibility deck (14 slides) for the Innothon 2026 jury. Built from deck_data.json (python -m src.report_figs).
// Run: node deck/build_deck.js   -> deck/India2047_defensibility_deck.pptx
const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");
const SKILL = process.env.PPTX_SKILL_DIR || "";
const D = JSON.parse(fs.readFileSync(path.join(__dirname, "deck_data.json"), "utf8"));
const FIG = D.fig_dir;
const H = D.head;

const THEME = {
  name: "India2047", headFontFace: "Arial", bodyFontFace: "Calibri",
  colors: { dk1: "1F2937", lt1: "FFFFFF", dk2: "0B2D6B", lt2: "EEF2F8", accent1: "0B2D6B", accent2: "E1251B",
            accent3: "F5B700", accent4: "14A39A", accent5: "7B3FA0", accent6: "1F6FD1", hlink: "1F6FD1", folHlink: "7B3FA0" },
};
const NAVY = "0B2D6B", RED = "E1251B", INK = "1F2937", MUTED = "5B6475", ICE = "EEF2F8", GRID = "D9DEE7";
const TC = D.tech_colors;
const TECHS = ["Coal", "Gas", "Nuclear", "Hydro", "Solar", "Wind", "Other RE"];
const REG = ["NR", "WR", "SR", "ER", "NER"];
const RN = { NR: "Northern", WR: "Western", SR: "Southern", ER: "Eastern", NER: "North-Eastern" };
const f0 = (v) => Math.round(v).toLocaleString("en-US");

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "India 2047 - generation forecast and regional mix";
pres.author = "Innothon 2026 team";
const C = pres.SchemeColor;

pres.defineSlideMaster({
  title: "TITLE_DARK", background: { color: NAVY },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.7, y: 1.6, w: 11.9, h: 1.6, fontSize: 40, bold: true, color: "FFFFFF", valign: "top", align: "left" }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.7, y: 3.35, w: 11.9, h: 1.6, fontSize: 20, color: "CADCFC", valign: "top" }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENT", background: { color: "FFFFFF" },
  margin: [0.5, 0.5, 0.6, 0.5],
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.3, w: 12.3, h: 0.85, fontSize: 26, bold: true, color: NAVY, valign: "middle", align: "left" }, text: "" } },
    { text: { text: "Innothon 2026 · India 2047 · Forecast demand. Match regional strengths. Explain the mix.", options: { x: 0.5, y: 7.08, w: 9, h: 0.3, fontSize: 10, color: MUTED } } },
  ],
  slideNumber: { x: 12.3, y: 7.08, w: 0.5, h: 0.3, fontSize: 10, color: MUTED },
});

function source(slide, text) {
  slide.addText("Source: " + text, { x: 0.5, y: 6.7, w: 12.3, h: 0.35, fontSize: 10, color: MUTED, isTextBox: true, margin: 0 });
}
function card(slide, x, y, w, h, fill) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.12, fill: { color: fill || ICE }, line: { color: fill || ICE },
    shadow: { type: "outer", color: "9AA6BB", opacity: 0.25, blur: 4, offset: 1.5, angle: 90 } });
}
function stat(slide, x, y, w, big, label, color) {
  card(slide, x, y, w, 1.45, "FFFFFF");
  slide.addText(big, { x: x + 0.2, y: y + 0.12, w: w - 0.4, h: 0.75, fontSize: 28, bold: true, color: color || NAVY, fontFace: "Arial", isTextBox: true, margin: 0 });
  slide.addText(label, { x: x + 0.2, y: y + 0.88, w: w - 0.4, h: 0.5, fontSize: 12, color: MUTED, isTextBox: true, margin: 0 });
}
function bullets(slide, items, x, y, w, h, size) {
  slide.addText(items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1, paraSpaceAfter: 6 } })),
    { x, y, w, h, fontSize: size || 15, color: INK, valign: "top", isTextBox: true });
}
const axisOpts = { catAxisLabelColor: MUTED, valAxisLabelColor: MUTED, catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt",
  catAxisLabelFontSize: 11, valAxisLabelFontSize: 11, valGridLine: { color: GRID, size: 0.5 }, catGridLine: { style: "none" },
  legendFontFace: "+mn-lt", legendFontSize: 11, legendColor: MUTED, dataLabelFontFace: "+mn-lt" };

// ---------------------------------------------------------------- helpers on data
const BY = H.base_fy;
const pc = (v, tot) => Math.round(100 * v / tot);
const M47 = H.mix_2047, MB = H.mix_base;
const T47 = Object.values(M47).reduce((a, b) => a + b, 0), TB = Object.values(MB).reduce((a, b) => a + b, 0);
const SM = D.summary, S1 = SM["M1 Econometric (per capita)"], S2 = SM["M2 Intensity (decomposition)"], S3 = SM["M3 Time-series ARIMAX"];

// ---------------------------------------------------------------- 1 Title
pres.addSection({ title: "Answer" });
let s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Answer" });
s.addText("India needs ~" + f0(Math.round(H.p50_2047 / 10) * 10) + " TWh of generation in FY2047", { placeholder: "title" });
s.addText(`P10 ${f0(H.p10_2047)} – P90 ${f0(H.p90_2047)} TWh · ${H.growth_x.toFixed(1)}× FY${BY} · if NPP's trends continue the mix is ${pc(M47.Coal, T47)}% coal, ${pc(M47.Solar, T47)}% solar, ${pc(M47.Wind, T47)}% wind, ${pc(M47.Hydro, T47)}% hydro, ${pc(M47.Nuclear, T47)}% nuclear. Built only from the National Power Portal and the organiser CSV – no assumed values.`, { placeholder: "body" });
s.addText("ExxonMobil Innothon 2026 · Defensibility review", { x: 0.7, y: 6.3, w: 8, h: 0.4, fontSize: 14, color: "FFFFFF", isTextBox: true });
s.addNotes("One-line answer first. Every number traces to outputs/*.csv and is reproduced by python run_all.py. Every parameter is estimated from NPP or the CSV: docs/parameters.csv.");

// ---------------------------------------------------------------- 2 Data policy
pres.addSection({ title: "Approach" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Approach" });
s.addText("Two datasets, zero assumed values", { placeholder: "title" });
card(s, 0.5, 1.4, 6.0, 5.1);
s.addText("What we use", { x: 0.75, y: 1.55, w: 5.5, h: 0.45, fontSize: 20, bold: true, color: NAVY, isTextBox: true, margin: 0 });
bullets(s, [`National Power Portal: all-India generation by hydro / thermal / RES / nuclear (FY1947–FY${BY}); region- and state-wise coal, gas, hydro, nuclear (CEA sub-report 16, FY2019–26)`,
  "Organiser CSV: population and real GSDP by state (demand drivers)",
  "CSV installed solar / wind / bio / small-hydro mix – only as shares, to split NPP's single RES total into solar, wind, other and by region",
  `Every parameter estimated from these data and listed in docs/parameters.csv (${D.selection.length} share-model weights, elasticities, trends)`], 0.75, 2.05, 5.5, 4.3, 15);
card(s, 6.85, 1.4, 6.0, 5.1);
s.addText("What we never use", { x: 7.1, y: 1.55, w: 5.5, h: 0.45, fontSize: 20, bold: true, color: RED, isTextBox: true, margin: 0 });
bullets(s, ["Capacity to set the level of generation, or as a comparison – generation (TWh) is the only basis",
  "Consumption, sales or 'energy requirement' series",
  "Any other dataset, outside study or benchmark – a unit test checks data/raw and every NPP source URL",
  "Assumed costs, resource potentials, policy targets or new-load sizes – none exist in the pipeline (unit test)"], 7.1, 2.05, 5.5, 4.3, 15);
source(s, "tests/test_invariants.py::test_only_permitted_datasets, ::test_no_assumed_values, ::test_capacity_never_drives_generation_level");
s.addNotes("The price of 'no assumptions': the mix is a data-trend projection ('where history leads'), not a cost-optimised plan. We say so openly.");

// ---------------------------------------------------------------- 3 Data foundation
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Approach" });
s.addText("We found and fixed the data traps before modelling", { placeholder: "title" });
const quirks = [
  ["Capacity, not generation", "5 'Installed –' MW columns never drive generation; only their mix (shares) splits NPP RES"],
  ["Non-standard zones", "Rajasthan West→Northern, MP/Chhattisgarh 'Central'→Western, Sikkim→Eastern"],
  ["Missing rows", "Telangana 2013 gap interpolated; Delhi / Chandigarh backcast at their own CSV growth"],
  ["2024 carry-forward", "19 of 34 states repeat 2023 capacity; GSDP 2024 carry-forward replaced by the CSV's own 2023 growth"],
  ["GSDP base break", "2011 total = 2.2× 2010: pre-2011 spliced with the CSV's own growth rates"],
  ["NPP gaps", `No RES after FY${BY} → FY${BY} is the base year; FY2025–26 NPP conventional actuals kept for out-of-sample checks`],
];
quirks.forEach((q, i) => {
  const col = i % 2, row = Math.floor(i / 2);
  const x = 0.5 + col * 6.2, y = 1.35 + row * 1.25;
  card(s, x, y, 6.0, 1.1);
  s.addText(q[0], { x: x + 0.2, y: y + 0.08, w: 5.6, h: 0.38, fontSize: 15, bold: true, color: NAVY, isTextBox: true, margin: 0 });
  s.addText(q[1], { x: x + 0.2, y: y + 0.46, w: 5.6, h: 0.6, fontSize: 13, color: INK, isTextBox: true, margin: 0 });
});
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.5, y: 5.2, w: 12.3, h: 1.35, rectRadius: 0.12, fill: { color: NAVY }, line: { color: NAVY } });
s.addText([{ text: "Consistency check passed: ", options: { bold: true, color: "FFFFFF" } },
  { text: `four NPP products (history endpoint, 18-column sub-reports 2 and 16, DGR17) agree within ${H.consistency_max.toFixed(2)}% on ${H.consistency_n} overlapping year × fuel comparisons (bar ±2%).`, options: { color: "FFFFFF" } }],
  { x: 0.8, y: 5.3, w: 11.8, h: 1.15, fontSize: 16, valign: "middle", isTextBox: true });
source(s, "outputs/data_quality_report.md, npp_consistency_check.csv; npp.gov.in (accessed 19/20-11-2026); organiser CSV");

// ---------------------------------------------------------------- 4 Method + backtest
pres.addSection({ title: "Forecast" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Forecast" });
s.addText("Three models, blended by back-test accuracy", { placeholder: "title" });
const models = [["M1 Per-capita econometric – why", `ln(NPP kWh per person) on ln(CSV real GSDP per person), FY2007–${BY}: income elasticity ${S1.beta_lny.toFixed(2)} (SE ${S1.se_lny.toFixed(2)}); curvature tested, not identified`],
  ["M2 Intensity – how big", `ln(generation / CSV GDP) trend: ${(100 * S2.c).toFixed(2)}%/yr drift (SE ${(100 * S2.se_c).toFixed(2)})`],
  ["M3 ARIMAX – what history says", `ln G on ln GDP with AR(1) errors and a COVID dummy: GDP elasticity ${S3.b_gdp.toFixed(2)}, φ = ${S3.phi.toFixed(2)}`]];
models.forEach((m, i) => {
  card(s, 0.5, 1.35 + i * 1.42, 5.9, 1.27);
  s.addText(m[0], { x: 0.7, y: 1.43 + i * 1.42, w: 5.5, h: 0.4, fontSize: 16, bold: true, color: NAVY, isTextBox: true, margin: 0 });
  s.addText(m[1], { x: 0.7, y: 1.83 + i * 1.42, w: 5.5, h: 0.75, fontSize: 13, color: INK, isTextBox: true, margin: 0 });
});
s.addText(`Weights = inverse hold-out MAPE: ${Object.entries(SM.weights).map(([k, v]) => k.split(" (")[0].replace(" Econometric", "").replace(" Intensity", "").replace(" Time-series ARIMAX", "") + " " + Math.round(100 * v) + "%").join(" · ")}. No add-on demand modules.`, { x: 0.5, y: 5.65, w: 5.9, h: 0.8, fontSize: 13, italic: true, color: RED, isTextBox: true, margin: 0 });
const bt = D.backtest;
s.addChart(pres.charts.BAR, [{ name: "MAPE %", labels: bt.map(b => b.m.replace(" (history only, reference)", " (ref.)")), values: bt.map(b => b.mape) }], {
  x: 6.8, y: 1.3, w: 6.0, h: 5.2, barDir: "bar", showTitle: true, title: `Hold-out MAPE, FY2019–${BY} (train FY2007–2018)`, titleFontSize: 14, titleColor: NAVY, titleFontFace: "+mn-lt",
  chartColors: ["7FA7E8", "7FA7E8", "7FA7E8", "BFC6D1", RED], showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.0\"%\"", dataLabelFontSize: 12,
  showLegend: false, valAxisHidden: true, ...axisOpts, catAxisLabelFontSize: 12 });
source(s, "outputs/backtest_metrics.csv, rolling_cv.csv, model_summary.json");

// ---------------------------------------------------------------- 5 Fan
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Forecast" });
s.addText(`${f0(H.p50_2047)} TWh in FY2047 (P50), ${H.cagr_pct.toFixed(1)}%/yr – NPP history FY2007–${BY}: ${H.hist_cagr.toFixed(1)}%/yr`, { placeholder: "title" });
const fy = D.fan.years.map(String);
const nz = (arr) => arr.map(v => (v === null ? "" : v));
s.addChart(pres.charts.LINE, [
  { name: "NPP actual", labels: fy, values: nz(D.fan.actual) }, { name: "P10", labels: fy, values: nz(D.fan.p10) },
  { name: "P50 (Base)", labels: fy, values: nz(D.fan.p50) }, { name: "P90", labels: fy, values: nz(D.fan.p90) },
  { name: "Low scenario", labels: fy, values: nz(D.fan.low) }, { name: "High scenario", labels: fy, values: nz(D.fan.high) }], {
  x: 0.5, y: 1.3, w: 8.4, h: 5.3, chartColors: ["1F2937", "9DB4DA", NAVY, "9DB4DA", RED, RED], lineSize: 2, lineDataSymbol: "none",
  showLegend: true, legendPos: "b", valAxisTitle: "TWh generated", showValAxisTitle: true, valAxisTitleFontSize: 11, valAxisTitleColor: MUTED,
  catAxisLabelFrequency: 5, ...axisOpts });
s.addText("Waypoints, Base P50 (TWh)", { x: 9.3, y: 1.4, w: 3.3, h: 0.45, fontSize: 15, bold: true, color: NAVY, isTextBox: true, margin: 0 });
s.addTable([[{ text: "FY", options: { bold: true } }, { text: "P50", options: { bold: true } }],
  [String(BY) + " (NPP)", f0(H.actual_base)], ["2030", f0(H.p50_2030)], ["2035", f0(H.p50_2035)], ["2040", f0(H.p50_2040)], ["2047", f0(H.p50_2047)]],
  { x: 9.25, y: 1.9, w: 3.4, colW: [1.7, 1.7], fontSize: 12, color: INK, border: { type: "solid", color: GRID, pt: 0.5 } });
s.addText(`Scenarios = P10 / P90 of GDP growth from bootstrapping the CSV's own annual growth (${H.gdp_low.toFixed(1)}% / ${H.gdp_high.toFixed(1)}% vs ${H.gdp_cagr_csv.toFixed(1)}%): Low ${f0(H.low_2047)}, High ${f0(H.high_2047)} TWh. Out of sample, FY2025 conventional generation missed by ${H.val_2025 > 0 ? "+" : ""}${H.val_2025.toFixed(1)}%.`, { x: 9.3, y: 4.45, w: 3.3, h: 2.1, fontSize: 11.5, color: INK, isTextBox: true, margin: 0 });
source(s, "outputs/forecast_national.csv (5,000-draw Monte Carlo), mix_validation.csv; history: npp.gov.in");

// ---------------------------------------------------------------- 6 Waterfall
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Forecast" });
s.addText("Trace the number: more people, and more electricity per person", { placeholder: "title" });
const wf = D.waterfall;
s.addChart(pres.charts.BAR, [{ name: "TWh", labels: wf.map(w => w.c.replace(" (CSV trend)", "").replace(" (income, CSV GSDP)", "")), values: wf.map(w => w.v) }], {
  x: 0.5, y: 1.3, w: 7.6, h: 5.2, barDir: "col", chartColors: [NAVY, "7FA7E8", "14A39A", RED], showValue: true, dataLabelPosition: "outEnd",
  dataLabelFormatCode: "#,##0", showLegend: false, ...axisOpts, catAxisLabelFontSize: 12 });
bullets(s, [`Population (CSV trend, growth falling ${Math.abs(SM.drivers.pop_decay * 100).toFixed(1)}% a year): ${f0(H.pop_base_m)} M → ${f0(H.pop_2047_m)} M adds ${f0(wf[1].v)} TWh`,
  `Generation per person (driven by CSV real GSDP per person): ${f0(H.kwh_pc_base)} → ${f0(H.kwh_pc_2047)} kWh adds ${f0(wf[2].v)} TWh`,
  "Urbanisation: neither NPP nor the CSV has urbanisation data, so its effect is inside income per person – stated, not invented",
  "No add-on modules (H₂, EVs, data centres): they would need assumed sizes; their effect is only what the 2007–2024 trend already contains"], 8.4, 1.5, 4.4, 5.0, 14);
source(s, "outputs/waterfall.csv (additive LMDI on the Base ensemble path)");

// ---------------------------------------------------------------- 7 Regions
pres.addSection({ title: "Regions" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Regions" });
const gx = REG.map(r => D.req[r].p50 / D.req[r].yb);
s.addText(`Every region grows ${Math.min(...gx).toFixed(1)}–${Math.max(...gx).toFixed(1)}×; regions sum exactly to the national total`, { placeholder: "title" });
s.addImage({ path: path.join(FIG, "map_requirement.png"), x: 0.5, y: 1.25, w: 5.0, h: 5.3, altText: "Map of regional requirement" });
const rq = D.req;
s.addTable([[{ text: "Region", options: { bold: true } }, { text: `FY${BY}`, options: { bold: true } }, { text: "2047 P10", options: { bold: true } }, { text: "2047 P50", options: { bold: true } }, { text: "2047 P90", options: { bold: true } }],
  ...REG.map(r => [RN[r], f0(rq[r].yb), f0(rq[r].p10), f0(rq[r].p50), f0(rq[r].p90)])],
  { x: 5.8, y: 1.4, w: 7.0, colW: [1.8, 1.3, 1.3, 1.3, 1.3], fontSize: 13, color: INK, border: { type: "solid", color: GRID, pt: 0.5 } });
bullets(s, ["Requirement = each region's CSV population × (GSDP per person)^ε, ε = M1 elasticity; state shares follow their own CSV trends",
  "MinT reconciliation: regions add up exactly to the national forecast (unit test)",
  "Regional bands carry national uncertainty plus share uncertainty from the state-trend standard errors"], 5.8, 4.3, 7.0, 2.2, 13);
source(s, "outputs/forecast_region_year.csv; organiser CSV (population, GSDP)");

// ---------------------------------------------------------------- 8 Mix method
pres.addSection({ title: "Mix" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Mix" });
s.addText("The mix: nested shares, each chosen by out-of-sample back-test", { placeholder: "title" });
const lv = [["Level 1 · national sources", "Thermal / hydro / nuclear / RES shares of NPP generation, FY2007–2024"],
  ["Level 2 · inside thermal and RES", "Coal vs gas: NPP sub-report 16. Solar vs wind vs other: CSV RE-fleet mix (shares only)"],
  ["Level 3 · where it is generated", "Each region's share of India's coal, gas, hydro, nuclear (NPP) and solar, wind, other (CSV mix)"]];
lv.forEach((m, i) => {
  card(s, 0.5, 1.35 + i * 1.5, 5.9, 1.35);
  s.addText(m[0], { x: 0.7, y: 1.43 + i * 1.5, w: 5.5, h: 0.4, fontSize: 16, bold: true, color: NAVY, isTextBox: true, margin: 0 });
  s.addText(m[1], { x: 0.7, y: 1.85 + i * 1.5, w: 5.5, h: 0.8, fontSize: 13, color: INK, isTextBox: true, margin: 0 });
});
s.addText("Candidate families per share: constant (no change), multinomial-logit trend (diffusion), recent increments (additions continue). Best window per family on a hold-out; families blended by inverse error.", { x: 0.5, y: 5.9, w: 5.9, h: 0.75, fontSize: 12, italic: true, color: RED, isTextBox: true, margin: 0 });
const selRows = D.selection.filter(r => r.p.startsWith("L1") || r.p.startsWith("L2"));
s.addTable([[{ text: "Share panel", options: { bold: true } }, { text: "Family", options: { bold: true } }, { text: "Hold-out MAE (pp)", options: { bold: true } }, { text: "Weight", options: { bold: true } }],
  ...selRows.map(r => [r.p.replace(/ \(.*\)/, ""), `${r.f}(${r.a})`, r.mae.toFixed(2), r.w.toFixed(2)])],
  { x: 6.8, y: 1.35, w: 6.0, colW: [2.9, 1.1, 1.2, 0.8], fontSize: 11, color: INK, border: { type: "solid", color: GRID, pt: 0.5 } });
source(s, "src/mix.py; outputs/mix_model_selection.csv");
s.addNotes("Why this is not an assumption: the candidate set is fixed in advance and the data picks among them by out-of-sample error. The CSV fleet mix splits NPP's single RES number because NPP publishes no solar/wind split; it implies equal output per MW across RE types - a stated simplification.");

// ---------------------------------------------------------------- 9 National mix pathway
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Mix" });
s.addText(`If trends continue: coal ${pc(M47.Coal, T47)}%, solar ${pc(M47.Solar, T47)}%, non-fossil ${Math.round(100 * H.nonfossil_2047)}% by 2047`, { placeholder: "title" });
const yrs = [String(BY), "2030", "2035", "2040", "2047"];
s.addChart(pres.charts.BAR, TECHS.map(tk => ({ name: tk, labels: yrs, values: yrs.map(y => D.nat_path[y][tk]) })), {
  x: 0.5, y: 1.3, w: 7.6, h: 5.25, barDir: "col", barGrouping: "percentStacked", chartColors: TECHS.map(tk => TC[tk]),
  showLegend: true, legendPos: "b", showValue: false, ...axisOpts, valAxisLabelFormatCode: "0%", showTitle: true, title: "National mix, % of generation (Base)", titleFontSize: 14, titleColor: NAVY, titleFontFace: "+mn-lt" });
s.addTable([[{ text: "Source", options: { bold: true } }, { text: `FY${BY}`, options: { bold: true } }, { text: "2047", options: { bold: true } }, { text: "2047 TWh", options: { bold: true } }],
  ...TECHS.map(tk => [tk, pc(MB[tk], TB) + "%", pc(M47[tk], T47) + "%", f0(M47[tk])])],
  { x: 8.4, y: 1.4, w: 4.4, colW: [1.3, 1.0, 1.0, 1.1], fontSize: 12, color: INK, border: { type: "solid", color: GRID, pt: 0.5 } });
s.addText("Solar's share of RES keeps rising (recent CSV additions are mostly solar); wind grows in TWh but its share falls. Coal grows in TWh because NPP's thermal share has barely moved since 2007.", { x: 8.4, y: 4.75, w: 4.4, h: 1.8, fontSize: 12, color: INK, isTextBox: true, margin: 0 });
source(s, "outputs/mix_pathway.csv, mix_shares_national.csv");

// ---------------------------------------------------------------- 10 Regional strengths
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Mix" });
s.addText("Regional strengths revealed by the data", { placeholder: "title" });
s.addImage({ path: path.join(FIG, "map_anchor.png"), x: 0.5, y: 1.25, w: 5.0, h: 5.3, altText: "Map of each region's strongest technology" });
const kr = D.kpi_region;
REG.forEach((r, i) => {
  const a = D.anchor[r], m = D.mix47[r], tot = Object.values(m).reduce((x, y) => x + y, 0);
  const share = Math.round(100 * m[a] / REG.map(q => D.mix47[q][a]).reduce((x, y) => x + y, 0));
  card(s, 5.8, 1.3 + i * 1.06, 7.0, 0.96, "FFFFFF");
  s.addText(`${RN[r]} · ${a}`, { x: 6.0, y: 1.36 + i * 1.06, w: 3.0, h: 0.36, fontSize: 14, bold: true, color: NAVY, isTextBox: true, margin: 0 });
  s.addText(`${share}% of India's ${a.toLowerCase()} in 2047 · non-fossil ${Math.round(100 * kr[r].nonfossil_share)}% · ${kr[r].net_export_twh >= 0 ? "exports" : "imports"} ${f0(Math.abs(kr[r].net_export_twh))} TWh`,
    { x: 6.0, y: 1.72 + i * 1.06, w: 6.6, h: 0.45, fontSize: 12, color: INK, isTextBox: true, margin: 0 });
});
source(s, "Location quotient (region's share of India's output of a source ÷ its share of generation) on outputs/mix_pathway.csv; docs/regional_cards.md");
s.addNotes("Strength = location quotient, computed, not chosen: NR hydro (half of NPP hydro), WR and SR wind (CSV fleet), ER coal (96% of its NPP conventional output), NER gas (Assam/Tripura plants in NPP sub-report 16).");

// ---------------------------------------------------------------- 11 Regional mix 2047
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Mix" });
s.addText("Where the 2047 generation sits – and who imports", { placeholder: "title" });
s.addChart(pres.charts.BAR, TECHS.map(tk => ({ name: tk, labels: REG.map(r => RN[r]), values: REG.map(r => D.mix47[r][tk]) })), {
  x: 0.5, y: 1.3, w: 7.3, h: 5.25, barDir: "col", barGrouping: "stacked", chartColors: TECHS.map(tk => TC[tk]), showLegend: true, legendPos: "b",
  ...axisOpts, showTitle: true, title: "Generation located in each region, FY2047 (TWh, Base)", titleFontSize: 14, titleColor: NAVY, titleFontFace: "+mn-lt" });
s.addImage({ path: path.join(FIG, "map_net_2047.png"), x: 8.1, y: 1.25, w: 4.7, h: 5.0, altText: "Implied net export or import by region in 2047" });
source(s, "outputs/kpis.csv: net position = generation located in the region − its requirement (implied inter-regional transfer)");

// ---------------------------------------------------------------- 12 Uncertainty
pres.addSection({ title: "Robustness" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Robustness" });
s.addText("GDP growth moves the answer most – every range comes from the data", { placeholder: "title" });
const tor = D.tornado.slice().reverse();
s.addChart(pres.charts.BAR, [{ name: "Low", labels: tor.map(t => t.i), values: tor.map(t => t.lo) }, { name: "High", labels: tor.map(t => t.i), values: tor.map(t => t.hi) }], {
  x: 0.5, y: 1.3, w: 8.0, h: 5.2, barDir: "bar", barGrouping: "clustered", barOverlapPct: 100, chartColors: [RED, NAVY], showLegend: true, legendPos: "b",
  ...axisOpts, catAxisLabelFontSize: 11, catAxisLabelPos: "low", showTitle: true, title: "FY2047 swing vs Base (TWh)", titleFontSize: 14, titleColor: NAVY, titleFontFace: "+mn-lt" });
bullets(s, [`GDP: bootstrap of the CSV's annual growth rates → P10–P90 ${H.gdp_low.toFixed(1)}–${H.gdp_high.toFixed(1)}%/yr`,
  "Model elasticities: each model's own estimated standard error",
  "Residual: the ensemble's own back-test errors, resampled",
  "Population: the CSV trend is so regular that its slope uncertainty barely moves 2047",
  `80% interval ${f0(H.p10_2047)}–${f0(H.p90_2047)} TWh (±${Math.round(50 * (H.p90_2047 - H.p10_2047) / H.p50_2047)}%)`], 8.8, 1.5, 4.0, 5.0, 13);
source(s, "outputs/tornado.csv, mc_2047_draws.csv");

// ---------------------------------------------------------------- 13 Limits
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Robustness" });
s.addText("What 'no assumptions' costs – and how we defend it", { placeholder: "title" });
const lim = [["Trend, not plan", "The mix shows where NPP history leads. Costs, resource potentials and policy targets would all need assumed values – so they are out, by design."],
  ["NPP has one RES number", `Solar / wind / other and their regions come from the CSV RE-fleet mix (shares only) – implies equal output per MW; FY${BY} RES itself is NPP-actual.`],
  ["No urbanisation series", "Neither dataset has one; its effect sits inside income per person (M1), not as a separate bar."],
  ["Short history", "18 annual points: a falling income elasticity cannot be estimated; tested and reported as not identified."],
  ["Coal keeps growing", "Because NPP's thermal share moved only 79% → 78% in 17 years; trend models cannot see future policy."]];
lim.forEach((q, i) => {
  card(s, 0.5, 1.3 + i * 1.07, 12.3, 0.95, i % 2 ? "FFFFFF" : ICE);
  s.addText(q[0], { x: 0.7, y: 1.38 + i * 1.07, w: 3.0, h: 0.8, fontSize: 15, bold: true, color: NAVY, valign: "middle", isTextBox: true, margin: 0 });
  s.addText(q[1], { x: 3.8, y: 1.38 + i * 1.07, w: 8.8, h: 0.8, fontSize: 13, color: INK, valign: "middle", isTextBox: true, margin: 0 });
});
source(s, "docs/methodology.md §8; docs/qa_prep.md");

// ---------------------------------------------------------------- 14 Demo
pres.addSection({ title: "Demo" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Demo" });
s.addText("Live dashboard: trace, compare, stress-test", { placeholder: "title" });
s.addImage({ path: path.join(FIG, "dashboard_overview.png"), x: 0.5, y: 1.3, w: 6.2, h: 5.37, altText: "Dashboard overview tab" });
bullets(s, ["8 tabs: Overview · Forecast & back-test · Regions · Generation mix (% of 100) · Regional strengths & cards · Uncertainty · Scenario Lab (forecast + mix re-run live) · Data & method",
  "Run: pip install -r requirements.txt → streamlit run dashboard/app.py",
  "Reproduce everything: python run_all.py (or make all); 10 invariant tests incl. data-policy and no-assumption tests",
  "Repo: docs/methodology.md (+PDF), docs/parameters.csv (every number and how it was estimated), docs/regional_cards.md, docs/qa_prep.md"], 7.0, 1.4, 5.8, 5.2, 14);
source(s, "dashboard/app.py; README.md");

(async () => {
  const out = path.join(__dirname, "India2047_defensibility_deck.pptx");
  await pres.writeFile({ fileName: out });
  if (SKILL) {
    const { applyTheme } = require(path.join(SKILL, "scripts", "apply_theme.js"));
    await applyTheme(out, THEME);
  }
  console.log("[deck] written", out);
})();
