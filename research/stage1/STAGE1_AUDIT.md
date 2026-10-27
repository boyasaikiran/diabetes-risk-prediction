# Stage 1 — Project audit and results verification

Project: *Diabetes Risk Prediction Using Machine Learning and Explainable AI* (Pima Indians Diabetes Database, OpenML 37)
Audit date: 27 Oct 2026. Evidence: files in the repository, plus commands **actually executed** for this audit
(`research/stage1_verify.py` → `research/stage1/verification_results.json`; `pytest`; `ruff`; an isolated retraining run).
Scope: Stage 1 only. No literature review, no novelty claim, no manuscript text.

> **Disclosure that bears on research-integrity and AI-use rules.** The code, documentation, E-report and slides in this repository were
> produced with AI assistance (Claude) in earlier sessions. The numbers were produced by running the code; the prose and implementation were not
> written by you unaided. Check your institution's AI-assistance and authorship policy before deciding how any of this can be used in a paper (see §8).

---

## 1. Project inventory

| Area | Files | Notes |
|---|---|---|
| Data | `data/raw/pima_diabetes.csv`, `provenance.json` | 768 × 9; SHA-256 recorded and **matches** the file |
| Pipeline | `src/data_loader.py`, `preprocessing.py`, `train.py`, `evaluate.py`, `validation.py`, `predict.py`, `explainability.py`, `report_generator.py`, `config.py`; `config/config.yaml` | ~830 lines |
| App | `app.py`, `ui/components.py`, `ui/styles.css` | Streamlit, 5 pages |
| Artifacts | `models/model.joblib`, `metadata.json`; `artifacts/metrics.json`, `data_profile.json`, `model_comparison.csv`, 5 PNG | **No saved test predictions, no split indices, no OOF predictions** |
| Tests | 7 files, 45 tests | Synthetic data only (see §2, row 14) |
| Docs | README, dataset/model cards, methodology, privacy, deployment; E-report (DOCX/PDF, 36 body pp.); slides (15) | Written by AI assistance |
| Env | `requirements.txt` (ranges, not pinned), `requirements-dev.txt`, `Dockerfile` (never built) | No lock file |
| VCS | Git repository exists but has **no commits** | Provenance of code at result time is not recorded |

## 2. Implementation audit

