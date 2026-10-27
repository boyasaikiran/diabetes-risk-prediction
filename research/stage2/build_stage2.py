"""Builds research/stage2/LITERATURE_MATRIX.csv and the tables embedded in STAGE2_NOTES.md.
Bibliographic fields come from sources_verified.json (Crossref/arXiv); analytic fields below are
paraphrased notes written from ABSTRACTS ONLY (full texts not read) and are for the student's own use."""
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
V = json.loads((HERE / "sources_verified.json").read_text(encoding="utf-8"))

# key: (role, peer-review note, objective, dataset/n, methods, evaluation, findings (abstract-level), limitations/reviewer notes, relevance to us, does NOT establish)
NR = "NR"
S = {
 # ---------------- diabetes / Pima group
 "kavak": ("D", "journal", "Review ML/data-mining applications in diabetes research", "n/a (review)", "Systematic review; 4 application categories", "n/a", "Prediction/diagnosis most popular; ~85% supervised methods; SVM most used; mainly clinical datasets", "Pre-2017; breadth over depth; not a performance benchmark", "Context for supervised baselines", "Which model is best; calibration or explanation practice"),
 "chaki": ("D", "journal", "Review detection, diagnosis, self-management of diabetes with ML/AI", "107 publications (Scopus, PubMed)", "Systematic review by datasets, preprocessing, features, models, assistants, metrics", "n/a", "Organises the field; lists three open research issues", "Abstract does not name the issues; read full text", "Taxonomy of datasets/preprocessing/metrics", "Performance ranking of methods"),
 "khanam": ("D", "journal", "Compare ML algorithms for diabetes prediction", "Pima, 768", "7 ML algorithms + neural networks", NR, "LR and SVM performed well; 2-hidden-layer NN reached 88.6% accuracy", "Validation protocol NR in abstract; accuracy only", "Supports LR/SVM as strong Pima baselines", "That 88.6% survives leakage-safe evaluation"),
 "sisodia": ("D", "journal (conference proceedings volume)", "Predict diabetes with classification algorithms", "Pima, 768", "Decision tree, SVM, naive Bayes", NR, "Naive Bayes highest accuracy 76.30%; ROC curves used to verify", "Accuracy-centred; calibration NR; protocol NR", "Reference accuracy level under simple protocol", "Calibration, uncertainty"),
 "kaur": ("D", "journal", "Diabetes classification using ML in R", "Pima, 768", "SVM-linear, SVM-RBF, k-NN, ANN, MDR", NR, "Compares five models (numbers not in abstract read)", "Results NR", "Another multi-model Pima comparison", "Any numerical result"),
 "miao": ("D", "conference", "Predict diabetes on PIMA with several ML algorithms", "Pima, 768", "Several ML algorithms; standardisation; later 'adjustment'", NR, "SVM best: accuracy 85.06% (standardised), 87.01% after adjustment", "Nature of 'adjustment' and whether test data guided it: NR; check full text", "Example of high-accuracy single-protocol claims", "Leakage-safe performance"),
 "msys": ("D", "journal", "Effect of replacing missing values and outliers on diabetes risk stratification", "Pima, 768 (268/500)", "Group-median imputation of missing, median for outliers; 6 feature selectors × 10 classifiers", NR + " (validated 'for stability and reliability')", "RF+RF reached accuracy 92.26%, sens 95.96%, spec 79.72%, AUC 0.93", "'Group median' may be class-conditional (check full text for label use before split); preprocessing order NR", "Direct precedent on handling zeros/outliers; magnitude of claims is a leakage red flag to check", "That imputation-by-group is leakage-free"),
 "kirbas": ("D", "journal", "SHAP-interpretable diabetes prediction on Pima", "Pima, 768", "8 models; SMOTE; scaling; SHAP", "Train/test split and 10-fold CV", "RF best: acc 82%, F1 0.83 (split); 83%/0.84 (CV); SHAP: glucose, BMI, pregnancies, insulin key", "Whether SMOTE/scaling are inside folds: NR; calibration NR; SHAP stability NR", "Closest 'SHAP on Pima' peer-reviewed precedent", "Explanation stability; calibration"),
 "rfegru": ("D", "journal", "RFE-GRU model for Pima classification", "Pima, 768", "Mean imputation, normalisation, RFE feature selection, GRU; vs RF, LR, kNN, NB, HGB", NR, "Precision/recall/F1/accuracy ≈ 90.5-90.7%, AUC 0.9278", "Much higher than leakage-safe studies; split and order of preprocessing/feature selection NR", "Illustrates the spread of reported performance", "Validity of the 0.93 AUC"),
 "etasr": ("D", "journal", "Leakage-preventing preprocessing pipeline for diabetes prediction", "Pima, 768", "MICE, SMOTE, z-score, 2 feature-selection methods; RF, MLP, XGBoost, SVM, LR", "Single 80:20 split and 5-fold CV", "RF 79.79% acc (split); MLP 77.81% acc, ROC-AUC 84.43% (CV)", "Stated aim is leakage prevention; abstract does not mention calibration or explanation; engineered features (Glucose_BMI) selected", "Overlaps our leakage-safe preprocessing contribution", "Calibration, uncertainty, explanation"),
 "aposta": ("D", "journal (venue quality not assessed)", "Statistically rigorous, cross-dataset comparison of LR, RF, XGBoost, SVM", "Pima 768; BRFSS 2015 (8,000 subsample; 253,680 full)", "Fold-nested scaling/SMOTE; 10x repeated 5-fold CV; paired Wilcoxon on fold AUCs; nested CV; SHAP on XGBoost", "Single split vs repeated CV vs nested CV", "Single split favoured XGBoost; repeated CV: LR best (AUC 0.835±0.028); XGBoost worst on Pima; ranking reverses on full BRFSS", "Wilcoxon on per-fold AUCs: folds are not independent (see Nadeau & Bengio, Demsar); whether a variance correction was applied is NR, check full text; calibration NR", "Strong overlap: leakage-safe repeated-CV model comparison with LR winning on Pima", "Calibration; explanation stability"),
 "jaimlnn": ("D", "journal (venue quality not assessed)", "Stability of permutation feature importance across 5 classifiers on clinical tabular data", "Pima, WDBC, Cleveland heart", "LR, SVM, RF, HGB, MLP; permutation importance each fold", "10x5-fold stratified CV (50 fits); corrected resampled t-test; Spearman, top-5 Jaccard, top-feature recurrence; data reduced to 25%", "Equal AUC but different stability; Pima stability 0.70-0.87, glucose ranked first in every fit of four models; LR 0.90 to 0.68 at 25% data", "Permutation importance only (not SHAP); abstract mentions calibration measured; full text needed", "Closest overlap with 'explanation stability' direction", "SHAP stability; local-explanation stability; effect of imputation"),
 "thresh_math": ("D", "journal (venue quality not assessed)", "Joint effect of oversampling intensity and decision threshold on imbalanced medical classification", "Pima; Heart Failure; Thoracic Surgery", "5 classifiers; baseline/SMOTE/ADASYN; thresholds 0.30-0.70", "Leakage-free repeated stratified 10-fold ×5; mixed-effects model", "Thresholds <0.5 beneficial on Pima; best F1 0.6890; oversampling tended to increase Brier", "F1-based threshold choice; abstract-level only", "Overlaps threshold-analysis direction; shows Brier worsens with oversampling", "Threshold choice for a screening sensitivity target; calibration of unsampled models"),
 "leakfree_rs": ("D", "PREPRINT (Research Square, not peer-reviewed)", "Leakage-free, statistically validated evaluation framework for diabetes risk", "Pima 768; Early-Stage Diabetes Risk dataset", "6 models (LR, RF, FFNN, BPNN, GRNN, ABC-FFNN); fold-contained preprocessing", "Multi-seed stratified 10-fold CV; calibration; pairwise statistical tests", "Pima AUC 0.76-0.84 (GRNN 0.837±0.002; LR 0.832; RF 0.829); calibration assessed", "Preprint; details need full text", "Strong overlap with 'reproducible evaluation framework' direction", "Explanation stability"),
 "calib_first_rs": ("D", "PREPRINT (Research Square, not peer-reviewed)", "Calibration-first, physiology-aware parsimonious LR for diabetes risk", "Not named in the abstract portion read (predictors suggest Pima)", "5 predictors; insulin orthogonalised from glucose; Brier minimisation; vs LR, RF, XGB, GB", "Covariate-shift simulations", "LR AUROC 0.836, AUPRC 0.714, Brier 0.166, 'excellent calibration'", "Preprint; dataset and validation protocol need full text", "Overlaps 'calibration-aware LR' direction", "External validity"),
 "reliab_aware": ("D", "journal (venue quality not assessed)", "Reliability-aware, interpretable framework for diabetes prediction", "Pima, 768", "LR, RF, XGBoost; SHAP global/local; Feature Consistency Index (cross-model SHAP agreement); perturbation robustness", "Brier score, reliability diagrams", "XGB AUC 0.8374 best; RF best Brier 0.1646; glucose and BMI consistently attributed; BP, skin thickness weak and unstable", "Resampling stability of SHAP not described in abstract; protocol NR", "Overlaps calibration + SHAP + robustness at a broad level", "Stability across resampled training sets"),
 "zenodo_shap": ("D", "REPOSITORY RECORD (Zenodo; dissertation type; authors not listed in metadata; peer review not evident)", "Stability of SHAP under class imbalance for diabetes", "Pima", "SVM, kNN, DT, XGBoost; SMOTE-Tomek at varying ratios; coefficient of variation of SHAP values", NR, "XGBoost: best accuracy but less stable SHAP; SVM more stable", "Provenance weak; cite only with caution", "Overlaps SHAP-stability idea (class-imbalance axis)", "Resampling stability for calibrated LR"),
 "collins2011": ("D", "journal", "Review methods and reporting of T2D risk-prediction model development", "Systematic review of T2D models", "Methodological review", "n/a", "Widespread poor methods: univariate pre-screening, categorising predictors, missing data handling unreported in 41% of studies", "Not about ML specifically", "Shows long-standing reporting/method problems in diabetes prediction", "ML-specific practice"),
 "noble2011": ("D", "journal", "Evaluate risk models/scores for T2D", "Systematic review", "Standard + realist review", "n/a", "Many models; few externally validated; usability and use-case often unclear", "Pre-ML era focus", "Context: intended use and external validation", "Pima-specific issues"),
 "pima_survey": ("D", "journal (venue quality not assessed)", "Survey and evaluation of Pima-based diabetes classification", "Pima, 768", "Survey + own evaluation (scaling, feature selection, oversampling)", NR, "Preprocessing helps; RF often best; evaluation approaches vary widely", "Abstract-level; may inherit heterogeneity it describes", "Evidence that Pima evaluation practice is inconsistent", "Calibration/stability"),
 # ---------------- methodology / explainability / reporting group
 "davis": ("M", "conference", "Relationship between PR and ROC curves", "n/a", "Theory", "n/a", "ROC dominance iff PR dominance; achievable PR curve; PR more informative for skewed data", "Theoretical", "Why report PR-AUC", "Clinical utility"),
 "saito": ("M", "journal", "ROC vs PR plot on imbalanced data", "n/a", "Analytical and simulation", "n/a", "ROC plots can be deceptive on imbalanced data; PR plots more informative", "Not specific to healthcare", "Support for PR reporting", "Calibration"),
 "steyerberg": ("M", "journal", "Framework for prediction-model performance measures", "Case study: testicular cancer (544 dev / 273 val)", "Review of measures", "Illustrative", "Report discrimination and calibration always; decision-analytic measures if used for decisions", "Single case study", "Metric selection rationale", "ML-specific recommendations"),
 "vancalster2019": ("M", "journal", "Argue calibration deserves attention", "n/a", "Position/guidance (STRATOS)", "n/a", "Poor calibration can mislead and harm decisions; how to avoid and assess it", "Guidance, not a new experiment", "Core justification for calibration analysis", "Specific method superiority"),
 "vancalster2016": ("M", "journal", "Define a calibration hierarchy", "Simulated data", "Four calibration levels (mean, weak, moderate, strong)", "Simulation", "Defines levels and implications for development/validation", "Simulation only", "Vocabulary for calibration claims", "Real-data behaviour of ML models"),
 "niculescu": ("M", "conference", "Quality of probabilities from supervised learners", "Multiple datasets (abstract NR)", "Compares learners and calibration methods", "Empirical", "Boosted trees/stumps distort probabilities (sigmoid-shaped); naive Bayes pushes to 0/1; other models better calibrated (abstract-level)", "2005; modern learners differ", "Basis for comparing calibrators", "Behaviour on small clinical data"),
 "vickers2006": ("M", "journal", "Decision curve analysis", "n/a", "Method", "Net benefit", "Evaluates models by clinical consequences using only the dataset", "Needs a plausible threshold range", "Possible threshold-utility analysis", "That our threshold is clinically right"),
 "wynants2019": ("M", "journal", "Risk-threshold myths for prediction models", "n/a", "Guidance (STRATOS)", "n/a", "Thresholds often chosen ad hoc; implicit costs of FP/FN matter", "Guidance", "Justifies treating threshold as a stated assumption", "Specific threshold values"),
 "wolff": ("M", "journal", "PROBAST risk-of-bias tool", "n/a", "Tool development", "n/a", "Structured assessment of bias/applicability", "Needs full guidance to apply", "Checklist to self-audit our study", "Study quality by itself"),
 "tripodai": ("M", "journal", "TRIPOD+AI reporting guideline", "n/a", "Consensus guidance", "n/a", "Updated reporting items for regression and ML prediction models", "Reporting, not validity", "Checklist for manuscript", "Model quality"),
 "riley2019": ("M", "journal", "Minimum sample size for binary/time-to-event prediction models", "n/a", "Criteria on n, events, EPP", "n/a", "Sample-size criteria for model development", "Framework; needs application", "Quantifies how small 768/268 is relative to parameters", "That 768 is adequate"),
 "kapoor": ("M", "journal", "Leakage and reproducibility in ML-based science", "Survey of 17 fields, 294 papers", "Survey + taxonomy of 8 leakage types + case reproduction", "Reproducibility study", "Leakage widespread; complex ML no better than LR once errors corrected (civil-war example)", "Not medical", "Leakage taxonomy; model-info sheet", "Pima-specific leakage rates"),
 "varma": ("M", "journal", "Bias when CV error is used for model selection", "Simulated/real (NR)", "Study of non-nested CV", "Empirical", "Evaluates validity of CV error of the optimised classifier (magnitude: read full text)", "Abstract-level only", "Justifies nested CV", "Size of bias in our setting"),
 "cawley": ("M", "journal (JMLR; no DOI)", "Over-fitting in model selection and selection bias", "NR", "Analysis of model-selection criteria", "Empirical", "Selection-criterion optimisation causes bias in performance estimates", "Volume/pages to confirm from JMLR (v11, cawley10a)", "Justifies nested CV", "Quantitative bias for Pima"),
 "vabalas": ("M", "journal", "ML validation with limited sample size", "Simulated/real small datasets", "Compares validation approaches", "Empirical", "Validation choices affect bias with small samples; design guidance", "Not medical-specific", "Small-sample evaluation design", "Pima-specific thresholds"),
 "nadeau": ("M", "journal", "Variance of generalisation-error estimators (corrected resampled t-test)", "n/a", "Statistical analysis", "n/a", "ABSTRACT NOT RETRIEVED; content known only from general knowledge — verify before citing", "Verify full text", "Why repeated-CV fold comparisons need variance correction", "—"),
 "dietterich": ("M", "journal", "Compare approximate statistical tests for classifiers", "Simulated + real", "5 tests compared for Type I error", "Empirical", "Reviews tests and their error rates", "1998", "Model-comparison testing options", "Modern repeated-CV practice"),
 "demsar": ("M", "journal (JMLR; no DOI)", "Statistical comparison of classifiers over multiple datasets", "n/a", "Review of tests", "n/a", "Recommends tests for multi-dataset comparisons (abstract-level)", "Multi-dataset setting; we have one", "Caution against naive significance tests", "Single-dataset inference"),
 "christodoulou": ("M", "journal", "Compare LR with ML for clinical prediction", "71 studies, 282 comparisons", "Systematic review", "Studies' validation", "No ML advantage at low risk of bias; 68% potential validation bias; calibration unaddressed in 79%", "Search period 2016-2017", "Key background: LR vs ML; calibration neglected", "Current (2026) state"),
 "lundberg2017": ("M", "preprint/conference (NIPS 2017)", "Unified framework for model-prediction attributions (SHAP)", "n/a", "Theory", "n/a", "Additive attribution framework", "—", "Basis of our explainer", "Stability"),
 "lundberg2020": ("M", "journal", "Exact TreeSHAP, local-to-global explanations", "Medical + other datasets (NR)", "Polynomial-time algorithm; interaction values", "Empirical", "Local explanations combined into global understanding for tree models", "Tree-focused", "Context for SHAP variants", "Behaviour for linear/calibrated pipelines"),
 "kumar2020": ("M", "conference (ICML 2020)", "Critique Shapley-based feature importance", "n/a", "Theoretical analysis", "n/a", "Mathematical and human-centric problems with Shapley explanations", "Arxiv version read", "Caveat on interpreting SHAP", "Empirical size of instability"),
 "slack": ("M", "conference", "Adversarial attacks on LIME/SHAP", "Real datasets", "Adversarial classifiers", "Empirical", "Perturbation-based explainers can be fooled", "Adversarial setting", "Limits of faithfulness claims", "Behaviour in benign settings"),
 "alvarez": ("M", "PREPRINT (arXiv)", "Robustness of interpretability methods", "NR", "Robustness metrics", "Empirical", "Current methods perform poorly on robustness metrics", "Preprint", "Concept: similar inputs should give similar explanations", "Resampling stability"),
 "krishna": ("M", "PREPRINT (arXiv)", "Disagreement problem among post hoc explainers", "NR", "Formalisation + study", "Empirical/qualitative", "Post hoc methods often disagree", "Preprint", "Motivates stability/agreement checks", "Pima-specific"),
 "matijevic": ("M", "PREPRINT (arXiv)", "Reduce individual prediction instability in clinical models", "Clinical cohorts (NR)", "Bootstrapping-based regularisation for deep nets", "Empirical", "Predictions vary across training samples; proposed regulariser", "Deep learning; preprint", "Shows instability concept in clinical risk models", "LR/tabular stability"),
 "ghassemi": ("M", "journal (viewpoint)", "Argue current XAI is a false hope in health care", "n/a", "Viewpoint", "n/a", "Post hoc explanations do not guarantee trust/fairness", "Opinion", "Caution on explanation claims", "Empirical evidence"),
 "rudin": ("M", "journal", "Use interpretable models for high-stakes decisions", "n/a", "Position paper", "n/a", "Prefer inherently interpretable models", "Position", "Supports LR choice", "Performance parity in all domains"),
 "obermeyer": ("M", "journal", "Racial bias in a population-health algorithm", "Large US health-system data", "Audit", "Empirical", "Cost used as proxy for need created bias", "US-specific", "Illustrates label/target choice risks", "Pima issues"),
 "gianfrancesco": ("M", "journal", "Biases in ML using EHR data", "n/a", "Viewpoint", "n/a", "Lists bias sources", "Opinion", "Framing for population-specific bias", "Pima-specific"),
}
assert set(S) <= set(V), set(S) - set(V)


