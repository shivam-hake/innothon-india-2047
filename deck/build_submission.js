// InnoThon 2026 submission deck (7 slides) - Team DynamiX.
// Data: deck_data.json + submission_data.json (python -m src.report_figs, then the prep snippet in docs).
// Run: node deck/build_submission.js  -> deck/DynamiX_InnoThon2026.pptx
const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const Fa = require("react-icons/fa");

const SKILL = process.env.PPTX_SKILL_DIR || "";
const D = JSON.parse(fs.readFileSync(path.join(__dirname, "deck_data.json"), "utf8"));
const S = JSON.parse(fs.readFileSync(path.join(__dirname, "submission_data.json"), "utf8"));
const H = D.head, FIG = D.fig_dir, BY = H.base_fy;

const THEME = {
  name: "DynamiX", headFontFace: "Arial", bodyFontFace: "Calibri",
  colors: { dk1: "1F2937", lt1: "FFFFFF", dk2: "0B2D6B", lt2: "EEF2F8", accent1: "0B2D6B", accent2: "E1251B",
            accent3: "F5B700", accent4: "14A39A", accent5: "7B3FA0", accent6: "1F6FD1", hlink: "1F6FD1", folHlink: "7B3FA0" },
};
const NAVY = "0B2D6B", RED = "E1251B", INK = "1F2937", MUTED = "5B6475", ICE = "EEF2F8", GRID = "D9DEE7", SKY = "7FA7E8";
const TC = D.tech_colors;
const TECHS = ["Coal", "Gas", "Nuclear", "Hydro", "Solar", "Wind", "Other RE"];
const MSG = { NR: "Protect and grow hydro; 42% of India's hydro", WR: "The exporter: build lines to the South", SR: "Biggest demand: grow wind and solar fastest here", ER: "Almost all coal: first in line for a managed transition", NER: "Keep gas as backup, grow hydro" };
const REG = ["NR", "WR", "SR", "ER", "NER"];
const RN = { NR: "Northern", WR: "Western", SR: "Southern", ER: "Eastern", NER: "North-Eastern" };
const f0 = (v) => Math.round(v).toLocaleString("en-US");

async function icon(Comp, color, size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Comp, { color: "#" + color, size: String(size) }));
  const png = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + png.toString("base64");
}

