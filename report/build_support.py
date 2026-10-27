"""Builds the supporting pack: evidence checklist, open items, viva sheet, compliance matrix."""
from __future__ import annotations

import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from lxml import etree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import content as C  # noqa: E402
import docx_engine as E  # noqa: E402

TEMPLATE = HERE / "template" / "E-report template.docx"
OUT = HERE / "output" / "E-Report_Supporting_Pack.docx"
SOFFICE = r"C:\Program Files\LibreOffice\program\soffice.exe"
WNS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
T, CI, META = C.T, C.CI, C.META

V, D, N, MISS = "Verified (code/execution)", "Documentation only", "Not verified", "Missing"
body: list[str] = []


def H1(t, first=False):
    body.append(E.para(E.run(t, b=True, sz=30), jc="left", before=0 if first else 200, after=120, page_break_before=not first, keep_next=True, outline=0))


def P(t):
    body.append(E.para(E.inline(t, sz=22), jc="both", after=100, line=264))


def TB(header, rows, widths, sz=17, aligns=None):
    body.append(E.table(header, rows, widths, sz=sz, aligns=aligns))


body.append(E.para(E.run("E-Report Supporting Pack", b=True, sz=36), jc="center", after=60))
body.append(E.para(E.run(C.TITLE, b=True, sz=24), jc="center", after=60))
body.append(E.para(E.run("Course 25AI2004 – Artificial Intelligence in Healthcare · Evidence checklist, open items, viva sheet and compliance matrix", i=True, sz=22), jc="center", after=240))
P("This pack accompanies the E-report. It was produced from the project files and from commands actually executed on 26–27 October 2026 (pytest, Ruff, the training pipeline, the Streamlit app, and reference look-ups against Crossref, PubMed, JMLR, arXiv and sdgs.un.org). Status labels follow four classes: **Verified (code/execution)**, **Documentation only**, **Not verified**, **Missing**.")