| # | Component | What the code actually does | Existing evidence | Verified? | Problems | Required action |
|---|---|---|---|---|---|---|
| 1 | Data acquisition | `fetch_openml(37)`, renames columns, maps `tested_positive`→1, caches CSV, writes hash | `provenance.json` | **Yes** (hash matches; 268/500; 0 duplicate rows; 0 duplicate feature rows) | No subject IDs, so independence of records cannot be checked | State as an assumption |
| 2 | Outcome variable | `Outcome` = 1 if "tested positive" | Dataset documentation (OpenML text of the UCI file): positive = 2-h post-load glucose ≥ 200 mg/dL **at any survey examination or found during routine care** | **Partly.** Label ↔ documentation confirmed; **timing relative to the features is not documented** | The recorded `Glucose` never reaches 200 (max 199, positives included), so it cannot be the measurement that defined the label. Whether the task is *concurrent status* or *later onset* is unknown. My earlier text ("glucose is partly circular", "model largely re-expresses the criterion") is **not supported** (§3, W1) | Call the target "recorded diabetes status in the dataset"; never "future onset" unless the original study design is found and supports it; correct the report/slides/README wording |
| 3 | Zero → missing | `ZeroToNaN` on Glucose, BP, SkinThickness, Insulin, BMI; Pregnancies untouched | Counts 5 / 35 / 227 / 374 / 11 | **Yes** (counts recomputed) | "Zero = missing" is an inference (documentation says "Missing Attribute Values: None"). 49 % of insulin and 30 % of skin-fold imputed. No sensitivity analysis of the imputation | Treat as an assumption; plan a robustness experiment |
| 4 | Split | `train_test_split(test_size=.2, stratify=y, random_state=42)` — one split | `metadata.json` | **Yes**: 614/154, 214/54 positives; no index or exact-row overlap between train and test | Only 54 test positives; indices not saved | Save split indices; use repeated/nested evaluation |
| 5 | Preprocessing fit | Imputer + scaler inside the sklearn `Pipeline` | Code | **Yes (by execution)**: for all 5 calibration folds the stored imputer medians equal the medians of **that fold's training part**, and differ from both the full-training and full-dataset medians → no leakage through imputer | Scaler assumed to follow the same mechanism (not separately inspected) | None; keep the check as a test |
| 6 | Tuning and model selection | `GridSearchCV`, 5-fold stratified, on training split only; selection = best CV ROC-AUC then simplest within 1 SE | `model_comparison.csv` | **Yes**: LR CV 0.8450 ± 0.0130 recomputed exactly; test set not used | (a) best-of-grid CV score is optimistic; (b) not nested; (c) the same folds are reused for OOF predictions, calibration decision and threshold; (d) top four models are within fold noise and no paired comparison was done | Nested CV or a separate validation scheme for the new experiments; paired comparisons |
| 7 | Calibration | `CalibratedClassifierCV(sigmoid, cv=5)`; final model = average of 5 fold models; kept if OOF Brier improves | `metrics.json` | **Partly**: calibrated OOF Brier 0.1508 recomputed; the raw 0.1602 was taken from the artifact | Sigmoid only; no isotonic or other comparison; no calibration slope/intercept or ECE; test bins hold 19–20 records | Add calibration slope/intercept with CIs; compare calibrators if it serves the research question |
| 8 | Threshold | Largest τ with OOF sensitivity ≥ 0.80 on training split | `metadata.json` (0.2941) | **Yes**: recomputed 0.2941 independently; OOF sens 0.804 / spec 0.700; test set not used | Target 0.80 is arbitrary; OOF scores come from fold models while the deployed model is their average (in-sample sens at τ = 0.799, i.e. no meaningful mismatch); the threshold flags **50 %** of test records | Pre-specify and justify thresholds; report a threshold sweep |
| 9 | Test metrics, confusion matrix | `evaluate.compute_metrics` | `metrics.json` | **Yes, exact** (max abs diff 0.0 over 8 metrics); confusion matrix TN 67, FP 33, FN 10, TP 44 reproduced by sklearn **and** by hand; `classes_ = [0, 1]`; row/column order correct | — | — |
| 10 | Bootstrap CI | Stratified percentile bootstrap, 1000 draws, fixed model and threshold, test set only | `metrics.json` | **Yes (approx.)**: independent code, different seed, 5000 draws → ROC-AUC 0.738–0.874 vs saved 0.735–0.872; others within ≈ 0.01 | CI covers test-sampling noise only (not training variability, split choice or threshold choice); 1000 draws is minimal | Report as "test-set bootstrap CI"; add repeated-split variability |
| 11 | Permutation importance | Test set, 30 repeats, ROC-AUC | `metrics.json` | **Reproduced from artifact only** (not recomputed) | One split; correlated features; no stability across resamples; computed on the test set (descriptive only) | Stability analysis across splits/bootstrap |
| 12 | SHAP local explanations | `shap.explainers.Permutation` on the full pipeline probability, 100-row training background, `max_evals=161`; occlusion fallback on any exception | Unit test (additivity) | **Yes**: method used was SHAP, not the fallback, on all 6 rows tested; additivity error ≤ 8 × 10⁻¹⁶; across 8 seeds contributions varied by ≤ 0.45 percentage points | Only local explanations for illustrative inputs; no global SHAP; faithfulness vs. an exact linear explanation not tested; background choice not varied | If explanations stay in scope: stability + background sensitivity |
| 13 | App ↔ batch consistency | `Predictor.predict` | Tests | **Yes**: 39 accepted test rows gave probabilities identical to batch prediction (max diff 0.0); zero and NaN inputs give identical outputs | App refuses rows with missing BMI (required field) and one dataset row (BP 24 mm Hg < range 30) | Document; not research-critical |
| 14 | Automated tests | 45 pytest tests | Fresh run today: **45 passed** (4.8 s); Ruff: all checks passed | **Yes** | Tests use synthetic data; **none** compares `metrics.json` with a recomputation from predictions, none covers `train.run` or split-leakage invariants | Add result-consistency and leakage tests |
| 15 | Reproducibility | Seeded; metadata stores library versions | README claim "identical results on re-run" | **Yes**: isolated retraining (copy of `src/`, `config/`, data) reproduced CV table, selected model, threshold, confusion matrix and all test metrics with max diff 0.0 (same machine and versions) | Ranges not pinned, no lock file, no commits, no experiment log, no saved predictions | Pin, commit, log, save predictions |
| 16 | Documentation claims | README, model card, E-report, slides | — | **Partly** | See W1 (circularity wording); also "insulin/BP/skin add essentially nothing" is true of *permutation importance*, not of predictive signal in general | Correct wording |

## 3. Confirmed results (independently recomputed today)

| Reported value | Recomputed | Status |
|---|---|---|
| Test n = 154 (54 pos / 100 neg) | 154 (54 / 100) | **Verified** |
| ROC-AUC 0.809 | 0.80870 | **Verified** |
| ROC-AUC 95 % CI 0.735–0.872 | 0.738–0.874 (independent, 5000 draws) | **Verified** (test-set bootstrap, fixed model) |
| Sensitivity 0.815; Specificity 0.670; Precision 0.571 | 0.81481; 0.67000; 0.57143 | **Verified** |
| F1 0.672; Accuracy 0.721; Brier 0.174 | 0.67176; 0.72078; 0.17385 | **Verified** |
| TP 44, FP 33, FN 10, TN 67 | identical (sklearn and by hand) | **Verified** |
| Threshold ≈ 0.294 | 0.2941 recomputed from OOF training predictions | **Verified** |
| CV ROC-AUC of LR 0.845 ± 0.013 | 0.84499 ± 0.01303 | **Verified** |
| 45 tests pass | 45 passed | **Verified** (software behaviour only) |
| Full pipeline reproducible | Identical on isolated retrain | **Verified** (same machine/versions only) |