(async () => {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  pres.title = "InnoThon 2026 - Team DynamiX - India 2047";
  pres.author = "Team DynamiX";

  pres.defineSlideMaster({
    title: "TITLE_DARK", background: { color: NAVY },
    objects: [{ placeholder: { options: { name: "title", type: "title", x: 0.7, y: 1.05, w: 11.9, h: 1.3, fontSize: 54, bold: true, color: "FFFFFF", valign: "top", align: "left" }, text: "" } }],
  });
  pres.defineSlideMaster({
    title: "CONTENT", background: { color: "FFFFFF" },
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.28, w: 12.3, h: 0.8, fontSize: 26, bold: true, color: NAVY, valign: "middle", align: "left" }, text: "" } },
      { text: { text: "InnoThon 2026 · Team DynamiX · India 2047", options: { x: 0.5, y: 7.08, w: 6, h: 0.3, fontSize: 10, color: MUTED } } },
    ],
    slideNumber: { x: 12.3, y: 7.08, w: 0.5, h: 0.3, fontSize: 10, color: MUTED },
  });

  const card = (s, x, y, w, h, fill, name) => s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.1, objectName: name || "card",
    fill: { color: fill || ICE }, line: { color: fill || ICE } });
  const txt = (s, t, o) => s.addText(t, { isTextBox: true, margin: 0, color: INK, ...o });
  const source = (s, t) => txt(s, "Source: " + t, { x: 0.5, y: 6.75, w: 12.3, h: 0.3, fontSize: 9.5, color: MUTED });
  const ax = { catAxisLabelColor: MUTED, valAxisLabelColor: MUTED, catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt",
    catAxisLabelFontSize: 10, valAxisLabelFontSize: 10, valGridLine: { color: GRID, size: 0.5 }, catGridLine: { style: "none" },
    legendFontFace: "+mn-lt", legendFontSize: 10, legendColor: MUTED, dataLabelFontFace: "+mn-lt", titleFontFace: "+mn-lt", titleColor: NAVY, titleFontSize: 13 };
  const stat = (s, x, y, w, big, label, color) => {
    card(s, x, y, w, 1.15, "FFFFFF", "stat");
    s.addShape(pres.shapes.RECTANGLE, { x, y, w: 0.08, h: 1.15, fill: { color: color || NAVY }, line: { color: color || NAVY } });
    txt(s, big, { x: x + 0.25, y: y + 0.1, w: w - 0.35, h: 0.6, fontSize: 26, bold: true, color: color || NAVY, fontFace: "Arial" });
    txt(s, label, { x: x + 0.25, y: y + 0.68, w: w - 0.35, h: 0.42, fontSize: 11.5, color: MUTED });
  };
  const arrow = (s, x, y, w) => s.addShape(pres.shapes.RIGHT_ARROW, { x, y, w, h: 0.32, fill: { color: SKY }, line: { color: SKY } });

  const ic = {
    db: await icon(Fa.FaDatabase, "FFFFFF"), broom: await icon(Fa.FaBroom, "FFFFFF"), check: await icon(Fa.FaCheckDouble, "FFFFFF"),
    chart: await icon(Fa.FaChartLine, "FFFFFF"), bolt: await icon(Fa.FaBolt, "FFFFFF"), map: await icon(Fa.FaMapMarkedAlt, "FFFFFF"),
    users: await icon(Fa.FaUsers, "FFFFFF"), rupee: await icon(Fa.FaRupeeSign, "FFFFFF"), layers: await icon(Fa.FaLayerGroup, "FFFFFF"),
    warn: await icon(Fa.FaExclamationTriangle, RED), rocket: await icon(Fa.FaRocket, NAVY), link: await icon(Fa.FaLink, "FFFFFF"),
    github: await icon(Fa.FaGithub, "FFFFFF"),
  };
  const iconCircle = (s, x, y, d, data, fill) => {
    s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill || NAVY }, line: { color: fill || NAVY } });
    s.addImage({ data, x: x + d * 0.24, y: y + d * 0.24, w: d * 0.52, h: d * 0.52 });
  };

  const M47 = S.nat_pct["2047"], MB = S.nat_pct[String(BY)];

  // ============================================================ 1 Title
  pres.addSection({ title: "Title" });
  let s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Title" });
  s.addText("InnoThon 2026", { placeholder: "title" });
  txt(s, "Team DynamiX", { x: 0.7, y: 2.35, w: 8, h: 0.6, fontSize: 28, bold: true, color: "F5B700" });
  txt(s, "India 2047: how much electricity the country will generate, where, and from which sources",
    { x: 0.7, y: 3.0, w: 11.5, h: 0.6, fontSize: 20, color: "CADCFC" });
  const tstats = [[`${f0(H.p50_2047)} TWh`, "generation needed in FY2047"], [`${H.growth_x.toFixed(1)}×`, `today's level (FY${BY})`],
    [`${Math.round(100 * H.nonfossil_2047)}%`, `non-fossil share (from ${Math.round(100 * H.nonfossil_base)}%)`], [`${H.mape_ensemble.toFixed(1)}%`, "error on years the model never saw"]];
  tstats.forEach((t, i) => {
    const x = 0.7 + i * 3.05;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 4.25, w: 2.85, h: 1.4, rectRadius: 0.1, fill: { color: "17407F" }, line: { color: "17407F" } });
    txt(s, t[0], { x: x + 0.2, y: 4.35, w: 2.5, h: 0.7, fontSize: 30, bold: true, color: "FFFFFF", fontFace: "Arial" });
    txt(s, t[1], { x: x + 0.2, y: 5.05, w: 2.5, h: 0.5, fontSize: 12.5, color: "CADCFC" });
  });
  txt(s, "Data: National Power Portal (npp.gov.in) and the organiser CSV only · All figures are energy generated (TWh)",
    { x: 0.7, y: 6.45, w: 11.9, h: 0.4, fontSize: 13, color: "CADCFC" });
  [["qr_dashboard.png", "Live dashboard", 9.55], ["qr_github.png", "GitHub code", 11.2]].forEach(q => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: q[2], y: 0.45, w: 1.45, h: 1.75, rectRadius: 0.08, fill: { color: "FFFFFF" }, line: { color: "FFFFFF" } });
    s.addImage({ path: path.join(FIG, q[0]), x: q[2] + 0.1, y: 0.55, w: 1.25, h: 1.25, altText: "QR code: " + q[1] });
    txt(s, q[1], { x: q[2], y: 1.83, w: 1.45, h: 0.3, fontSize: 11, bold: true, color: NAVY, align: "center" });
  });
  s.addNotes("Team DynamiX. One sentence: India will need about 4,740 TWh of generation in 2047, 2.8 times today, and we show where it is generated and from which sources, using only NPP and the organiser's CSV.");

  // ============================================================ 2 What we did
  pres.addSection({ title: "What we did" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "What we did" });
  s.addText("What we did: explore the data, clean it, check it, then model", { placeholder: "title" });
  const hy = S.hist.fy.map(String);
  s.addChart(pres.charts.AREA, [
    { name: "Thermal", labels: hy, values: S.hist.thermal }, { name: "Hydro", labels: hy, values: S.hist.hydro },
    { name: "Nuclear", labels: hy, values: S.hist.nuclear }, { name: "Renewables (RES)", labels: hy, values: S.hist.res }], {
    x: 0.5, y: 1.15, w: 6.15, h: 3.15, barGrouping: "stacked", chartColors: ["3A3A3A", "1F6FD1", "7B3FA0", "F5B700"],
    showTitle: true, title: `EDA 1 · NPP generation by source, FY2007–${BY} (TWh)`, showLegend: true, legendPos: "b", catAxisLabelFrequency: 3, ...ax });
  const base0 = S.csv.pop[0], g0 = S.csv.gdp[0];
  const cy = S.csv.fy.map(String);
  s.addChart(pres.charts.LINE, [
    { name: "Population (CSV)", labels: cy, values: S.csv.pop.map(v => +(100 * v / base0).toFixed(1)) },
    { name: "Real GSDP (CSV)", labels: cy, values: S.csv.gdp.map(v => +(100 * v / g0).toFixed(1)) },
    { name: "Generation (NPP)", labels: cy, values: cy.map(y => { const i = S.hist.fy.indexOf(+y); return i < 0 ? "" : +(100 * (S.hist.thermal[i] + S.hist.hydro[i] + S.hist.nuclear[i] + S.hist.res[i]) / (S.hist.thermal[0] + S.hist.hydro[0] + S.hist.nuclear[0] + S.hist.res[0])).toFixed(1); }) }], {
    x: 6.85, y: 1.15, w: 6.0, h: 3.15, chartColors: [SKY, "14A39A", NAVY], lineSize: 2.5, lineDataSymbol: "none",
    showTitle: true, title: "EDA 2 · Drivers vs generation (FY2007 = 100)", showLegend: true, legendPos: "b", catAxisLabelFrequency: 3, ...ax });
  const steps = [
    [ic.db, "Collect", "4 NPP reports (national history, region & station-wise, fuel-wise) + organiser CSV"],
    [ic.broom, "Clean", "6 zones remapped to 5 grid regions · missing years filled · 2011 GSDP break spliced · capacity columns kept out of demand"],
    [ic.check, "Verify", `4 NPP sources agree within ${S.cons.mx}% on ${S.cons.n} overlapping checks`],
    [ic.chart, "Model", `Forecast FY${BY}–2047 nationally and for 5 regions, then the generation mix`]];
  steps.forEach((st, i) => {
    const x = 0.5 + i * 3.15;
    card(s, x, 4.5, 2.85, 2.1, ICE, "step");
    iconCircle(s, x + 0.2, 4.65, 0.62, st[0], i === 2 ? RED : NAVY);
    txt(s, `${i + 1}. ${st[1]}`, { x: x + 0.95, y: 4.72, w: 1.8, h: 0.45, fontSize: 16, bold: true, color: NAVY });
    txt(s, st[2], { x: x + 0.2, y: 5.38, w: 2.5, h: 1.15, fontSize: 11.5, valign: "top" });
    if (i < 3) arrow(s, x + 2.88, 5.38, 0.24);
  });
  source(s, "npp.gov.in (generation dashboard history; CEA 18-column sub-reports 2 & 16; DGR17); organiser CSV; outputs/data_quality_report.md");
  s.addNotes("EDA 1: thermal has stayed near 78% of generation since 2007; renewables grew fastest. EDA 2: generation grew faster than population and close to GDP, which is why income is the main driver. Data problems we fixed: non-standard zones, a missing Telangana year, a GSDP base change in 2011 and a carry-forward in 2024. Four NPP reports agree within 0.13%.");

  // ============================================================ 3 National results
  pres.addSection({ title: "Results" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
  s.addText(`India needs ${H.growth_x.toFixed(1)}× today's electricity by 2047: ${f0(H.p50_2047)} TWh`, { placeholder: "title" });
  stat(s, 0.5, 1.15, 2.95, `${f0(H.p50_2047)} TWh`, `FY2047 base case (P50)`);
  stat(s, 3.6, 1.15, 2.95, `${f0(H.p10_2047)}–${f0(H.p90_2047)}`, "80% range (TWh)", SKY);
  stat(s, 6.7, 1.15, 2.95, `${H.cagr_pct.toFixed(1)}% / yr`, `growth (history: ${H.hist_cagr.toFixed(1)}%)`, "14A39A");
  stat(s, 9.8, 1.15, 3.05, `${f0(H.kwh_pc_base)} → ${f0(H.kwh_pc_2047)}`, "kWh per person", RED);
  const fy = D.fan.years.map(String), nz = (a) => a.map(v => (v === null ? "" : v));
  s.addChart(pres.charts.LINE, [
    { name: "NPP actual", labels: fy, values: nz(D.fan.actual) }, { name: "P10", labels: fy, values: nz(D.fan.p10) },
    { name: "P50 base case", labels: fy, values: nz(D.fan.p50) }, { name: "P90", labels: fy, values: nz(D.fan.p90) },
    { name: "Low", labels: fy, values: nz(D.fan.low) }, { name: "High", labels: fy, values: nz(D.fan.high) }], {
    x: 0.5, y: 2.45, w: 6.6, h: 4.2, chartColors: ["1F2937", "B9C9E6", NAVY, "B9C9E6", RED, RED], lineSize: 2.25, lineDataSymbol: "none",
    showTitle: true, title: "Total generation (TWh): history and forecast", showLegend: true, legendPos: "b", catAxisLabelFrequency: 5, ...ax });
  s.addChart(pres.charts.DOUGHNUT, [{ name: "2047 mix", labels: TECHS, values: TECHS.map(t => M47[t]) }], {
    x: 7.25, y: 2.4, w: 2.9, h: 2.75, holeSize: 55, chartColors: TECHS.map(t => TC[t]), showLegend: false, showPercent: false, showValue: false,
    showTitle: true, title: "FY2047 mix", ...ax });
  TECHS.forEach((t, i) => {
    const y = 2.5 + i * 0.37;
    s.addShape(pres.shapes.RECTANGLE, { x: 10.35, y: y + 0.07, w: 0.2, h: 0.2, fill: { color: TC[t] }, line: { color: TC[t] } });
    txt(s, t, { x: 10.62, y, w: 1.25, h: 0.34, fontSize: 12 });
    txt(s, `${MB[t].toFixed(0)}% → ${M47[t].toFixed(0)}%`, { x: 11.75, y, w: 1.1, h: 0.34, fontSize: 12, bold: true, color: NAVY, align: "right" });
  });
  card(s, 7.25, 5.2, 2.85, 1.45, NAVY, "benchmark");
  txt(s, [{ text: "Benchmark\n", options: { bold: true, color: "F5B700", breakLine: false } },
    { text: `Error on hidden years: ${H.mape_ensemble.toFixed(1)}% (simple trend line: ${H.mape_ets.toFixed(1)}%)`, options: { color: "FFFFFF" } }],
    { x: 7.4, y: 5.25, w: 2.6, h: 1.35, fontSize: 12, valign: "middle" });
  const vc = S.val_conv;
  s.addChart(pres.charts.BAR, [{ name: "NPP actual", labels: vc.map(v => "FY" + v.fy), values: vc.map(v => v.a) },
    { name: "Our forecast", labels: vc.map(v => "FY" + v.fy), values: vc.map(v => v.f) }], {
    x: 10.2, y: 5.1, w: 2.65, h: 1.6, barDir: "col", barGrouping: "clustered", chartColors: ["9CA3AF", NAVY], showValue: true, dataLabelPosition: "outEnd",
    dataLabelFormatCode: "#,##0", dataLabelFontSize: 9, valAxisHidden: true, showLegend: true, legendPos: "b", ...ax, legendFontSize: 9,
    valAxisMinVal: 1200, showTitle: true, title: `Blind check: ${vc[0].d > 0 ? "+" : ""}${vc[0].d}% / ${vc[1].d > 0 ? "+" : ""}${vc[1].d}%`, titleFontSize: 10.5 });
  source(s, "outputs/forecast_national.csv (5,000-draw Monte Carlo), mix_pathway.csv, backtest_metrics.csv, mix_validation.csv");
  s.addNotes(`Low and High use the CSV's own lower and upper GDP growth (${H.gdp_low.toFixed(1)}% and ${H.gdp_high.toFixed(1)}% a year). The mix shows coal still at ${M47.Coal.toFixed(0)}% because NPP's thermal share has barely moved since 2007; solar rises from ${MB.Solar.toFixed(0)}% to ${M47.Solar.toFixed(0)}%. Benchmark: our models halve the error of a plain trend line on the six years we hid from them.`);

  // ============================================================ 4 Regional results
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
  s.addText("The South needs the most, the West supplies it", { placeholder: "title" });
  s.addImage({ path: path.join(FIG, "map_anchor.png"), x: 0.35, y: 1.1, w: 4.75, h: 5.05, altText: "Map of India's five grid regions with each region's strongest source" });
  txt(s, "Strength = the source a region produces more of than its size suggests", { x: 0.5, y: 6.18, w: 4.6, h: 0.5, fontSize: 10.5, italic: true, color: MUTED });
  s.addChart(pres.charts.BAR, [
    { name: `FY${BY} (NPP-based)`, labels: REG.map(r => RN[r]), values: REG.map(r => S.req[r][String(BY)]) },
    { name: "FY2047 forecast", labels: REG.map(r => RN[r]), values: REG.map(r => S.req[r]["2047"]) }], {
    x: 5.3, y: 1.1, w: 7.55, h: 2.85, barDir: "col", barGrouping: "clustered", chartColors: [SKY, NAVY], showValue: true, dataLabelPosition: "outEnd",
    dataLabelFormatCode: "#,##0", dataLabelFontSize: 10, showLegend: true, legendPos: "b",
    showTitle: true, title: "Electricity each region needs (TWh)", valAxisHidden: true, ...ax });
  const kr = D.kpi_region;
  REG.forEach((r, i) => {
    const x = 5.3 + i * 1.53, a = D.anchor[r], net = kr[r].net_export_twh;
    card(s, x, 4.15, 1.43, 2.52, i % 2 ? "FFFFFF" : ICE, "region");
    s.addShape(pres.shapes.RECTANGLE, { x, y: 4.15, w: 1.43, h: 0.08, fill: { color: TC[a] }, line: { color: TC[a] } });
    txt(s, RN[r], { x: x + 0.1, y: 4.28, w: 1.25, h: 0.3, fontSize: 12, bold: true, color: NAVY });
    txt(s, a, { x: x + 0.1, y: 4.58, w: 1.25, h: 0.36, fontSize: 16, bold: true, color: a === "Solar" ? "B8860B" : TC[a] });
    txt(s, `${f0(S.req[r][String(BY)])} → ${f0(S.req[r]["2047"])} TWh · ${Math.round(100 * kr[r].nonfossil_share)}% clean`, { x: x + 0.1, y: 4.95, w: 1.3, h: 0.42, fontSize: 9.5 });
    txt(s, `${net >= 0 ? "Exports" : "Imports"} ${f0(Math.abs(net))} TWh`, { x: x + 0.1, y: 5.38, w: 1.3, h: 0.3, fontSize: 10.5, bold: true, color: net >= 0 ? NAVY : RED });
    s.addShape(pres.shapes.LINE, { x: x + 0.1, y: 5.74, w: 1.23, h: 0, line: { color: GRID, width: 1 } });
    txt(s, MSG[r], { x: x + 0.1, y: 5.8, w: 1.27, h: 0.82, fontSize: 9.5, italic: true, color: INK, valign: "top" });
  });
  source(s, "outputs/forecast_region_year.csv, kpis.csv, mix_pathway.csv; NPP sub-report 16 (regional fuel data); CSV population & GSDP");
  s.addNotes("Southern needs the most power by 2047 because of its population and income. Western generates the most and exports to the South. Strengths come from data: Northern holds about 42% of India's hydro, Western and Southern most of the wind, Eastern is almost all coal, North-Eastern hosts 40% of India's gas plants. Regions always add up exactly to the national total.");

  // ============================================================ 5 How the forecast works
  pres.addSection({ title: "Method" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Method" });
  s.addText("How the forecast works: three models, weighted by accuracy", { placeholder: "title" });
  card(s, 0.5, 1.2, 1.9, 2.75, NAVY, "drivers");
  iconCircle(s, 1.1, 1.35, 0.7, ic.users, "17407F");
  txt(s, "Drivers", { x: 0.6, y: 2.15, w: 1.7, h: 0.4, fontSize: 15, bold: true, color: "FFFFFF", align: "center" });
  txt(s, `Population → ${f0(H.pop_2047_m)} M\nGDP +${H.gdp_cagr_csv.toFixed(1)}%/yr\n(both from CSV trends)`, { x: 0.6, y: 2.6, w: 1.7, h: 1.2, fontSize: 11.5, color: "CADCFC", align: "center" });
  const SM = D.summary, w = SM.weights;
  const mods = [["M1 · Per person", "Electricity per person rises with income per person", w["M1 Econometric (per capita)"]],
    ["M2 · Intensity", "Electricity per rupee of GDP follows its trend", w["M2 Intensity (decomposition)"]],
    ["M3 · Time series", "Generation follows GDP; errors carry year to year", w["M3 Time-series ARIMAX"]]];
  arrow(s, 2.45, 2.43, 0.35);
  mods.forEach((m, i) => {
    const y = 1.2 + i * 0.95;
    card(s, 2.85, y, 2.9, 0.85, ICE, "model");
    txt(s, m[0], { x: 3.0, y: y + 0.06, w: 2.0, h: 0.32, fontSize: 13.5, bold: true, color: NAVY });
    txt(s, `${Math.round(100 * m[2])}%`, { x: 4.95, y: y + 0.06, w: 0.7, h: 0.32, fontSize: 13.5, bold: true, color: RED, align: "right" });
    txt(s, m[1], { x: 3.0, y: y + 0.4, w: 2.65, h: 0.42, fontSize: 10.5 });
  });
  arrow(s, 5.8, 2.43, 0.35);
  card(s, 6.2, 1.2, 1.75, 2.75, RED, "ensemble");
  iconCircle(s, 6.72, 1.35, 0.7, ic.layers, "B51C14");
  txt(s, "Combined forecast", { x: 6.25, y: 2.15, w: 1.65, h: 0.6, fontSize: 14, bold: true, color: "FFFFFF", align: "center" });
  txt(s, "weights = how accurate each model was", { x: 6.3, y: 2.8, w: 1.55, h: 1.0, fontSize: 11, color: "FFE4E1", align: "center" });
  const bt = D.backtest;
  s.addChart(pres.charts.BAR, [{ name: "Error %", labels: bt.map(b => b.m.replace(" (history only, reference)", " (trend only)").replace(" Econometric (per capita)", " per person").replace(" Intensity (decomposition)", " intensity").replace(" Time-series ARIMAX", " time series")), values: bt.map(b => b.mape) }], {
    x: 8.2, y: 1.1, w: 4.65, h: 2.95, barDir: "bar", chartColors: [SKY, SKY, SKY, "BFC6D1", RED], showValue: true, dataLabelPosition: "outEnd",
    dataLabelFormatCode: "0.0\"%\"", dataLabelFontSize: 11, showLegend: false, valAxisHidden: true, showTitle: true,
    title: `Error on hidden years FY2019–${BY}`, ...ax, catAxisLabelFontSize: 10.5 });
  txt(s, "How we tested and picked the model", { x: 0.5, y: 4.12, w: 6, h: 0.34, fontSize: 15, bold: true, color: NAVY });
  // timeline FY2007-FY2047, proportional to years
  const X0 = 0.5, PER = 12.35 / 41;
  const segs = [[2007, 2018, "Train · FY2007–2018 (12 yrs)", NAVY, "FFFFFF"], [2019, BY, `Validate · FY2019–${String(BY).slice(2)} (hidden)`, RED, "FFFFFF"],
    [BY + 1, BY + 2, `Check FY${BY + 1}–${BY + 2}`, "14A39A", "FFFFFF"], [BY + 3, 2047, `Forecast · FY${BY + 1}–2047 (check years included)`, "DCE4F1", NAVY]];
  segs.forEach(g => {
    const x = X0 + (g[0] - 2007) * PER, wseg = (g[1] - g[0] + 1) * PER;
    s.addShape(pres.shapes.RECTANGLE, { x, y: 4.5, w: wseg - 0.03, h: 0.42, fill: { color: g[3] }, line: { color: g[3] }, objectName: "timeline" });
    txt(s, g[2], { x: x + 0.05, y: 4.5, w: wseg - 0.1, h: 0.42, fontSize: g[0] === BY + 1 ? 8.5 : 11, bold: true, color: g[4], align: "center", valign: "middle" });
  });
  const how = [["Hide the last 6 years", `Fit on FY2007–2018 only, then predict FY2019–${BY} (includes COVID)`],
    ["Test again from 5 start years", `Rolling check (FY2013, 15, 17, 19, 21 starts): M1 ${S.cv["M1 Econometric (per capita)"]}%, M2 ${S.cv["M2 Intensity (decomposition)"]}%, M3 ${S.cv["M3 Time-series ARIMAX"]}%`],
    ["No single winner → blend", "Best model changes with the test window, so all three are combined, weighted by accuracy"],
    ["Check after the base year", `Final models use all of FY2007–${BY}. FY${BY + 1} conventional generation came within ${Math.abs(H.val_2025).toFixed(1)}% of NPP actual`]];
  how.forEach((h, i) => {
    const x = 0.5 + i * 3.1;
    card(s, x, 5.05, 2.95, 1.62, i % 2 ? "FFFFFF" : ICE, "how");
    s.addShape(pres.shapes.OVAL, { x: x + 0.15, y: 5.14, w: 0.42, h: 0.42, fill: { color: NAVY }, line: { color: NAVY } });
    txt(s, String(i + 1), { x: x + 0.15, y: 5.14, w: 0.42, h: 0.42, fontSize: 14, bold: true, color: "FFFFFF", align: "center", valign: "middle" });
    txt(s, h[0], { x: x + 0.67, y: 5.12, w: 2.2, h: 0.46, fontSize: 12.5, bold: true, color: NAVY, valign: "middle" });
    txt(s, h[1], { x: x + 0.15, y: 5.66, w: 2.72, h: 0.98, fontSize: 10.5, valign: "top" });
  });
  txt(s, "Source: outputs/backtest_metrics.csv, rolling_cv.csv, model_summary.json, mix_validation.csv", { x: 0.5, y: 6.78, w: 12.3, h: 0.26, fontSize: 9.5, color: MUTED });
  s.addNotes(`M1: 10% more income per person gives about ${(10 * SM["M1 Econometric (per capita)"].beta_lny).toFixed(1)}% more electricity per person. M2: electricity per rupee falls ${Math.abs(100 * SM["M2 Intensity (decomposition)"].c).toFixed(1)}% a year. M3: GDP elasticity ${SM["M3 Time-series ARIMAX"].b_gdp.toFixed(2)}. All three beat a plain trend line by about half. Because the ranking changes between tests, we blend them instead of betting on one.`);

  // ============================================================ 6 Mix + uncertainty
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Method" });
  s.addText("Mix depends on which trend lasts; GDP drives the total", { placeholder: "title" });
  const mr = S.mix_range;
  s.addChart(pres.charts.BAR, [{ name: "Non-fossil share 2047", labels: mr.map(m => m.label), values: mr.map(m => m.nonfossil) }], {
    x: 0.5, y: 1.1, w: 4.15, h: 3.0, barDir: "bar", chartColors: [SKY, SKY, NAVY, "14A39A"], showValue: true, dataLabelPosition: "outEnd",
    dataLabelFormatCode: "0\"%\"", dataLabelFontSize: 11, showLegend: false, valAxisHidden: true, valAxisMaxVal: 65, showTitle: true,
    title: "2047 non-fossil share: which past pattern continues?", ...ax, catAxisLabelFontSize: 10, catAxisOrientation: "maxMin" });
  card(s, 0.5, 4.2, 4.15, 1.0, ICE, "range");
  txt(s, [{ text: "Range from data alone: ", options: { bold: true, color: NAVY } },
    { text: `${Math.round(mr[0].nonfossil)}–${Math.round(mr[3].nonfossil)}% non-fossil. If solar keeps its last-decade pace, coal falls to ${Math.round(mr[3].coal)}%.`, options: {} }],
    { x: 0.65, y: 4.25, w: 3.9, h: 0.9, fontSize: 11, valign: "middle" });
  txt(s, [{ text: "How the mix is built: ", options: { bold: true, color: RED } },
    { text: "total → thermal / hydro / nuclear / renewables (NPP history) → coal vs gas (NPP station data), solar vs wind vs other (CSV installed mix, as %) → 5 regions. Each split uses the method that predicted past years best.", options: {} }],
    { x: 0.5, y: 5.3, w: 4.15, h: 1.35, fontSize: 10.5, valign: "top" });
  const yrs = [String(BY), "2030", "2035", "2040", "2047"];
  s.addChart(pres.charts.BAR, TECHS.map(t => ({ name: t, labels: yrs, values: yrs.map(y => S.nat_pct[y][t]) })), {
    x: 4.8, y: 1.1, w: 4.4, h: 5.55, barDir: "col", barGrouping: "percentStacked", chartColors: TECHS.map(t => TC[t]),
    showLegend: true, legendPos: "b", showTitle: true, title: "Mix over time (% of generation)", valAxisLabelFormatCode: "0%", ...ax });
  const tor = D.tornado.slice().reverse();
  s.addChart(pres.charts.BAR, [{ name: "Lower", labels: tor.map(t => t.i.replace(" (CSV bootstrap P10 / P90)", "").replace(" (-/+1.28 SE)", "").replace(" (P10 / P90)", "").replace(" (single model min / max)", "")), values: tor.map(t => t.lo) },
    { name: "Higher", labels: tor.map(t => t.i.replace(" (CSV bootstrap P10 / P90)", "").replace(" (-/+1.28 SE)", "").replace(" (P10 / P90)", "").replace(" (single model min / max)", "")), values: tor.map(t => t.hi) }], {
    x: 9.35, y: 1.1, w: 3.5, h: 4.05, barDir: "bar", barGrouping: "clustered", barOverlapPct: 100, chartColors: [RED, NAVY], showLegend: true, legendPos: "b",
    showTitle: true, title: "Change in 2047 (TWh)", catAxisLabelPos: "low", ...ax, catAxisLabelFontSize: 9.5 });
  card(s, 9.35, 5.3, 3.5, 1.35, ICE, "uncert");
  txt(s, [{ text: "GDP growth matters most. ", options: { bold: true, color: NAVY } },
    { text: `Its range comes from the CSV's own yearly growth rates (${H.gdp_low.toFixed(1)}–${H.gdp_high.toFixed(1)}%/yr).`, options: {} }],
    { x: 9.5, y: 5.38, w: 3.25, h: 1.2, fontSize: 11, valign: "middle" });
  source(s, "src/mix.py; outputs/mix_model_selection.csv, mix_shares_national.csv, tornado.csv");
  s.addNotes("The mix is built as a tree of shares. Each share is projected by whichever simple method predicted past years best. Solar wins most of the renewable growth because about 95% of recent renewable additions in the CSV are solar. The tornado shows GDP growth moves the 2047 total the most, then the model elasticities.");

  // ============================================================ 7 Limitations & future scope
  pres.addSection({ title: "Next" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Next" });
  s.addText("Limitations and future scope", { placeholder: "title" });
  txt(s, "Limitations", { x: 0.5, y: 1.15, w: 6, h: 0.45, fontSize: 19, bold: true, color: RED });
  txt(s, "Future scope", { x: 6.85, y: 1.15, w: 6, h: 0.45, fontSize: 19, bold: true, color: NAVY });
  const lim = [["Trend, not a plan", "The mix shows where today's trends lead. Policy targets and costs are outside the two datasets, so coal stays high."],
    ["Renewables are one number in NPP", "Solar/wind split uses the CSV's installed mix, treating each MW as producing the same energy."],
    ["No urbanisation data", "Its effect is captured through income per person, not as a separate driver."],
    ["Only 18 years of history", "Limits model complexity; a slowing growth rate as incomes rise cannot yet be measured."],
    ["Outside data would change the answer", "Our test version with outside data and assumptions (hydrogen, EVs, data centres, costs, targets) gave ~6,100–6,300 TWh (+28–34%) and 76% non-fossil. Left out to follow the NPP + CSV rule."]];
  const fut = [["Add hourly data", "Check that the 2047 mix can meet demand hour by hour (storage, peaks)."],
    ["Add cost and policy layers", "With approved cost and target data, turn the trend mix into an optimised plan."],
    ["Source-wise RE data", "Use generation by solar and wind once published, instead of capacity shares."],
    ["Update every year", "Re-run the pipeline as NPP publishes new years; the dashboard refreshes automatically."],
    ["Scenario with outside data", "If allowed, add the outside-data version as a clearly labelled second scenario next to the data-only one."]];
  lim.forEach((l, i) => {
    const y = 1.62 + i * 0.9, last = i === lim.length - 1;
    card(s, 0.5, y, 6.1, 0.83, last ? "FBD5D1" : (i % 2 ? "FFFFFF" : "FDECEA"), "lim");
    s.addImage({ data: ic.warn, x: 0.66, y: y + 0.24, w: 0.34, h: 0.34 });
    txt(s, l[0], { x: 1.17, y: y + 0.05, w: 5.3, h: 0.3, fontSize: 13, bold: true, color: RED });
    txt(s, l[1], { x: 1.17, y: y + 0.34, w: 5.35, h: 0.47, fontSize: last ? 9.5 : 10.5 });
  });
  fut.forEach((l, i) => {
    const y = 1.62 + i * 0.9;
    card(s, 6.85, y, 6.0, 0.83, i % 2 ? "FFFFFF" : ICE, "fut");
    s.addImage({ data: ic.rocket, x: 7.01, y: y + 0.24, w: 0.34, h: 0.34 });
    txt(s, l[0], { x: 7.52, y: y + 0.05, w: 5.2, h: 0.3, fontSize: 13, bold: true, color: NAVY });
    txt(s, l[1], { x: 7.52, y: y + 0.34, w: 5.25, h: 0.47, fontSize: 10.5 });
  });
  card(s, 0.5, 6.18, 12.35, 0.62, NAVY, "links");
  s.addImage({ data: ic.link, x: 0.7, y: 6.3, w: 0.36, h: 0.36 });
  txt(s, "Dashboard: https://india2047-innothon.streamlit.app", { x: 1.2, y: 6.25, w: 5.6, h: 0.48, fontSize: 13, color: "FFFFFF", valign: "middle" });
  s.addImage({ data: ic.github, x: 6.9, y: 6.3, w: 0.36, h: 0.36 });
  txt(s, "GitHub: https://github.com/shivam-hake/innothon-india-2047", { x: 7.4, y: 6.25, w: 5.4, h: 0.48, fontSize: 13, color: "FFFFFF", valign: "middle" });
  s.addNotes("Be upfront: the mix is a trend projection because we used only NPP and the CSV. With outside data and assumptions our test version was about 28-34% higher in 2047 (mostly assumed new loads) and much cleaner (76% non-fossil, from an optimiser using assumed costs and targets). Future work adds hourly checks, cost and policy layers and source-wise renewable data. ");

  const out = path.join(__dirname, "DynamiX_InnoThon2026.pptx");
  await pres.writeFile({ fileName: out });
  if (SKILL) {
    const { applyTheme } = require(path.join(SKILL, "scripts", "apply_theme.js"));
    await applyTheme(out, THEME);
  }
  console.log("[deck] written", out);
})();