# ------------------------------------------------------------------ A. evidence
H1("A. Evidence and verification checklist", first=True)
rows = [
    ["768 records, 8 features, 268 positive / 500 negative", "`artifacts/data_profile.json` from executed profiling of the downloaded CSV", V, "Reported (Section 3.2, Table 3.1)"],
    ["Dataset source and licence", "`data/raw/provenance.json`; OpenML API metadata read at run time (licence field “Public”)", V + "; licence of original source not checked", "Reported with advice to verify terms; raw file not redistributed"],
    ["Zeros encode missing values (Glucose 5, BP 35, Skin 227, Insulin 374, BMI 11)", "`data_profile.json`; dataset documentation states “Missing Attribute Values: None”", V, "Section 3.3"],
    ["Stratified 80/20 split, 614/154, seed 42", "`metadata.json`; split re-computed from `train_test_split` with the same seed (214/400 and 54/100)", V, "Section 3.4, Table 5.1"],
    ["Seven candidates and hyperparameter grids", "`src/train.py` read in full", V, "Table 3.3"],
    ["CV ROC-AUC per model (LR 0.845 ± 0.013 …)", "`artifacts/metrics.json`, `model_comparison.csv` from executed training", V, "Table 5.2"],
    ["Selected model = Logistic Regression, C = 0.1, balanced", "`metrics.json` best_params; saved model inspected (5 × LogisticRegression C = 0.1, balanced)", V, "Sections 3.7, 5.3"],
    ["Sigmoid calibration kept; out-of-fold Brier 0.1602 → 0.1508", "`metrics.json` (`brier_raw_vs_calibrated_train_oof`)", V, "Sections 3.7, 5.7"],
    ["Threshold 0.2941 (sensitivity ≥ 0.80 out-of-fold)", "`metadata.json`", V, "Sections 3.8, 5.4"],
    ["Held-out test metrics and 95% bootstrap CIs", "`metrics.json`; confusion matrix 44/33/10/67 re-computed independently from the saved model", V, "Table 5.4, Section 5.5"],
    ["Calibration bins (8 quantile bins, 19–20 records)", "`metrics.json` curve data; bin sizes re-computed", V, "Table 5.5"],
    ["Permutation importance (Glucose 0.145 …)", "`metrics.json`", V, "Table 5.7"],
    ["Logistic-regression coefficients (Glucose +0.99 …)", "Extracted from the saved calibrated model (mean over 5 folds)", V, "Table 5.3"],
    ["SHAP additivity; example contributions", "Executed example input; `test_explanation_is_additive_and_matches_prediction` passed", V, "Table 5.8, Section 3.10"],
    ["Failure-case summary (10 FN, 33 FP)", "Computed from saved model on the seeded test split", V, "Table 5.6; described as indicative only"],
    ["Glucose-only / without-glucose ablation (CV ROC-AUC 0.799 / 0.768 vs 0.845)", "`research/stage1/glucose_ablation_cv_train_only.json`, same folds, training split only", V + " (exploratory)", "Section 5.9; replaces the earlier ‘circular’ wording"],
    ["45 tests passed", "`pytest -v` executed 27 Oct 2026: 45 passed in 5.8 s", V, "Table 4.2, Section 5.10"],
    ["Ruff clean", "Executed: source clean; 5 findings in notebook/helper script found and fixed; final run clean", V, "Sections 4.11, 5.13 (discrepancy disclosed)"],
    ["Streamlit pages, validation message, prediction flow", "Headless AppTest of all pages; Chrome (Playwright) screenshots of the running app", V, "Figures 4.2–4.5"],
    ["PDF and CSV report export", "3 report tests; sample PDF generated and rendered (Figure 4.6)", V, "Section 4.10"],
    ["Training time ≈ 25 s", "Log timestamps (03:51:31 → 03:51:54)", V + " (approximate)", "Section 4.2"],
    ["Python 3.12.3 and library versions", "`pip freeze`, `metadata.json`", V, "Table 4.1"],
    ["Hardware (AMD64, Windows 11 Home, CPU only)", "`platform` output; RAM not recorded", V + " (partial)", "Table 4.1 (RAM omitted)"],
    ["Training reproducible (identical metrics on re-run)", "Observed in two consecutive runs with the same seed during development", V + " (same machine only)", "Chapter 5 intro; not claimed across machines"],
    ["Docker image builds and runs", "`Dockerfile` inspected only", N, "Stated as unverified (Section 4.12, 6.2)"],
    ["Cloud deployment works", "Not attempted", N, "Stated as unverified"],
    ["WHO: 830 M (2022), 1.6 M deaths (2021)", "WHO fact sheet fetched 27 Oct 2026", V + " (external source)", "Section 1.1 [1]"],
    ["IDF Atlas: 10.5 % / 536.6 M (2021); 12.2 % / 783.2 M (2045)", "Abstract retrieved from PubMed/Semantic Scholar", V + " (external source)", "Section 1.1 [2]"],
    ["SDG 3 title and Target 3.4 wording", "sdgs.un.org/goals/goal3 fetched", V + " (external source)", "Section 1.4 [10]"],
    ["Literature entries: authors, years, DOIs, journals", "Crossref API for all DOI-bearing items; JMLR page for scikit-learn; arXiv record for SHAP", V, "References [1]–[23]"],
    ["Findings attributed to Sisodia, Khanam, Kaur, Kavakiotis, Chaki, Saito, Steyerberg, Rudin, Obermeyer", "Abstracts retrieved (Crossref / PubMed / Semantic Scholar)", V + " (abstracts only)", "Described only as far as the abstracts state; Kaur’s numerical results not quoted"],
    ["Niculescu-Mizil & Caruana: calibration methods compared", "Bibliographic data verified; no abstract retrieved", "Verified (bibliographic) / " + N + " (description)", "Described generally (Platt scaling vs isotonic regression); please read the paper’s abstract before the viva"],
    ["Efron & Tibshirani (book), Hosmer et al. (book 3rd ed.)", "Hosmer: Crossref record checked; Efron: bibliographic details not machine-verified", "Hosmer verified; Efron " + N, "Cited for general method; verify the Efron details in your library catalogue"],
    ["Original ADAP result: 76 % sensitivity/specificity, 576/192 split, cut-off 0.448", "Dataset documentation (OpenML description of UCI file)", D, "Section 2.3, attributed to the documentation"],
    ["KITS Technology Mission", "Not in template or project files", MISS, "Highlighted placeholder in Section 1.4"],
    ["Student name, registration number, guide name and designation", "Not supplied", MISS, "Highlighted placeholders on cover and certificate"],
    ["Clinical validity / accuracy vs. other studies", "Not established; deliberately not compared", "—", "Stated as not clinically validated; accuracy comparison avoided"],
]
TB(["Report claim", "Evidence source", "Verification status", "Report treatment"], rows, [2500, 3200, 1500, 2200], sz=16)