def cite(k):
    r = V[k]
    au = ", ".join(r.get("authors", [])[:3]) + (f" +{r['n_authors'] - 3}" if r.get("n_authors", 0) > 3 else "")
    ident = r.get("doi") or ("arXiv:" + str(r.get("arxiv")) if r.get("arxiv") else "JMLR")
    vol = f" {r.get('volume') or ''}{('(' + r['issue'] + ')') if r.get('issue') else ''}{(', ' + r['pages']) if r.get('pages') else ''}".strip()
    return au, r.get("year"), r.get("title"), (r.get("venue") or ""), vol, ident


COLS = ["key", "role", "authors", "year", "title", "venue", "vol/pages", "identifier", "type / peer-review note", "objective", "dataset & n", "methods", "evaluation strategy", "principal findings (abstract-level)", "limitations / reviewer notes", "relevance to our work", "what it does NOT establish", "verification"]
rows = []
for k, (role, peer, obj, ds, meth, ev, fnd, lim, rel, notest) in S.items():
    au, yr, title, venue, vol, ident = cite(k)
    r = V[k]
    ver = ("Metadata verified via Crossref" if r.get("crossref_ok") else "Metadata verified via arXiv API" if r.get("arxiv") else "Record found via OpenAlex (DataCite DOI, not in Crossref); authors not listed" if r.get("doi") else "Title verified on JMLR page; volume/pages to confirm") + f"; abstract read from {r.get('abstract_source') or 'NOT RETRIEVED'}; full text NOT read"
    rows.append([k, role, au, yr, title, venue, vol, ident, peer, obj, ds, meth, ev, fnd, lim, rel, notest, ver])
