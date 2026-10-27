// Builds Diabetes_Risk_Prediction_System_Presentation.pptx (15 slides, 16:9).
// All numbers come from the project's actual run (artifacts/metrics.json, seed 42).
const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");
const { applyTheme } = require(path.join(process.env.PPTX_SKILL_DIR, "scripts", "apply_theme.js"));

const OUT = path.join(__dirname, "Diabetes_Risk_Prediction_System_Presentation.pptx");
const M = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "artifacts", "metrics.json"), "utf8"));
const T = M.test.metrics, CI = M.test.ci95, CMX = T.confusion_matrix;
const comp = M.model_comparison;
const imp = M.permutation_importance_test;
const prof = M.data_profile;

const NAVY = "10243A", BLUE = "247BA0", TEAL = "20B2AA", WHITE = "FFFFFF", LIGHT = "F3F6F9", AMBER = "F4B942";
const INK = "1C2B30", MUTED = "5A6B75";
const FONT = "Calibri";

const THEME = {
  name: "Healthcare AI",
  headFontFace: FONT, bodyFontFace: FONT,
  colors: { dk1: INK, lt1: WHITE, dk2: NAVY, lt2: LIGHT, accent1: BLUE, accent2: TEAL, accent3: AMBER,
            accent4: "5B8DB8", accent5: "7FD1C7", accent6: "8A979C", hlink: BLUE, folHlink: MUTED },
};

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
pres.theme = { headFontFace: FONT, bodyFontFace: FONT };
pres.title = "Diabetes Risk Prediction System Using Machine Learning and Explainable AI";
pres.subject = "B.Tech CSE (AI & ML) project presentation";

pres.defineSlideMaster({
  title: "CONTENT", background: { color: WHITE },
  objects: [{ text: { text: "Diabetes Risk Prediction System · Educational prototype, not a medical device",
    options: { x: 0.6, y: 7.05, w: 9, h: 0.3, fontFace: FONT, fontSize: 11, color: MUTED, margin: 0, isTextBox: true } } }],
  slideNumber: { x: 12.2, y: 7.05, w: 0.6, h: 0.3, fontFace: FONT, fontSize: 11, color: MUTED, align: "right" },
});
pres.defineSlideMaster({ title: "DARK", background: { color: NAVY } });

async function icon(Comp, color, size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Comp, { color: "#" + color, size: String(size) }));
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}
const shadow = () => ({ type: "outer", color: "000000", opacity: 0.12, blur: 8, offset: 2, angle: 90 });

function title(s, text) {
  s.addText(text, { x: 0.6, y: 0.35, w: 12.1, h: 0.8, fontFace: FONT, fontSize: 32, bold: true, color: NAVY,
    margin: 0, valign: "middle", isTextBox: true });
}
function txt(s, text, x, y, w, h, o = {}) {
  s.addText(text, Object.assign({ x, y, w, h, fontFace: FONT, fontSize: 16, color: INK, margin: 0, valign: "top", isTextBox: true }, o));
}
function card(s, x, y, w, h, fill = LIGHT, o = {}) {
  s.addShape(pres.ShapeType.roundRect, Object.assign({ x, y, w, h, fill: { color: fill }, line: { color: fill, width: 0 },
    rectRadius: 0.12, shadow: shadow() }, o));
}
async function badge(s, Comp, x, y, d, bg, fg = WHITE) {
  s.addShape(pres.ShapeType.ellipse, { x, y, w: d, h: d, fill: { color: bg }, line: { color: bg, width: 0 } });
  const p = d * 0.26;
  s.addImage({ data: await icon(Comp, fg), x: x + p, y: y + p, w: d - 2 * p, h: d - 2 * p });
}
function arrow(s, x, y, w, h, color = BLUE, o = {}) {
  s.addShape(pres.ShapeType.line, Object.assign({ x, y, w, h, line: { color, width: 2, endArrowType: "triangle" } }, o));
}
function box(s, label, x, y, w, h, fill, fg = WHITE, size = 15) {
  s.addShape(pres.ShapeType.roundRect, { x, y, w, h, fill: { color: fill }, line: { color: fill, width: 0 }, rectRadius: 0.1, shadow: shadow() });
  txt(s, label, x + 0.05, y, w - 0.1, h, { align: "center", valign: "middle", bold: true, color: fg, fontSize: size });
}
const H = (t) => ({ text: t, options: { bold: true, color: WHITE, fill: { color: NAVY }, fontSize: 14, fontFace: FONT } });
const C = (t, b) => ({ text: t, options: { fontSize: 14, fontFace: FONT, color: INK, bold: !!b } });
const pct = (v) => (v * 100).toFixed(1) + "%";
const f3 = (v) => v.toFixed(3);