H1("Discrepancies found between documentation and evidence")
P("1. **Ruff status.** An earlier statement that the whole repository was Ruff-clean was true for `src/`, `ui/`, `tests/` and `app.py` but not for the exploratory notebook and one helper script (5 findings). Fixed; the final full-repository run reports no findings. Disclosed in report Section 5.13.")
P("2. **Chart legends.** While capturing screenshots, legends overlapped axis titles on the ROC and calibration charts. Fixed in `ui/components.py` before the screenshots used in the report were taken.")
P("3. **Range warnings.** The training-range warning uses raw feature ranges that include the dataset’s zeros, so low-end outliers rarely trigger a warning. Disclosed as a minor weakness (Section 5.11); not changed.")
P("4. **Glucose wording (corrected 27 Oct 2026).** Earlier text said glucose is partly circular with the label and that the model re-expresses the criterion. The Stage 1 audit found this unsupported: the dataset documentation defines a positive as 2-h glucose ≥ 200 mg/dL at any examination or in routine care, recorded glucose never exceeds 199, the timing is undocumented, and the model without glucose still reaches CV ROC-AUC 0.768. Wording corrected in the report, slides, README, model/dataset cards and the app.")
P("5. All other documented values (selected model, test ROC-AUC ≈ 0.81, threshold ≈ 0.29, counts) matched the saved artefacts.")

# ------------------------------------------------------------------ B. open items
H1("B. Remaining placeholders, missing evidence and actions before submission")
items = [
    ["1", "Cover page: replace [STUDENT NAME] ([REGISTRATION NUMBER]); [FACULTY NAME]", "Student", "Highlighted in yellow. If this is a team project, add the other students (the template shows four lines; one was kept)."],
    ["2", "Bonafide certificate: student name/registration, faculty name and designation", "Student / faculty", "Highlighted. The certificate carries no signature; the faculty signs on the printed copy."],
    ["3", "Section 1.4: KITS Technology Mission paragraph", "Student", "Insert the mission statement/theme from your institution and one or two linking sentences."],
    ["4", "Evaluation sheet (page v)", "Faculty", "Left exactly as in the template, including “Ms. R. Hemalatha”; marks and signature are the faculty’s."],
    ["5", "Online certification (10 marks in the rubric)", "Student", "Not part of the report text; attach/submit the certificate as the course requires."],
    ["6", "Page limit", "Student", "The template’s sample contents suggests about 15 body pages; this report has 36. Confirm the limit with your guide. A shortened version can be produced on request."],
    ["7", "Table-of-contents page numbers", "Student", "Computed from a LibreOffice rendering. Word may paginate slightly differently: after final edits, open in Word and check the page numbers (they are typed values, as in the template)."],
    ["8", "Dataset terms", "Student", "OpenML shows licence “Public”. Check the UCI/NIDDK terms before redistributing the raw file (it is not in the repository)."],
    ["9", "Niculescu-Mizil & Caruana, Efron & Tibshirani", "Student", "Read the abstract/catalogue entry and confirm the short descriptions in Sections 2.4 and 3.9."],
    ["10", "Docker and cloud deployment", "Student", "Either build/run and record the result, or keep the “not verified” wording."],
    ["11", "Screenshots", "Student", "Four real screenshots are included. Session History and About pages were captured (`docs/screenshots/06,07`) but not used; add if you wish."],
    ["12", "Originality and policy", "Student", "Read and understand every section, add your own analysis where you can, and run the institution’s required similarity check. No similarity or AI-detection score can be promised."],
    ["13", "Presentation date", "Student", "The template’s “29/10/26” was left unchanged; confirm it."],
]
TB(["#", "Item", "Owner", "Action"], items, [400, 3300, 1100, 4600], sz=17)