## 4. Unverified claims
- Permutation-importance values (read from the artifact, not recomputed); raw (uncalibrated) OOF Brier 0.1602.
- Whether any record pair belongs to the same woman (no IDs).
- Timing between feature measurement and the outcome-defining examination (not in the dataset documentation).
- Docker image and cloud deployment (never built).
- Any statement about performance outside this one split (no repeated-split or external evidence exists).

## 5. Potential methodological errors / weaknesses (ranked)

- **W1 — Outcome semantics and an unsupported earlier claim.** The documented label rule (glucose ≥ 200 at *any* examination or in routine care) and the fact that recorded glucose is capped at 199 mean the data are neither a clean "same-measurement" label nor a documented follow-up cohort. Evidence from today: glucose alone gives CV ROC-AUC **0.799 ± 0.034**, glucose + BMI 0.829, glucose + BMI + age 0.837, all eight features **0.845 ± 0.013**, and **all features except glucose still reach 0.768 ± 0.015** (training split, same folds; test set untouched). Glucose is the strongest single predictor, but "the model merely re-expresses the label criterion" is **not** supported, and I withdraw it. Also, 49 % of positives have glucose < 140 mg/dL.
- **W2 — One small split.** 54 test positives; ROC-AUC CI ± 0.07; the top four models are within one fold SD. No conclusion that depends on a single 80/20 split is secure.
- **W3 — Non-nested selection.** Same folds for tuning, OOF, calibration decision and threshold; mild optimism in OOF-based quantities.
- **W4 — Uncertainty is understated.** The bootstrap CI is conditional on one trained model and one threshold.
- **W5 — Threshold choice** (sensitivity ≥ 0.80) is a design choice; the resulting rule flags half the test set with PPV 0.57.
- **W6 — Calibration evidence is thin** (19–20 records per bin; one calibrator; no slope/intercept). Probabilities reflect this sample's 35 % prevalence, not a population risk.
- **W7 — Explanation validity untested across resamples**; permutation importance is a single-split, test-set quantity.
- **W8 — Imputation assumption** (zero = missing; median imputation); missingness may itself be informative; not examined.
- **W9 — Population specificity and no external validation.**
- **W10 — Reproducibility infrastructure gaps** (no saved predictions/indices/OOF scores, no lock file, no commits, no experiment log).

No evidence was found of: test-set use in selection, tuning or threshold choice; preprocessing fitted on test data; label-order errors in the confusion matrix; a SHAP→fallback substitution in the reported example; or train/test row overlap.

## 6. Missing evidence and files needed to proceed

1. **Your institution's AI-assistance / authorship / originality rules** (determines what I may write versus what I may only support — rule 17).
2. Target venue (or permission to shortlist), template, page/word limit, citation style.
3. Original study documentation for the Pima data (e.g. Smith *et al.* 1988 and related cohort papers) **if accessible to you**, to resolve outcome timing (W1). I will search for it in Stage 2, but full texts may be paywalled.
4. Any other diabetes datasets you are permitted to use (for external validation) — none exist in the project.
5. Compute/time budget and whether new experiments may be added to this repository.
6. Decision to commit the repository now, so experiments have a recorded code state.
7. To be created in later stages (not yet existing): saved predictions and split indices, OOF scores, lock file, experiment log, result-consistency tests.

## 7. Preliminary research-readiness assessment

- **Engineering foundation: good.** The reported numbers are correct, leakage checks passed, and the pipeline reproduces exactly.
- **Scientific contribution: not yet established.** Pima + logistic regression/SVM/RF + SHAP + a dashboard is a well-trodden combination; I have **not** done the literature review, so I cannot yet say what is new, but nothing in the current project by itself supports a novelty claim, and I will not invent one.
- **Evidence strength: weak for any performance claim**, because of W2–W4. A paper built on the current single-split result would be a descriptive case study at best.
- **Plausible directions (to be scored in Stage 3, not chosen now):** explanation-stability across resamples (C); calibration/threshold behaviour with proper uncertainty (A, B); robustness to the zero-as-missing assumption and imputation (E); and an honest analysis of what the Pima label can and cannot support (F/G). Each is feasible on this dataset; whether any is *new* depends on Stage 2.
- **Overall:** not ready for drafting; ready to proceed to Stage 2 once the decisions below are made.

## 8. Decisions needed from you

1. **AI-use policy:** may AI write manuscript prose for you, or only provide notes/tables/feedback (so you write the prose)? Which of the existing AI-assisted materials are permitted as your own work?
2. **Wording corrections:** approve correcting the "glucose is circular / re-expresses the criterion" statements in README, model card, E-report and slides.
3. **Approve proceeding to Stage 2 (literature review)** — this uses web search and will take a while.
4. **Commit the repository now?** (recommended; no commits exist).
5. Venue preference, if you have one.

## 9. Exact next steps (after your approval)
1. Commit current state; add pinned lock file; save split indices and test predictions from the existing model (no retraining needed).
2. Stage 2: focused literature search with a verified evidence matrix and a research-gap statement.
3. Stage 3: score candidate contributions; recommend one primary question; seek your approval before any new experiments.