(async () => {
  // ---------- 1. TITLE ----------
  let s = pres.addSlide({ masterName: "DARK" });
  s.addNotes("Good morning. My project is a diabetes risk prediction system that uses machine learning and explainable AI. I want to be clear from the start: this is an educational risk-estimation prototype, not a diagnostic tool. It takes a few health measurements, produces a model-based probability, and shows which inputs influenced that number. Over the next ten to twelve minutes I will walk through the problem, the dataset, the pipeline, the real evaluation results, and the limitations. Everything numerical on these slides comes from experiments I actually ran.");
  txt(s, "B.Tech CSE (AI & ML) · Final-year project", 0.7, 0.7, 7, 0.4, { fontSize: 16, color: TEAL, bold: true });
  txt(s, "Diabetes Risk Prediction System", 0.7, 1.4, 7.4, 1.7, { fontSize: 46, bold: true, color: WHITE, valign: "top" });
  txt(s, "Machine Learning and Explainable AI for Healthcare Risk Estimation", 0.7, 3.2, 6.8, 0.9, { fontSize: 22, color: "CFE3EE" });
  const info = [["Student", "[YOUR NAME]"], ["Registration no.", "[YOUR REGISTRATION NUMBER]"], ["Department", "CSE — Artificial Intelligence and Machine Learning"],
    ["Institution", "[YOUR COLLEGE NAME]"], ["Project guide", "[GUIDE NAME]"], ["Academic year", "[YEAR]"]];
  info.forEach(([k, v], i) => {
    txt(s, k, 0.7, 4.45 + i * 0.4, 2.0, 0.35, { fontSize: 14, color: TEAL, bold: true });
    txt(s, v, 2.7, 4.45 + i * 0.4, 5.6, 0.35, { fontSize: 14, color: WHITE });
  });
  // illustration: data -> model -> risk network
  const cx = 10.3, cy = 3.7;
  s.addShape(pres.ShapeType.ellipse, { x: cx - 2.5, y: cy - 2.5, w: 5, h: 5, fill: { color: "17324F" }, line: { color: BLUE, width: 1.5, dashType: "dash" } });
  s.addShape(pres.ShapeType.ellipse, { x: cx - 1.55, y: cy - 1.55, w: 3.1, h: 3.1, fill: { color: "1B4468" }, line: { color: TEAL, width: 1.5 } });
  const sat = [[fa.FaDatabase, -90, "Health data"], [fa.FaChartLine, 30, "Analytics"], [fa.FaHeartbeat, 150, "Risk estimate"]];
  for (const [Comp, ang, lab] of sat) {
    const r = 2.5, px = cx + r * Math.cos(ang * Math.PI / 180), py = cy + r * Math.sin(ang * Math.PI / 180);
    s.addShape(pres.ShapeType.line, { x: Math.min(cx, px), y: Math.min(cy, py), w: Math.abs(px - cx) || 0.001, h: Math.abs(py - cy) || 0.001,
      flipH: px < cx, flipV: py < cy, line: { color: TEAL, width: 1.5 } });
    await badge(s, Comp, px - 0.5, py - 0.5, 1.0, BLUE);
    const ty = ang === -90 ? py - 1.05 : py + 0.55;
    txt(s, lab, px - 0.75, ty, 1.5, 0.4, { align: "center", fontSize: 14, color: "CFE3EE", bold: true });
  }
  await badge(s, fa.FaBrain, cx - 0.75, cy - 0.75, 1.5, TEAL);

  // ---------- 2. INTRODUCTION ----------
  s = pres.addSlide({ masterName: "CONTENT" });
  title(s, "Introduction: why estimate diabetes risk?");
  s.addNotes("Diabetes is a chronic condition in which the body either cannot produce enough insulin or cannot use it effectively. The WHO reports that the number of people living with diabetes rose from 200 million in 1990 to 830 million in 2022, and that it was the direct cause of 1.6 million deaths in 2021. Those are WHO figures, not mine. Earlier awareness can prompt people to seek proper testing. Machine learning can learn patterns from structured measurements, but a bare probability is hard to trust, which is why I pair every prediction with an explanation of which inputs mattered. Viva tip: be ready to say that this tool estimates risk within one dataset and does not diagnose.");
  card(s, 0.6, 1.4, 5.9, 2.75);
  await badge(s, fa.FaTint, 0.85, 1.6, 0.6, BLUE);
  txt(s, "What is diabetes?", 1.65, 1.62, 4.6, 0.55, { fontSize: 20, bold: true, color: NAVY, valign: "middle" });
  txt(s, [
    { text: "A chronic disease: the pancreas does not make enough insulin, or the body cannot use it effectively (WHO).", options: { bullet: true, breakLine: true } },
    { text: "Earlier awareness can prompt timely testing and follow-up.", options: { bullet: true, breakLine: true } },
    { text: "ML can find patterns in structured health data, but needs transparent output.", options: { bullet: true } },
  ], 0.85, 2.35, 5.45, 1.7, { fontSize: 15, paraSpaceAfter: 4 });
  card(s, 6.8, 1.4, 2.9, 2.75, NAVY);
  txt(s, "830 million", 6.95, 1.75, 2.6, 0.7, { fontSize: 34, bold: true, color: AMBER });
  txt(s, "people living with diabetes worldwide in 2022 (up from 200 million in 1990)", 6.95, 2.55, 2.6, 1.4, { fontSize: 15, color: WHITE });
  card(s, 9.95, 1.4, 2.75, 2.75, NAVY);
  txt(s, "1.6 million", 10.1, 1.75, 2.5, 0.7, { fontSize: 34, bold: true, color: AMBER });
  txt(s, "deaths directly caused by diabetes in 2021", 10.1, 2.55, 2.5, 1.4, { fontSize: 15, color: WHITE });
  const flow = [[fa.FaClipboardList, "Health information", "age, BMI, glucose, …"], [fa.FaBrain, "Machine learning", "trained, validated model"],
    [fa.FaHeartbeat, "Risk estimate", "probability, not a diagnosis"], [fa.FaEye, "Explanation", "which inputs mattered"]];
  for (let i = 0; i < 4; i++) {
    const x = 0.6 + i * 3.08;
    card(s, x, 4.5, 2.7, 1.95, WHITE, { line: { color: "D5E3EA", width: 1 } });
    await badge(s, flow[i][0], x + 0.2, 4.7, 0.65, i === 3 ? TEAL : BLUE);
    txt(s, flow[i][1], x + 1.0, 4.72, 1.65, 0.62, { fontSize: 16, bold: true, color: NAVY, valign: "middle" });
    txt(s, flow[i][2], x + 0.2, 5.55, 2.4, 0.8, { fontSize: 14, color: MUTED });
    if (i < 3) arrow(s, x + 2.72, 5.47, 0.34, 0.001, TEAL);
  }
  txt(s, "Source: World Health Organization, Diabetes fact sheet (page dated 14 Nov 2024). who.int/news-room/fact-sheets/detail/diabetes", 0.6, 6.62, 12, 0.3, { fontSize: 11, color: MUTED });

  // ---------- 3. PROBLEM & OBJECTIVES ----------
  s = pres.addSlide({ masterName: "CONTENT" });
  title(s, "Problem statement and objectives");
  s.addNotes("The problem statement is simple: build an accessible application that estimates diabetes risk from structured inputs and makes its predictions understandable. I broke that into six objectives, and each one maps to a module in the code: data analysis, a reproducible preprocessing pipeline, model comparison, evaluation, explainability and the interactive app. If asked what is novel, the honest answer is the end-to-end rigour: leakage-safe evaluation, calibration, and explanations tied to the actual model output, rather than a new algorithm.");
  card(s, 0.6, 1.4, 4.3, 5.35, NAVY);
  await badge(s, fa.FaBullseye, 0.9, 1.7, 0.75, TEAL);
  txt(s, "Problem", 1.85, 1.75, 2.8, 0.65, { fontSize: 22, bold: true, color: WHITE, valign: "middle" });
  txt(s, "Develop an accessible application that estimates diabetes risk from structured health-related inputs while providing understandable model predictions.", 0.9, 2.7, 3.7, 3.2, { fontSize: 19, color: WHITE });
  txt(s, "Educational use only. Not a diagnostic system.", 0.9, 5.85, 3.7, 0.7, { fontSize: 14, color: AMBER, bold: true });
  const objs = [[fa.FaDatabase, "Analyze a documented diabetes dataset"], [fa.FaCogs, "Build a reproducible preprocessing pipeline"], [fa.FaLayerGroup, "Train and compare ML models"],
    [fa.FaChartBar, "Evaluate with suitable metrics"], [fa.FaEye, "Explain predictions with interpretable methods"], [fa.FaDesktop, "Develop an interactive application"]];
  for (let i = 0; i < 6; i++) {
    const x = 5.2 + (i % 2) * 3.82, y = 1.4 + Math.floor(i / 2) * 1.8;
    card(s, x, y, 3.6, 1.6);
    await badge(s, objs[i][0], x + 0.2, y + 0.3, 0.7, BLUE);
    txt(s, String(i + 1), x + 3.0, y + 0.12, 0.45, 0.4, { fontSize: 14, bold: true, color: TEAL, align: "right" });
    txt(s, objs[i][1], x + 1.05, y + 0.2, 2.4, 1.2, { fontSize: 16, bold: true, color: NAVY, valign: "middle" });
  }

  // ---------- 4. EXISTING VS PROPOSED ----------
  s = pres.addSlide({ masterName: "CONTENT" });
  title(s, "Existing approaches vs. the proposed system");
  s.addNotes("This is a conceptual comparison, not a benchmark. Manual interpretation depends on individual expertise and is hard to standardise. Simple rules use fixed cut-offs and cannot capture interactions between variables. Basic machine learning systems often report one accuracy number and give no explanation. My system adds model comparison, a leakage-safe evaluation, calibration, and per-prediction explanations in an interactive dashboard. It is meant to complement clinical assessment, never replace a doctor or an established test. If asked, say clearly that I make no claim of beating clinical practice.");
  txt(s, "Existing approaches", 0.6, 1.4, 5.6, 0.5, { fontSize: 22, bold: true, color: MUTED });
  const old = [[fa.FaUserMd, "Manual interpretation of indicators", "Depends on individual expertise; hard to standardise"],
    [fa.FaSlidersH, "Simple rule-based assessment", "Fixed cut-offs; ignores interactions between variables"],
    [fa.FaRobot, "Basic ML prediction systems", "Often one accuracy figure; little or no explanation"]];
  for (let i = 0; i < 3; i++) {
    const y = 2.0 + i * 1.5;
    card(s, 0.6, y, 5.6, 1.3);
    await badge(s, old[i][0], 0.85, y + 0.3, 0.7, "8A979C");
    txt(s, old[i][1], 1.8, y + 0.2, 4.2, 0.4, { fontSize: 17, bold: true, color: NAVY });
    txt(s, old[i][2], 1.8, y + 0.65, 4.2, 0.6, { fontSize: 14, color: MUTED });
  }
  arrow(s, 6.35, 3.95, 0.55, 0.001, TEAL);
  card(s, 7.05, 1.4, 5.65, 5.1, NAVY);
  txt(s, "Proposed explainable ML system", 7.35, 1.6, 5.1, 0.5, { fontSize: 22, bold: true, color: WHITE });
  const caps = ["Structured data processing", "Model comparison", "Performance evaluation", "Prediction explanations", "Interactive visualization"];
  for (let i = 0; i < caps.length; i++) {
    const y = 2.3 + i * 0.78;
    await badge(s, fa.FaCheck, 7.35, y, 0.5, TEAL);
    txt(s, caps[i], 8.05, y, 4.4, 0.5, { fontSize: 18, color: WHITE, valign: "middle", bold: true });
  }
  txt(s, "Complements clinical assessment; does not replace doctors or established tests.", 7.35, 5.95, 5.1, 0.45, { fontSize: 14, color: AMBER, bold: true });

  // ---------- 5. ARCHITECTURE ----------
  s = pres.addSlide({ masterName: "CONTENT" });
  title(s, "System architecture");
  s.addNotes("There are two separate flows. The top lane is offline training: I load the dataset, analyse it, train and validate several models, evaluate on held-out data, and save one complete pipeline to disk. The bottom lane is what happens at prediction time: user input is validated, preprocessed by exactly the same saved pipeline, passed to the trained model, and the explainability module explains that same prediction before the dashboard and report are produced. The important point is that the app never retrains at startup; it just loads the saved model. That guarantees training and inference preprocessing are identical.");
  txt(s, "OFFLINE TRAINING  (python -m src.train)", 0.6, 1.35, 8, 0.35, { fontSize: 14, bold: true, color: BLUE });
  const off = ["Dataset", "Data analysis", "Training & validation", "Model evaluation", "Saved model"];
  off.forEach((t, i) => {
    const x = 0.6 + i * 2.5;
    box(s, t, x, 1.75, 2.0, 1.0, i === 4 ? AMBER : BLUE, i === 4 ? NAVY : WHITE, 16);
    if (i < 4) arrow(s, x + 2.02, 2.25, 0.46, 0.001, NAVY);
  });
  arrow(s, 11.6, 2.78, 0.001, 0.8, AMBER, { endArrowType: "none" });
  arrow(s, 6.55, 3.58, 5.05, 0.001, AMBER, { flipH: true, endArrowType: "none" });
  arrow(s, 6.55, 3.58, 0.001, 0.72, AMBER);
  txt(s, "model.joblib: pipeline + metadata, loaded (never retrained) at inference", 7.2, 3.15, 4.3, 0.4, { fontSize: 13, color: NAVY, bold: true, align: "right" });
  txt(s, "PREDICTION-TIME INFERENCE  (app.py)", 0.6, 3.85, 6, 0.35, { fontSize: 14, bold: true, color: TEAL });
  const inf = ["User input", "Input validation", "Data preprocessing", "Trained ML model", "Risk estimate", "Explainability module", "Dashboard & report"];
  inf.forEach((t, i) => {
    const x = 0.6 + i * 1.78;
    box(s, t, x, 4.3, 1.4, 1.15, i === 3 ? AMBER : TEAL, i === 3 ? NAVY : WHITE, 14);
    if (i < 6) arrow(s, x + 1.41, 4.87, 0.36, 0.001, NAVY);
  });
  card(s, 0.6, 5.85, 5.95, 1.0);
  txt(s, [{ text: "Offline: ", options: { bold: true, color: BLUE } }, { text: "slow, run once, uses labelled data, produces the saved pipeline.", options: {} }], 0.8, 5.95, 5.6, 0.8, { fontSize: 15, valign: "middle" });
  card(s, 6.75, 5.85, 5.95, 1.0);
  txt(s, [{ text: "Inference: ", options: { bold: true, color: TEAL } }, { text: "fast, per request, same preprocessing as training, no labels needed.", options: {} }], 6.95, 5.95, 5.6, 0.8, { fontSize: 15, valign: "middle" });

  // ---------- 6. DATASET ----------
  s = pres.addSlide({ masterName: "CONTENT" });
  title(s, "Dataset and features: Pima Indians Diabetes Database");
  s.addNotes("I chose the Pima Indians Diabetes Database from the National Institute of Diabetes and Digestive and Kidney Diseases, donated to UCI in 1990 and mirrored on OpenML. All numbers on this slide were measured by my own profiling script. There are 768 records, eight numeric features, and a binary outcome with about 35 percent positives. Missing values are coded as zero in five columns, which is physiologically impossible for glucose, blood pressure, skin-fold thickness, insulin and BMI. Insulin has 374 zeros and skin-fold 227, so imputed values carry little information. Important caveat: the cohort is adult women of Pima heritage in Arizona, so results may not generalise. The outcome’s timing relative to the recorded features is undocumented, so I describe it as recorded diabetes status. OpenML lists the licence as Public; I verify terms before redistribution.");
  const stats = [["768", "records"], ["8", "numeric features"], ["Outcome", "binary: 1 = diabetes"], [pct(prof.prevalence), `positive (${prof.class_counts["1"]} of ${prof.rows})`], ["0", "duplicate rows"]];
  stats.forEach((st, i) => {
    const x = 0.6 + i * 2.46;
    card(s, x, 1.4, 2.25, 1.35, NAVY);
    txt(s, st[0], x + 0.15, 1.5, 1.95, 0.65, { fontSize: i === 2 ? 22 : 30, bold: true, color: AMBER, valign: "middle" });
    txt(s, st[1], x + 0.15, 2.15, 1.95, 0.5, { fontSize: 14, color: WHITE });
  });
  card(s, 0.6, 3.0, 6.3, 3.75);
  txt(s, "Features by category", 0.85, 3.12, 5.5, 0.4, { fontSize: 18, bold: true, color: NAVY });
  const cats = [["Demographic / reproductive", "Age · Pregnancies", BLUE], ["Body measures", "BMI · Triceps skin-fold", TEAL], ["Metabolic labs", "Glucose (2-h OGTT) · Insulin (2-h)", AMBER],
    ["Cardiovascular", "Diastolic blood pressure", "5B8DB8"], ["Family history", "Diabetes pedigree function", "8A979C"]];
  cats.forEach(([a, b, c], i) => {
    const y = 3.65 + i * 0.6;
    s.addShape(pres.ShapeType.roundRect, { x: 0.85, y, w: 2.55, h: 0.5, fill: { color: c }, line: { color: c, width: 0 }, rectRadius: 0.08 });
    txt(s, a, 0.9, y, 2.45, 0.5, { fontSize: 13, bold: true, color: c === AMBER ? NAVY : WHITE, valign: "middle", align: "center" });
    txt(s, b, 3.55, y, 3.25, 0.5, { fontSize: 14, valign: "middle" });
  });
  card(s, 7.1, 3.0, 5.6, 3.75);
  const z = prof.zeros_treated_as_missing;
  s.addChart(pres.charts.BAR, [{ name: "Zeros treated as missing", labels: ["Insulin", "SkinThickness", "BloodPressure", "BMI", "Glucose"], values: [z.Insulin, z.SkinThickness, z.BloodPressure, z.BMI, z.Glucose] }], {
    x: 7.2, y: 3.05, w: 5.4, h: 3.65, barDir: "bar", chartColors: [BLUE], showTitle: true, title: "Zero values = missing measurements (count of 768)", titleFontSize: 14, titleColor: NAVY, titleFontFace: FONT,
    showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 13, dataLabelColor: INK, dataLabelFontFace: FONT, showLegend: false,
    catAxisLabelFontSize: 13, catAxisLabelColor: INK, catAxisLabelFontFace: FONT, valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" } });
  txt(s, "Source: NIDDK via UCI, mirrored on OpenML id 37 (licence field: Public). Adult females of Pima heritage. Statistics measured by this project.", 0.6, 6.78, 12, 0.25, { fontSize: 11, color: MUTED });

  // ---------- 7. PREPROCESSING ----------
  s = pres.addSlide({ masterName: "CONTENT" });
  title(s, "Data preprocessing pipeline");
  s.addNotes("This is the pipeline exactly as implemented. We validate the schema, then analyse missing data. The key insight is that zero is not always zero: a glucose or BMI of zero is impossible, so I convert those zeros to missing, but zero pregnancies is valid and left alone. There are no duplicate rows and no categorical features, so no encoding is needed. Median imputation and standardisation are inside a scikit-learn Pipeline, which means they are refit inside every cross-validation fold using training data only. That is how we prevent leakage: the test set never influences medians, scaling, hyperparameters, model choice or the decision threshold. I did not use resampling, because with a 35 to 65 split the metrics and an optional class-weight setting were enough, and resampling adds leakage risk.");
  const steps = [["1", "Load & validate schema", "Columns, numeric types, binary target checked"], ["2", "Missing-value analysis", "No NaNs; zeros hide missing values in 5 columns"],
    ["3", "Data cleaning", "Impossible zeros → NaN; 0 duplicate rows"], ["4", "Categorical encoding", "Not needed: all 8 features are numeric"],
    ["5", "Scaling", "Median imputation + standardisation in the pipeline"], ["6", "Split & validation", "Stratified 614 train / 154 test; 5-fold CV on train"],
    ["7", "Resampling", "Not used: avoids extra leakage risk"]];
  steps.forEach((st, i) => {
    const row = i < 4 ? 0 : 1, col = i < 4 ? i : i - 4;
    const w = 2.9, x = 0.6 + col * 3.07, y = 1.4 + row * 1.85;
    card(s, x, y, w, 1.65, i === 3 || i === 6 ? "E4EAEF" : LIGHT);
    s.addShape(pres.ShapeType.ellipse, { x: x + 0.15, y: y + 0.15, w: 0.45, h: 0.45, fill: { color: i === 3 || i === 6 ? "8A979C" : BLUE }, line: { color: WHITE, width: 0 } });
    txt(s, st[0], x + 0.15, y + 0.15, 0.45, 0.45, { align: "center", valign: "middle", bold: true, color: WHITE, fontSize: 14 });
    txt(s, st[1], x + 0.7, y + 0.12, 2.1, 0.55, { fontSize: 15, bold: true, color: NAVY, valign: "middle" });
    txt(s, st[2], x + 0.15, y + 0.78, 2.65, 0.8, { fontSize: 14, color: MUTED });
    if (i !== 3 && i !== 6) arrow(s, x + w + 0.0, y + 0.83, 0.17, 0.001, TEAL);
  });
  card(s, 9.8, 3.25, 2.9, 1.65, NAVY);
  await badge(s, fa.FaShieldAlt, 10.0, 3.45, 0.6, TEAL);
  txt(s, "Fit on training data only", 10.7, 3.4, 1.9, 0.75, { fontSize: 15, bold: true, color: WHITE, valign: "middle" });
  txt(s, "Same saved pipeline at inference", 10.0, 4.2, 2.6, 0.6, { fontSize: 14, color: "CFE3EE" });
  card(s, 0.6, 5.2, 5.95, 1.6, WHITE, { line: { color: AMBER, width: 1.5 } });
  txt(s, "Why zero ≠ missing", 0.85, 5.3, 5.5, 0.4, { fontSize: 17, bold: true, color: NAVY });
  txt(s, "Glucose, BP, skin-fold, insulin and BMI cannot truly be 0, so 0 means “not measured”. Pregnancies = 0 is valid and is kept.", 0.85, 5.72, 5.5, 1.0, { fontSize: 14 });
  card(s, 6.75, 5.2, 5.95, 1.6, WHITE, { line: { color: TEAL, width: 1.5 } });
  txt(s, "How leakage is prevented", 7.0, 5.3, 5.5, 0.4, { fontSize: 17, bold: true, color: NAVY });
  txt(s, "Medians and scaling are re-fit inside each CV fold. The test split never influences tuning, selection or the threshold.", 7.0, 5.72, 5.5, 1.0, { fontSize: 14 });

  // ---------- 8. ALGORITHMS ----------
  s = pres.addSlide({ masterName: "CONTENT" });
  title(s, "Candidate machine learning algorithms");
  s.addNotes("I compared a majority-class baseline plus six algorithms under one identical protocol. Logistic regression is linear and very interpretable. A decision tree gives readable rules but is unstable. Random forest and gradient boosting are ensembles that capture non-linear interactions at the cost of transparency. An SVM with an RBF kernel gives flexible boundaries but is harder to interpret and needs calibration for probabilities. Histogram gradient boosting is a fast boosting variant. Selection was not by accuracy alone: I used cross-validated ROC-AUC, then preferred the simplest model within one standard error, and checked calibration. The outcome is on the results slide; I deliberately did not pick a winner in advance.");
  const algos = [
    [fa.FaChartLine, "Logistic Regression", "Interpretable linear baseline", "Readable coefficients; stable", "Linear boundary only", 5],
    [fa.FaSitemap, "Decision Tree", "Rule-like, transparent splits", "Easy to visualise", "High variance; overfits", 4],
    [fa.FaTree || fa.FaLayerGroup, "Random Forest", "Bagged ensemble of trees", "Non-linear and robust", "Harder to interpret", 2],
    [fa.FaRocket || fa.FaCogs, "Gradient Boosting", "Sequential ensemble", "Strong on tabular data", "Sensitive to tuning", 2],
    [fa.FaProjectDiagram || fa.FaSitemap, "SVM (RBF)", "Kernel margin classifier", "Flexible decision boundary", "Opaque; needs calibration", 1],
    [fa.FaBolt || fa.FaCogs, "HistGradientBoosting", "Fast boosting variant", "Efficient; handles NaN", "Complex for small data", 2]];
  for (let i = 0; i < 6; i++) {
    const [Ic, name, role, plus, minus, interp] = algos[i];
    const x = 0.6 + (i % 3) * 4.1, y = 1.35 + Math.floor(i / 3) * 2.3;
    card(s, x, y, 3.9, 2.15);
    await badge(s, Ic, x + 0.2, y + 0.18, 0.6, i === 0 ? TEAL : BLUE);
    txt(s, name, x + 0.95, y + 0.18, 1.95, 0.6, { fontSize: 16, bold: true, color: NAVY, valign: "middle" });
    for (let d = 0; d < 5; d++)
      s.addShape(pres.ShapeType.ellipse, { x: x + 3.0 + d * 0.16, y: y + 0.4, w: 0.12, h: 0.12, fill: { color: d < interp ? TEAL : "C9D6DD" }, line: { color: WHITE, width: 0 } });
    txt(s, role, x + 0.25, y + 0.92, 3.45, 0.35, { fontSize: 14, color: MUTED });
    txt(s, [{ text: "+  ", options: { bold: true, color: "168F88" } }, { text: plus, options: {} }], x + 0.25, y + 1.3, 3.45, 0.35, { fontSize: 14 });
    txt(s, [{ text: "–  ", options: { bold: true, color: "B7791F" } }, { text: minus, options: {} }], x + 0.25, y + 1.68, 3.45, 0.35, { fontSize: 14 });
  }
  card(s, 0.6, 5.95, 12.1, 0.95, NAVY);
  await badge(s, fa.FaBalanceScale, 0.85, 6.1, 0.65, TEAL);
  txt(s, [{ text: "Final choice is made by experiment, not by name: ", options: { bold: true, color: AMBER } }, { text: "cross-validated performance, calibration, interpretability and fit to the intended use. A majority-class baseline is also included. Dots = interpretability (qualitative rating).", options: { color: WHITE } }], 1.7, 5.98, 10.8, 0.9, { fontSize: 14, valign: "middle" });

  // ---------- 9. TRAINING & VALIDATION ----------
  s = pres.addSlide({ masterName: "CONTENT" });
  title(s, "Model training and validation");
  s.addNotes("Here is the exact protocol. I split the data once, stratified and with a fixed seed: 614 rows for training and 154 held out. All tuning and model selection happens inside the training set using stratified five-fold cross-validation; in each round one fold acts as the validation set. After choosing a model, I fit it on all training data with sigmoid calibration, kept only because it lowered the out-of-fold Brier score, and I chose the decision threshold from out-of-fold training predictions so that sensitivity was at least 0.8. Only then did I score the test set, once, for the final model only. Running the pipeline twice gave identical results. The saved artifact bundles the preprocessing and model together.");
  const tw = 7.4, trw = tw * 0.8;
  s.addShape(pres.ShapeType.roundRect, { x: 0.6, y: 1.4, w: trw, h: 0.7, fill: { color: BLUE }, line: { color: BLUE, width: 0 }, rectRadius: 0.08 });
  txt(s, "Training split: 614 rows (80%)", 0.6, 1.4, trw, 0.7, { align: "center", valign: "middle", bold: true, color: WHITE, fontSize: 16 });
  s.addShape(pres.ShapeType.roundRect, { x: 0.6 + trw + 0.05, y: 1.4, w: tw - trw - 0.05, h: 0.7, fill: { color: AMBER }, line: { color: AMBER, width: 0 }, rectRadius: 0.08 });
  txt(s, "Test: 154", 0.6 + trw + 0.05, 1.4, tw - trw - 0.05, 0.7, { align: "center", valign: "middle", bold: true, color: NAVY, fontSize: 15 });
  txt(s, "5-fold stratified CV: tune + select (validation = held-out fold)", 0.6, 2.3, trw, 0.4, { fontSize: 14, bold: true, color: BLUE });
  for (let i = 0; i < 5; i++) {
    const w = (trw - 0.4) / 5, x = 0.6 + i * (w + 0.1);
    s.addShape(pres.ShapeType.roundRect, { x, y: 2.75, w, h: 0.6, fill: { color: LIGHT }, line: { color: "D5E3EA", width: 1 }, rectRadius: 0.06 });
    s.addShape(pres.ShapeType.roundRect, { x: x + i * (w / 5), y: 2.75, w: w / 5, h: 0.6, fill: { color: TEAL }, line: { color: TEAL, width: 0 }, rectRadius: 0.03 });
    txt(s, `Fold ${i + 1}`, x, 3.38, w, 0.3, { fontSize: 12, color: MUTED, align: "center" });
  }
  txt(s, "teal = validation fold", 0.6, 3.7, 3, 0.3, { fontSize: 12, color: MUTED });
  arrow(s, 0.6 + trw / 2, 3.98, 0.001, 0.45, NAVY);
  box(s, "Fit final model on all 614 · sigmoid calibration · threshold from out-of-fold predictions", 0.6, 4.45, trw, 1.0, BLUE, WHITE, 15);
  arrow(s, 0.6 + trw + 0.05 + (tw - trw) / 2, 2.12, 0.001, 2.33, AMBER, { endArrowType: "none" });
  box(s, "Scored once: metrics + 95% bootstrap CI", 0.6 + trw + 0.05 - 0.15, 4.45, 1.85, 1.0, AMBER, NAVY, 13);
  arrow(s, 0.6 + trw / 2, 5.47, 0.001, 0.4, NAVY);
  box(s, "Saved: model.joblib (pipeline + metadata, fixed seed)", 0.6, 5.9, tw, 0.8, NAVY, WHITE, 15);
  card(s, 8.4, 1.4, 4.3, 5.3, NAVY);
  txt(s, "Safeguards", 8.7, 1.55, 3.8, 0.45, { fontSize: 22, bold: true, color: WHITE });
  const sg = ["Stratified split, fixed seed 42", "Preprocessing fit per fold", "Selection and threshold use training data only", "Test set scored once, final model only", "Calibration kept only if Brier improves", "Reruns give identical results"];
  for (let i = 0; i < sg.length; i++) {
    const y = 2.2 + i * 0.72;
    await badge(s, fa.FaCheck, 8.7, y + 0.05, 0.4, TEAL);
    txt(s, sg[i], 9.25, y, 3.3, 0.6, { fontSize: 15, color: WHITE, valign: "middle" });
  }

  // ---------- 10. EVALUATION ----------
  s = pres.addSlide({ masterName: "CONTENT" });
  title(s, "Model evaluation (held-out test set, n = 154)");
  s.addNotes("These are real held-out test results for the final calibrated logistic regression, at a threshold of about 0.29 chosen on training data. Sensitivity is 0.81 with 44 true positives and 10 false negatives; specificity is 0.67 with 33 false positives. For a screening-style tool I favour sensitivity because a missed case is costlier than an extra follow-up, but that is exactly why precision is only 0.57: roughly four in ten positive flags are false alarms. The confidence intervals are wide because the test set is small; for example ROC-AUC could plausibly be anywhere from about 0.74 to 0.87. The Brier score and calibration curve tell us whether the probabilities themselves can be trusted, which matters more than accuracy for a risk estimate. None of this is clinical validation.");
  const ci = (k) => `95% CI ${CI[k][0].toFixed(2)}–${CI[k][1].toFixed(2)}`;
  // confusion matrix
  card(s, 0.6, 1.4, 4.6, 3.85);
  txt(s, "Confusion matrix", 0.85, 1.5, 4.1, 0.4, { fontSize: 18, bold: true, color: NAVY });
  txt(s, "Predicted neg", 1.6, 1.98, 1.5, 0.3, { fontSize: 12, color: MUTED, align: "center" });
  txt(s, "Predicted pos", 3.2, 1.98, 1.5, 0.3, { fontSize: 12, color: MUTED, align: "center" });
  const cmv = [[CMX.tn, CMX.fp], [CMX.fn, CMX.tp]], cml = [["True neg", "False pos"], ["False neg", "True pos"]], cmc = [[TEAL, AMBER], [AMBER, BLUE]];
  ["Actual\nneg", "Actual\npos"].forEach((t, r) => txt(s, t, 0.75, 2.35 + r * 1.4, 0.8, 1.3, { fontSize: 12, color: MUTED, align: "center", valign: "middle" }));
  for (let r = 0; r < 2; r++) for (let c = 0; c < 2; c++) {
    const x = 1.6 + c * 1.6, y = 2.35 + r * 1.4, dark = cmc[r][c] === AMBER;
    s.addShape(pres.ShapeType.roundRect, { x, y, w: 1.5, h: 1.3, fill: { color: cmc[r][c] }, line: { color: cmc[r][c], width: 0 }, rectRadius: 0.08 });
    txt(s, String(cmv[r][c]), x, y + 0.1, 1.5, 0.7, { align: "center", valign: "middle", bold: true, fontSize: 32, color: dark ? NAVY : WHITE });
    txt(s, cml[r][c], x, y + 0.82, 1.5, 0.35, { align: "center", fontSize: 13, bold: true, color: dark ? NAVY : WHITE });
  }
  // key metrics
  const key = [["Sensitivity", T.recall_sensitivity, "recall_sensitivity"], ["Specificity", T.specificity, "specificity"], ["ROC-AUC", T.roc_auc, "roc_auc"], ["Precision", T.precision, "precision"]];
  key.forEach(([n, v, k], i) => {
    const x = 5.4 + i * 1.85;
    card(s, x, 1.4, 1.75, 1.85, NAVY);
    txt(s, n, x + 0.1, 1.5, 1.55, 0.35, { fontSize: 14, bold: true, color: "CFE3EE", align: "center" });
    txt(s, v.toFixed(2), x + 0.1, 1.9, 1.55, 0.75, { fontSize: 34, bold: true, color: AMBER, align: "center", valign: "middle" });
    txt(s, ci(k), x + 0.1, 2.7, 1.55, 0.45, { fontSize: 12, color: WHITE, align: "center" });
  });
  const sec = [["PR-AUC", T.pr_auc, "pr_auc"], ["F1-score", T.f1, "f1"], ["Accuracy", T.accuracy, "accuracy"], ["Brier score", T.brier, "brier"]];
  sec.forEach(([n, v, k], i) => {
    const x = 5.4 + i * 1.85;
    card(s, x, 3.4, 1.75, 1.85, LIGHT);
    txt(s, n, x + 0.1, 3.5, 1.55, 0.35, { fontSize: 14, bold: true, color: NAVY, align: "center" });
    txt(s, v.toFixed(2), x + 0.1, 3.9, 1.55, 0.75, { fontSize: 28, bold: true, color: BLUE, align: "center", valign: "middle" });
    txt(s, ci(k), x + 0.1, 4.7, 1.55, 0.45, { fontSize: 12, color: MUTED, align: "center" });
  });
  // why these metrics
  card(s, 0.6, 5.45, 12.1, 1.2, WHITE, { line: { color: "D5E3EA", width: 1 } });
  const why = [[fa.FaSearch, "Sensitivity: missed cases (false negatives) cost more than extra follow-up."], [fa.FaExclamationTriangle, `Precision: ${CMX.fp} false alarms mean about 4 in 10 positive flags are wrong.`], [fa.FaBalanceScale, "Brier + calibration: can the probabilities be trusted?"]];
  for (let i = 0; i < 3; i++) {
    const x = 0.8 + i * 4.0;
    await badge(s, why[i][0], x, 5.78, 0.55, i === 1 ? AMBER : TEAL, i === 1 ? NAVY : WHITE);
    txt(s, why[i][1], x + 0.7, 5.55, 3.1, 1.0, { fontSize: 14, valign: "middle" });
  }
  txt(s, `Threshold ${T.threshold.toFixed(2)} chosen on training data (sensitivity ≥ 0.80). Bootstrap CIs, 1000 resamples; small test set gives wide intervals.`, 0.6, 6.7, 12.1, 0.3, { fontSize: 12, color: MUTED });

  // ---------- 11. EXPLAINABLE AI ----------
  s = pres.addSlide({ masterName: "CONTENT" });
  title(s, "Explainable AI: understanding individual predictions");
  s.addNotes("I use two kinds of explanation. Globally, permutation importance on the test set shows how much ROC-AUC drops when a feature is shuffled: glucose dominates by a wide margin, BMI and pregnancies are small contributors, and insulin, blood pressure and skin-fold thickness contribute essentially nothing. Locally, for each prediction the app runs SHAP's permutation explainer on the complete pipeline, so the contributions add up exactly to the predicted probability; I have a unit test for that additivity. The panel on the right is the app's output for its default demo inputs, not a real patient. Key viva point: these explanations show how the model uses inputs, which is association, not causation, and correlated features can share or distort importance.");
  card(s, 0.6, 1.4, 6.3, 3.9);
  const order = Object.keys(imp).sort((a, b) => imp[b].mean - imp[a].mean);
  s.addChart(pres.charts.BAR, [{ name: "Drop in ROC-AUC", labels: order.slice().reverse(), values: order.slice().reverse().map((k) => +imp[k].mean.toFixed(4)) }], {
    x: 0.7, y: 1.45, w: 6.1, h: 3.8, barDir: "bar", chartColors: [BLUE], showTitle: true, title: "Global: permutation importance (held-out test)", titleFontSize: 14, titleColor: NAVY, titleFontFace: FONT,
    showValue: true, dataLabelFormatCode: "0.000", dataLabelFontSize: 12, dataLabelColor: INK, dataLabelFontFace: FONT, dataLabelPosition: "outEnd", showLegend: false,
    catAxisLabelFontSize: 12, catAxisLabelColor: INK, catAxisLabelFontFace: FONT, valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" } });
  card(s, 7.1, 1.4, 5.6, 3.9, WHITE, { line: { color: AMBER, width: 1.5 } });
  txt(s, "Local: SHAP on one prediction", 7.35, 1.5, 5.1, 0.4, { fontSize: 18, bold: true, color: NAVY });
  txt(s, "ILLUSTRATIVE: app's default demo inputs, not a real patient. Values approximate, in probability points.", 7.35, 1.92, 5.1, 0.6, { fontSize: 12, color: "9A6A00", bold: true });
  const ex = [["Glucose", -8], ["BMI", -8], ["Pregnancies", -5]];
  ex.forEach(([n, v], i) => {
    const y = 2.7 + i * 0.72, w = Math.abs(v) * 0.32;
    txt(s, n, 7.35, y, 1.5, 0.5, { fontSize: 15, valign: "middle", bold: true });
    s.addShape(pres.ShapeType.roundRect, { x: 8.9, y, w, h: 0.5, fill: { color: TEAL }, line: { color: TEAL, width: 0 }, rectRadius: 0.05 });
    txt(s, `≈ −${Math.abs(v)} pts`, 8.9 + w + 0.1, y, 1.5, 0.5, { fontSize: 14, valign: "middle", color: INK });
  });
  txt(s, "Negative = lowers the estimate. Contributions + baseline = predicted probability.", 7.35, 4.8, 5.1, 0.45, { fontSize: 13, color: MUTED });
  const cav = [[fa.FaBalanceScale, "Association ≠ causation", "Shows how the model used inputs, not what causes diabetes"], [fa.FaProjectDiagram || fa.FaSitemap, "Correlated features", "Importance can be shared or unstable"], [fa.FaExclamationTriangle, "Only as good as the model", "A weak or biased model gives misleading explanations"]];
  for (let i = 0; i < 3; i++) {
    const x = 0.6 + i * 4.1;
    card(s, x, 5.5, 3.9, 1.35, NAVY);
    await badge(s, cav[i][0], x + 0.15, 5.7, 0.55, TEAL);
    txt(s, cav[i][1], x + 0.85, 5.6, 2.95, 0.4, { fontSize: 15, bold: true, color: AMBER });
    txt(s, cav[i][2], x + 0.85, 6.02, 2.95, 0.8, { fontSize: 13, color: WHITE });
  }

  // ---------- 12. UI ----------
  s = pres.addSlide({ masterName: "CONTENT" });
  title(s, "Application user interface and workflow");
  s.addNotes("The app is built with Streamlit and Plotly, with scikit-learn for modelling, SHAP for explanations, joblib for the saved model and ReportLab for PDF reports. The workflow is: open the dashboard, enter inputs, validate them, request a prediction, read the probability, review the explanation, and download a PDF or CSV report. Validation rejects out-of-range or non-numeric values with plain-language messages and never turns a blank into zero. The picture on the right is a conceptual wireframe of the implemented layout, clearly labelled as a mockup. I will demo the real application live. Privacy: no identifiers are asked, history is kept only in the session, and nothing is sent to third parties.");
  const wf = ["Open the dashboard", "Enter supported inputs", "Validate the information", "Request a prediction", "View the model output", "Review the explanation", "Export a report (PDF / CSV)"];
  for (let i = 0; i < 7; i++) {
    const y = 1.4 + i * 0.64;
    s.addShape(pres.ShapeType.ellipse, { x: 0.6, y, w: 0.46, h: 0.46, fill: { color: i === 6 ? TEAL : BLUE }, line: { color: WHITE, width: 0 } });
    txt(s, String(i + 1), 0.6, y, 0.46, 0.46, { align: "center", valign: "middle", bold: true, color: WHITE, fontSize: 14 });
    txt(s, wf[i], 1.25, y, 3.9, 0.46, { fontSize: 16, valign: "middle", bold: true, color: NAVY });
  }
  const tech = ["Python", "Streamlit", "scikit-learn", "Plotly", "joblib", "SHAP", "ReportLab"];
  tech.forEach((t, i) => {
    const x = 0.6 + (i % 3) * 1.55, y = 6.0 + Math.floor(i / 3) * 0.48;
    s.addShape(pres.ShapeType.roundRect, { x, y, w: 1.45, h: 0.4, fill: { color: LIGHT }, line: { color: BLUE, width: 1 }, rectRadius: 0.2 });
    txt(s, t, x, y, 1.45, 0.4, { align: "center", valign: "middle", fontSize: 13, bold: true, color: BLUE });
  });
  // wireframe
  s.addShape(pres.ShapeType.roundRect, { x: 5.5, y: 1.4, w: 7.2, h: 5.3, fill: { color: WHITE }, line: { color: "B8C7D1", width: 1.5 }, rectRadius: 0.1, shadow: shadow() });
  s.addShape(pres.ShapeType.rect, { x: 5.5, y: 1.4, w: 7.2, h: 0.4, fill: { color: "E4EAEF" }, line: { color: "E4EAEF", width: 0 } });
  txt(s, "MOCKUP · conceptual wireframe, not a screenshot", 5.7, 1.4, 6.8, 0.4, { fontSize: 12, bold: true, color: "9A6A00", valign: "middle" });
  s.addShape(pres.ShapeType.rect, { x: 5.5, y: 1.8, w: 1.7, h: 4.9, fill: { color: LIGHT }, line: { color: LIGHT, width: 0 } });
  ["Home", "Risk Estimation", "Model Insights", "Session History", "About"].forEach((n, i) => txt(s, n, 5.62, 2.0 + i * 0.45, 1.55, 0.35, { fontSize: 12, bold: i === 1, color: i === 1 ? BLUE : MUTED }));
  s.addShape(pres.ShapeType.rect, { x: 7.4, y: 1.95, w: 5.15, h: 0.5, fill: { color: "FFF6E0" }, line: { color: AMBER, width: 1 } });
  txt(s, "Educational tool, not a diagnosis", 7.5, 1.95, 5, 0.5, { fontSize: 12, color: "4A3200", valign: "middle", bold: true });
  ["Pregnancies", "Glucose", "BMI", "Age"].forEach((n, i) => {
    const x = 7.4 + (i % 2) * 2.65, y = 2.65 + Math.floor(i / 2) * 0.75;
    txt(s, n, x, y, 2.4, 0.25, { fontSize: 11, color: MUTED });
    s.addShape(pres.ShapeType.roundRect, { x, y: y + 0.27, w: 2.4, h: 0.35, fill: { color: LIGHT }, line: { color: "D5E3EA", width: 1 }, rectRadius: 0.05 });
  });
  s.addShape(pres.ShapeType.roundRect, { x: 7.4, y: 4.2, w: 1.5, h: 0.42, fill: { color: BLUE }, line: { color: BLUE, width: 0 }, rectRadius: 0.06 });
  txt(s, "Estimate", 7.4, 4.2, 1.5, 0.42, { align: "center", valign: "middle", bold: true, color: WHITE, fontSize: 13 });
  s.addShape(pres.ShapeType.roundRect, { x: 7.4, y: 4.85, w: 1.9, h: 1.65, fill: { color: LIGHT }, line: { color: "D5E3EA", width: 1 }, rectRadius: 0.08 });
  txt(s, "Model-estimated\nprobability\n[ xx% ]", 7.45, 4.9, 1.8, 1.5, { fontSize: 12, align: "center", valign: "middle", color: NAVY, bold: true });
  [0.55, 0.9, 0.35].forEach((w, i) => s.addShape(pres.ShapeType.rect, { x: 9.5, y: 5.0 + i * 0.5, w: w * 2.6, h: 0.3, fill: { color: i === 1 ? AMBER : TEAL }, line: { color: WHITE, width: 0 } }));
  txt(s, "Feature contributions (placeholder bars)", 9.5, 6.45, 3.1, 0.3, { fontSize: 11, color: MUTED });

  // ---------- 13. RESULTS ----------
  s = pres.addSlide({ masterName: "CONTENT" });
  title(s, "Results and discussion");
  s.addNotes("These are actual experiment results. On cross-validation, logistic regression, SVM and random forest are statistically indistinguishable, around 0.84 ROC-AUC, so I chose logistic regression as the simplest. On the held-out test set it reached an ROC-AUC of 0.81 with a 95 percent interval of about 0.74 to 0.87, comparable to the 76 percent sensitivity and specificity reported in the original 1988 paper on a different split. The main error pattern is false positives: 33 of 100 negatives were flagged because the threshold favours sensitivity. Calibration helped: out-of-fold Brier score improved from 0.160 to 0.151. The most important discussion point is that predictive performance is not clinical usefulness: glucose is the strongest single predictor, but a training-only ablation shows the other features still carry signal, with ROC-AUC 0.768 without glucose and 0.845 with all eight, and the timing of the outcome relative to the features is not documented. No external validation has been done.");
  card(s, 0.6, 1.4, 6.2, 5.35);
  const cmp = comp.filter((r) => true).slice().sort((a, b) => a.cv_roc_auc - b.cv_roc_auc);
  s.addChart(pres.charts.BAR, [{ name: "CV ROC-AUC", labels: cmp.map((r) => r.model.replace(" (majority class)", "").replace("HistGradientBoosting", "HistGB")), values: cmp.map((r) => +r.cv_roc_auc.toFixed(3)) }], {
    x: 0.7, y: 1.45, w: 6.0, h: 5.25, barDir: "bar", chartColors: [BLUE], showTitle: true, title: "5-fold CV ROC-AUC on training data", titleFontSize: 14, titleColor: NAVY, titleFontFace: FONT,
    showValue: true, dataLabelFormatCode: "0.000", dataLabelFontSize: 12, dataLabelColor: INK, dataLabelFontFace: FONT, dataLabelPosition: "outEnd", showLegend: false,
    catAxisLabelFontSize: 12, catAxisLabelColor: INK, catAxisLabelFontFace: FONT, valAxisMinVal: 0.4, valAxisMaxVal: 0.95, valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" } });
  const kp = [[T.roc_auc.toFixed(2), "Test ROC-AUC"], [Math.round(T.recall_sensitivity * 100) + "%", "Sensitivity"], [Math.round(T.specificity * 100) + "%", "Specificity"], [T.brier.toFixed(2), "Test Brier score"]];
  kp.forEach(([v, l], i) => {
    const x = 7.05 + (i % 2) * 2.9, y = 1.4 + Math.floor(i / 2) * 1.2;
    card(s, x, y, 2.75, 1.05, NAVY);
    txt(s, v, x + 0.15, y + 0.05, 1.3, 0.95, { fontSize: 30, bold: true, color: AMBER, valign: "middle" });
    txt(s, l, x + 1.45, y + 0.05, 1.25, 0.95, { fontSize: 13, color: WHITE, valign: "middle" });
  });
  txt(s, [
    { text: "Selected: logistic regression. CV AUC of top models within noise, simplest chosen.", options: { bullet: true, breakLine: true } },
    { text: `Errors: ${CMX.fp} false positives, ${CMX.fn} false negatives (threshold favours sensitivity).`, options: { bullet: true, breakLine: true } },
    { text: "Calibration: sigmoid kept; out-of-fold Brier 0.160 → 0.151.", options: { bullet: true, breakLine: true } },
    { text: "Glucose is the strongest predictor; the other features still add signal.", options: { bullet: true, breakLine: true } },
    { text: "Predictive performance ≠ clinical usefulness. No external validation.", options: { bullet: true, bold: true } }], 7.05, 3.95, 5.65, 2.8, { fontSize: 14, paraSpaceAfter: 4 });

  // ---------- 14. LIMITATIONS & FUTURE ----------
  s = pres.addSlide({ masterName: "CONTENT" });
  title(s, "Limitations and future scope");
  s.addNotes("Be upfront about limitations. The data is 768 rows from one 1990s study of adult women of Pima heritage, so it is not representative and may carry demographic bias. Five measurements use zero for missing, and imputation loses information. Any threshold trades false negatives against false positives; mine gives about 4 in 10 false alarms. There is no clinical validation and no external validation. Future work: validate on external and more representative datasets such as national health surveys with appropriate survey handling, run subgroup fairness evaluation, improve calibration monitoring and explanations, deploy securely, and only consider clinical workflow integration after proper review. On privacy: no identifiers are requested, nothing leaves the app, history is session-only, and I make no regulatory-compliance claim.");
  card(s, 0.6, 1.4, 5.95, 4.35);
  await badge(s, fa.FaExclamationTriangle, 0.85, 1.6, 0.6, AMBER, NAVY);
  txt(s, "Limitations", 1.65, 1.62, 4, 0.55, { fontSize: 22, bold: true, color: NAVY, valign: "middle" });
  txt(s, ["Small, old, single-population dataset (768 rows)", "Possible demographic bias; may not generalise", "Zeros hide missing or noisy measurements", "False positives and false negatives remain", "Outcome timing undocumented; glucose strongest", "No external or clinical validation"].map((t, i, a) => ({ text: t, options: { bullet: true, breakLine: i < a.length - 1 } })), 0.85, 2.4, 5.5, 3.3, { fontSize: 16, paraSpaceAfter: 6 });
  card(s, 6.75, 1.4, 5.95, 4.35, NAVY);
  await badge(s, fa.FaRocket || fa.FaFlask, 7.0, 1.6, 0.6, TEAL);
  txt(s, "Future scope", 7.8, 1.62, 4, 0.55, { fontSize: 22, bold: true, color: WHITE, valign: "middle" });
  txt(s, ["External validation on larger, representative data", "Ongoing calibration checks", "Fairness evaluation across subgroups", "Improved explainability", "Secure cloud deployment", "Clinical workflow integration, only after review"].map((t, i, a) => ({ text: t, options: { bullet: true, breakLine: i < a.length - 1 } })), 7.0, 2.4, 5.5, 3.3, { fontSize: 16, color: WHITE, paraSpaceAfter: 6 });
  card(s, 0.6, 5.95, 12.1, 0.9, WHITE, { line: { color: TEAL, width: 1.5 } });
  await badge(s, fa.FaLock, 0.85, 6.1, 0.6, TEAL);
  txt(s, [{ text: "Privacy and responsible use: ", options: { bold: true, color: NAVY } }, { text: "no identifiers collected, no third-party transfer, session-only history; educational use only; no compliance claims.", options: {} }], 1.7, 5.95, 10.8, 0.9, { fontSize: 15, valign: "middle" });

  // ---------- 15. CONCLUSION ----------
  s = pres.addSlide({ masterName: "DARK" });
  s.addNotes("To conclude: I addressed the problem of estimating diabetes risk from structured data in a way that is transparent. The approach is a reproducible scikit-learn pipeline, multiple models compared under one protocol, a calibrated logistic regression, and SHAP explanations tied to the real prediction. The evaluation strategy avoided leakage and reports confidence intervals. The honest result is moderate: about 0.81 ROC-AUC, and glucose does most of the work. The tool must be used responsibly and needs external validation before any real-world use. References are listed on this slide; all statistics and citations were checked against their sources. Thank you, I am happy to take questions.");
  txt(s, "Conclusion", 0.7, 0.5, 6, 0.6, { fontSize: 30, bold: true, color: WHITE });
  const sm = [["Problem", "Estimate diabetes risk transparently from structured data"], ["Approach", "Reproducible pipeline, 7 models compared, calibrated logistic regression"], ["Explainability", "SHAP + permutation importance tied to the real prediction"],
    ["Evaluation", `Leakage-safe CV; held-out test ROC-AUC ${T.roc_auc.toFixed(2)} (95% CI ${CI.roc_auc[0].toFixed(2)}–${CI.roc_auc[1].toFixed(2)})`], ["Responsible use", "Educational only; needs external and clinical validation"]];
  sm.forEach(([k, v], i) => {
    const y = 1.3 + i * 0.82;
    txt(s, k, 0.7, y, 1.9, 0.7, { fontSize: 15, bold: true, color: TEAL, valign: "middle" });
    txt(s, v, 2.6, y, 5.3, 0.7, { fontSize: 15, color: WHITE, valign: "middle" });
  });
  txt(s, "THANK YOU", 8.5, 1.5, 4.3, 0.9, { fontSize: 44, bold: true, color: WHITE, align: "left" });
  txt(s, "Questions & Discussion", 8.5, 2.5, 4.3, 0.6, { fontSize: 24, color: AMBER, bold: true });
  await badge(s, fa.FaHeartbeat, 8.5, 3.4, 0.9, BLUE);
  txt(s, "References", 0.7, 5.4, 4, 0.3, { fontSize: 12, bold: true, color: TEAL });
  txt(s, [
    "World Health Organization. Diabetes fact sheet. who.int/news-room/fact-sheets/detail/diabetes",
    "Smith JW et al. (1988). Using the ADAP learning algorithm to forecast the onset of diabetes mellitus. Proc. Symp. Computer Applications in Medical Care, 261–265. Data: archive.ics.uci.edu/ml/datasets/pima+indians+diabetes; openml.org/d/37",
    "Pedregosa F et al. (2011). Scikit-learn: Machine Learning in Python. JMLR 12:2825–2830. scikit-learn.org/stable",
    "Lundberg SM, Lee S-I (2017). A unified approach to interpreting model predictions. NeurIPS 30. shap.readthedocs.io"].map((t, i, a) => ({ text: t, options: { breakLine: i < a.length - 1 } })), 0.7, 5.72, 11.9, 1.55, { fontSize: 10.5, color: "B8CBD8", paraSpaceAfter: 2 });

  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