# ------------------------------------------------------------------ C. viva
H1("C. Viva preparation sheet")
qa = [
    ("What does your system do, and what does it not do?", "It takes eight health measurements, returns a calibrated probability, a flag against a screening threshold, a SHAP explanation and a downloadable report. It does not diagnose; it is an educational prototype trained on one small dataset and not clinically validated."),
    ("Why the Pima dataset, and what are its problems?", "It is public, documented and widely used (768 records). Problems: only adult women of Pima heritage, 1990s data, zeros encode missing values (insulin 374, skin-fold 227), and the outcome’s timing relative to the features is undocumented (label rule: 2-h glucose ≥ 200 mg/dL at any examination or in routine care, yet recorded glucose never exceeds 199)."),
    ("Why treat zeros as missing?", "A glucose, blood pressure, skin-fold, insulin or BMI of 0 is physiologically impossible. The documentation says there are no missing values, so zeros are an encoding of ‘not measured’. Pregnancies = 0 is valid, so it is kept."),
    ("What is data leakage and how did you avoid it?", "Using information from the test data during training or selection. Imputation medians and scaling are inside the pipeline (refit per CV fold on training data only); tuning, model selection, calibration and the threshold all use training data; the test set is scored once."),
    ("Why stratified splitting and 5-fold CV?", "Stratification keeps the 35 % positive rate in every split and fold. CV gives a more stable estimate than a single validation split on only 614 records and is used for tuning and selection."),
    ("Why logistic regression?", f"It had the best mean CV ROC-AUC ({C.COMP['Logistic Regression']['cv_roc_auc']:.3f}), the top four models were within noise, and it is the most interpretable. Selection rule: best score, then the simplest model within one standard error."),
    ("What are C and class_weight='balanced'?", "C is the inverse regularisation strength (smaller = stronger L2 penalty); the selected value was 0.1. ‘Balanced’ re-weights classes inversely to frequency so the minority (positive) class counts more."),
    ("What is probability calibration and why did you do it?", "Calibration makes predicted probabilities match observed frequencies. I fitted sigmoid (Platt-type) calibration with 5 folds and kept it because the out-of-fold Brier score fell from 0.1602 to 0.1508."),
    ("What is the Brier score? Is 0.174 good?", "Mean squared error between predicted probability and the 0/1 outcome (lower is better). Always predicting the prevalence scores about 0.227, so 0.174 is better than no-skill; it is not proof of clinical usefulness."),
    ("Explain ROC-AUC and PR-AUC.", f"ROC-AUC (0.809) is the probability a random positive scores above a random negative. PR-AUC ({T['pr_auc']:.3f}) is average precision; the no-skill level is the prevalence (about 0.35). PR is informative with imbalance."),
    ("Define sensitivity, specificity, precision. Why is precision only 0.57?", f"Sensitivity = TP/(TP+FN) = 44/54 = {T['recall_sensitivity']:.3f}; specificity = TN/(TN+FP) = 67/100 = {T['specificity']:.3f}; precision = TP/(TP+FP) = 44/77 = {T['precision']:.3f}. The threshold favours sensitivity, which creates 33 false positives."),
    ("How did you choose the threshold? Why not 0.5?", "Largest threshold whose out-of-fold sensitivity on the training set is at least 0.80, giving 0.2941. At 0.5 the CV recall of most models is only 0.53–0.59, which is too many missed cases for a screening-style tool. It is an operating point, not a medical cut-off."),
    ("What do the confidence intervals mean and why are they wide?", f"Stratified percentile bootstrap, 1000 resamples of the test set. The test set has 154 records (54 positive), so e.g. ROC-AUC is {T['roc_auc']:.3f} with 95 % CI {C.ci('roc_auc')}."),
    ("What is SHAP? What does ‘additive’ mean?", "SHAP assigns each feature a contribution to one prediction so that baseline + sum of contributions = predicted probability. I use the permutation explainer on the whole pipeline’s probability and test the additivity. If SHAP fails, an occlusion fallback is used."),
    ("Does a high SHAP value or importance mean the feature causes diabetes?", "No. It shows how the model uses the input, i.e. an association in this dataset. Correlated features can share importance, and the model may be wrong or biased."),
    ("Why does glucose dominate?", f"Permutation importance of glucose is {C.IMP['Glucose']['mean']:.3f}, far above others, and glucose alone gives a training CV ROC-AUC of 0.799. The other features still add signal (0.768 without glucose, 0.845 with all). The documented label rule is itself a glucose criterion, so a strong association is expected, but the recorded glucose cannot be the exact value that defined the label (maximum 199) and the timing is undocumented."),
    ("Test ROC-AUC (0.809) is lower than out-of-fold (0.846). Overfitting?", "The test value lies within its own CI and the gap is the size expected from sampling variability with 154 records; one split cannot show overfitting or luck. External validation would be needed."),
    ("What are the failure cases?", "False negatives (10) have a median glucose of 113.5, close to true negatives (99), so the model has little to separate them; false positives (33) have median glucose 137 and BMI 35.9, looking like positives. Counts are small."),
    ("Is the system clinically validated?", "No. It has internal validation on one dataset only. Clinical use would need external and prospective validation, subgroup analysis and regulatory review."),
    ("How is privacy handled?", "No identifiers are requested; nothing is sent to third parties; history is in session memory only; reports are generated in memory."),
    ("How does the app handle invalid input?", "validation.py checks types, ranges, required fields, integers and unknown fields, and returns field-specific messages. Blank optional values become missing (never zero) and are imputed by training medians, and the user is told."),
    ("What do your 45 tests prove?", "Software behaviour: validation, pipeline behaviour, feature order, probability range, SHAP additivity and fallback, report content, error handling. They do not prove clinical validity."),
    ("How is the work reproducible?", "Fixed seed 42 in config, pinned dependency ranges, provenance hash of the data, saved pipeline; re-running training gave identical metrics on my machine."),
    ("What would you do next?", "External validation on other datasets, subgroup/fairness analysis, calibration monitoring, verified container and cloud deployment. These are proposals; none is implemented."),
    ("Why not deep learning?", "768 records is too small for a deep model to be justified; comparisons showed several classical models perform similarly, so a simple interpretable one is preferable [Rudin]."),
]
TB(["Likely question", "Accurate answer from this implementation"], [[q, a] for q, a in qa], [3000, 6400], sz=17)