with open(HERE / "LITERATURE_MATRIX.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(COLS)
    w.writerows(rows)
print("matrix rows:", len(rows), "| diabetes:", sum(1 for r in rows if r[1] == "D"), "| methods:", sum(1 for r in rows if r[1] == "M"))

# ---------------- markdown tables
def md(cells):
    return "| " + " | ".join(str(c).replace("|", "/").replace("\n", " ") for c in cells) + " |"


AU_OVERRIDE = {"vancalster2019": "Van Calster et al. (STRATOS)", "vancalster2016": "Van Calster et al.", "wynants2019": "Wynants et al. (STRATOS)",
               "reliab_aware": "V. R. and Sasirekha", "pima_survey": "Abu-Shareha et al.", "jaimlnn": "Dalal and Akbar", "miao": "Miao",
               "zenodo_shap": "(authors not listed)", "cawley": "Cawley and Talbot", "demsar": "Demsar", "tripodai": "Collins et al. (TRIPOD+AI)"}


def short_au(k):
    if k in AU_OVERRIDE:
        return AU_OVERRIDE[k]
    r = V[k]
    a = r.get("authors", [])
    fam = a[0].split()[0] if a else "?"
    return f"{fam}{' et al.' if r.get('n_authors', 0) > 1 else ''}" if a else "(authors not listed)"


tabA = [md(["Study", "Year", "Dataset", "Method", "Validation", "Metrics (as reported)", "Explainability", "Limitations (reviewer notes)", "Relationship to our work"]), md(["---"] * 9)]
XAI = {"kirbas": "SHAP (global)", "aposta": "SHAP (XGBoost)", "jaimlnn": "Permutation importance stability", "reliab_aware": "SHAP global+local; FCI", "zenodo_shap": "SHAP stability (CV of SHAP)", "miao": "Correlation only"}
for k, v in S.items():
    if v[0] != "D":
        continue
    role, peer, obj, ds, meth, ev, fnd, lim, rel, notest = v
    tabA.append(md([f"{short_au(k)} [{k}]", V[k].get("year"), ds, meth, ev, fnd, XAI.get(k, "none stated"), lim + ("; " + peer if "PREPRINT" in peer or "REPOSITORY" in peer else ""), rel]))
tabB = [md(["Source [key]", "Year", "Type", "What it contributes (abstract-level)", "What it does NOT establish", "Use for us"]), md(["---"] * 6)]
for k, v in S.items():
    if v[0] != "M":
        continue
    role, peer, obj, ds, meth, ev, fnd, lim, rel, notest = v
    tabB.append(md([f"{short_au(k)} [{k}]", V[k].get("year"), peer, fnd, notest, rel]))
(HERE / "tableA.md").write_text("\n".join(tabA), encoding="utf-8")
(HERE / "tableB.md").write_text("\n".join(tabB), encoding="utf-8")
print("tables written")