# ------------------------------------------------------------------ D. compliance
H1("D. Compliance matrix")
P("Mapping of the report to the template’s required structure and to its evaluation rubric. Locations refer to the final E-report.")
comp = [
    ["Cover page (title, names, course, programme, supervisor, institution, October 2026)", "Cover", "Complete; personal items are highlighted placeholders"],
    ["Bonafide certificate", "Page ii", "Complete; names, faculty and designation are placeholders; wording unchanged"],
    ["Abstract (listed in template contents)", "Page iii", "Complete, with keywords"],
    ["Table of contents with page numbers", "Page iv", "Template table kept; page numbers filled from rendering; REFERENCES row added"],
    ["Evaluation report sheet", "Page v", "Unchanged from template"],
    ["Chapter 1 Introduction: 1.1 Background, 1.2 Industry relevance, 1.3 Aim and objectives, 1.4 SDG / KITS mission", "Chapter 1 (pp. 1–3)", "Complete except the KITS mission paragraph (placeholder)"],
    ["Chapter 2 Literature review (incl. comparative table, research gap)", "Chapter 2 (Table 2.1)", "Complete; 23 verified references in IEEE style"],
    ["Chapter 3 Methodology", "Chapter 3 (Sections 3.1–3.12)", "Complete; equations numbered (3.1)–(3.11)"],
    ["Chapter 4 Fabrication/Simulation/Program or Code/Design (title kept)", "Chapter 4 (Sections 4.1–4.12)", "Complete; Docker/cloud stated as unverified"],
    ["Chapter 5 Results and interpretation", "Chapter 5 (Sections 5.1–5.13)", "Complete; all numbers from artefacts"],
    ["Chapter 6 Conclusion and future scope", "Chapter 6", "Complete; completed work separated from proposals"],
    ["References", "End of report", "23 entries; each cited in the text"],
    ["Rubric: Online certification completion (10)", "Not in the report", "Student must provide the certificate separately"],
    ["Rubric: Problem statement with SDG (5)", "Sections 1.1, 1.3, 1.4", "Addressed; KITS paragraph pending"],
    ["Rubric: Methodology implementation (10)", "Chapters 3 and 4", "Addressed with code excerpts, tests and diagrams"],
    ["Rubric: Result analysis (5)", "Chapter 5", "Addressed with tables, figures, CIs and failure analysis"],
    ["Rubric: Report (10)", "Whole document", "Template formatting kept; numbered tables, figures and equations; page numbers; references"],
]
TB(["Template requirement", "Where in the report", "Status"], comp, [4200, 2200, 3000], sz=17)

# ------------------------------------------------------------------ assemble (reuse template package)
WORK = HERE / "work" / "support_pkg"
if WORK.exists():
    shutil.rmtree(WORK)
with zipfile.ZipFile(TEMPLATE) as z:
    z.extractall(WORK)
doc = WORK / "word" / "document.xml"
t = etree.parse(str(doc))
bd = t.getroot().find(f"{{{WNS}}}body")
for ch in list(bd):
    bd.remove(ch)
frag = etree.fromstring(f'<r xmlns:w="{WNS}">{"".join(body)}</r>')
for node in frag:
    bd.append(node)
sect = etree.fromstring(
    f'<w:sectPr xmlns:w="{WNS}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><w:footerReference w:type="default" r:id="rId51"/>'
    '<w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="1134" w:right="1418" w:bottom="1134" w:left="1418" w:header="0" w:footer="709" w:gutter="0"/><w:cols w:space="720"/></w:sectPr>')
bd.append(sect)
t.write(str(doc), xml_declaration=True, encoding="UTF-8", standalone=True)
footer = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:ftr xmlns:w="{WNS}"><w:p><w:pPr><w:jc w:val="center"/></w:pPr>'
          '<w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r><w:r><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:t>1</w:t></w:r><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p></w:ftr>')
(WORK / "word" / "footer3.xml").write_text(footer, encoding="utf-8")
rels = (WORK / "word" / "_rels" / "document.xml.rels").read_text(encoding="utf-8")
(WORK / "word" / "_rels" / "document.xml.rels").write_text(rels.replace("</Relationships>", '<Relationship Id="rId51" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer3.xml"/></Relationships>'), encoding="utf-8")
ct = (WORK / "[Content_Types].xml").read_text(encoding="utf-8")
(WORK / "[Content_Types].xml").write_text(ct.replace("</Types>", '<Override PartName="/word/footer3.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/></Types>'), encoding="utf-8")
if OUT.exists():
    OUT.unlink()
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(WORK / "[Content_Types].xml", "[Content_Types].xml")
    for f in sorted(WORK.rglob("*")):
        if f.is_file() and f.name != "[Content_Types].xml":
            z.write(f, f.relative_to(WORK).as_posix())
subprocess.run([SOFFICE, "--headless", "--convert-to", "pdf", "--outdir", str(OUT.parent), str(OUT)], check=True, capture_output=True, timeout=300)
print("built", OUT)
