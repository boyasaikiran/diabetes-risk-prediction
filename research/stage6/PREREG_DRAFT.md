# Pre-registration — label-aware imputation leakage (H2)

**Status: FROZEN as `prereg-v1` on 27 Oct 2026** (approved by the student). Frozen together with `STAGE6_DESIGN.md` and `experiment_matrix.csv` (hashes in `PREREG_FREEZE.txt`). No experiment had been run when this was frozen. Any later change must be a **dated amendment** appended in §9, never a silent edit. The file keeps its original name so that earlier references remain valid.

**AI-assistance disclosure.** The experiment code and tests for this study are written with AI assistance (Claude) with the student's approval under the student's institutional rule; the manuscript prose is written by the student.

**Disclosure of how this plan arose (forking paths).** The idea came from reading three Pima studies that describe outcome-conditional median imputation and report ROC-AUC ≈ 0.93–0.96 (abstract-level; full texts not yet read by us), and from an exploratory pilot on the *training split only* (RF ROC-AUC 0.840 → 0.938 under a leaky pipeline; permuted-label canary 0.49 vs 0.857). The size of the smallest effect of interest below was chosen knowing the pilot. The 154-row test split of the earlier project was never used for the pilot.

## 1. Research questions
- **Primary RQ.** How much does outcome-conditional imputation of the Pima impossible zeros inflate discrimination, calibration, thresholded metrics and explanation output compared with leakage-safe imputation; how does this depend on model family and on the fraction of missing values; and can a label-permutation canary detect it?
- **RQ-1 (model dependence, simulation).** Does inflation scale with missing fraction and model flexibility when the truth is known?
- **RQ-2 (diagnostics).** Do importance and calibration outputs reveal the leak?
- **Not in scope (optional extension only if you approve later):** comparison of honest imputers (median, MICE, missing-indicator); resampling (SMOTE) interactions; fairness; external datasets.

## 2. Imputation regimes (the manipulated factor)
Two crossed binary factors plus one optional regime. "Label-aware" means the imputed value depends on the row's outcome.

| Regime | Statistics fitted on | Uses the held-out row's true label? | Describes |
|---|---|---|---|
| **Reg-0 (valid reference)** | training part only | No | Leakage-safe: label-free median, refit inside each split |
| **Reg-1 (scope leak only)** | all rows, before splitting | No | Label-free median computed globally, then split (mild "preprocessing before split") |
| **Reg-2 (label leak only)** | training part only | **Yes** | Class medians from training rows; each held-out row filled with the median of its **true** class |
| **Reg-3 (both; "group median before split")** | all rows, before splitting | **Yes** | The practice described in the three studies |
| **Reg-4 (optional, exploratory)** | training part only | No (uses a *predicted* class) | Deployable pseudo-label variant: held-out class predicted from observed features only |

Each fitted model is evaluated two ways:
- **Apparent evaluation (App):** held-out rows imputed *by the regime's own rule* (what a researcher using that pipeline would see).
- **Deployment evaluation (Dep):** held-out rows imputed with the **label-free training medians** (what would happen on new patients whose label is unknown). For Reg-0 and Reg-1, App ≈ Dep.

## 3. Estimands (all paired within split and model)
Let `AUC_App(r)` and `AUC_Dep(r)` be held-out ROC-AUC under regime `r`.
- **E1 Apparent inflation (primary):** `AUC_App(Reg-3) − AUC_App(Reg-0)`.
- **E2 Deployment gap:** `AUC_App(r) − AUC_Dep(r)` for the same fitted model.
- **E3 Harm to deployment:** `AUC_Dep(r) − AUC_Dep(Reg-0)`.
- **E4 Decomposition:** label effect = `App(Reg-2) − App(Reg-0)`; scope effect = `App(Reg-1) − App(Reg-0)`; interaction = `App(Reg-3) − App(Reg-2) − App(Reg-1) + App(Reg-0)`.
- Same contrasts for PR-AUC, Brier, calibration intercept/slope, sensitivity and specificity at pre-specified thresholds, and the explanation measure (§5).

## 4. Hypotheses and decision rules
Smallest effect of interest (SESOI) for ROC-AUC: **0.02** (disclosed as pilot-informed). "Credible" = the Nadeau–Bengio-corrected 95 % CI (see Design §6) excludes the stated bound.

| ID | Hypothesis | Confirmed if | Refuted if |
|---|---|---|---|
| **H1 (primary, confirmatory)** | Reg-3 inflates apparent ROC-AUC of **RF-default** on Pima by more than the SESOI | lower CI bound of E1 (RF-default) > 0.02 | upper bound < 0.02 |
| H2 | Inflation is larger for flexible models than for LR | E1(RF-default) − E1(LR) > 0 with CI excluding 0 | CI includes or is below 0 |
| H3 | The **label** factor, not the statistics scope, drives most of the inflation | label effect > scope effect, interaction small | otherwise |
| H4 | Reg-3 and Reg-2 raise the deployment gap; Reg-0 and Reg-1 do not | E2 lower bound > 0.02 for Reg-2/3 (RF), E2 within ±0.02 for Reg-0/1 | otherwise |
| H5 (simulation) | Inflation is ≈ 0 at 0 % missing and increases with missing fraction | monotone trend, E1 at 0 % within ±0.005 | otherwise |
| H6 | The permutation canary flags Reg-2/3 for flexible models (TPR ≥ 0.90) and does not flag Reg-0/1 (FPR ≤ 0.05) | thresholds met | otherwise (report TPR/FPR honestly) |
| H7 (exploratory, no direction asserted) | Importance share of heavily imputed features (Insulin, SkinThickness) and calibration slope differ between valid and leaky regimes | descriptive | — |

**Expected limitation, stated in advance:** for logistic regression the effect may be below the SESOI and the canary may have low power. Those are results to report, not problems to fix.

## 5. Primary and secondary outcomes
- Primary: ROC-AUC (E1, RF-default, Pima).
- Secondary: PR-AUC; Brier; calibration intercept and slope (logistic recalibration on held-out logits); sensitivity/specificity at (a) τ = 0.5 and (b) τ = training prevalence; leak-feature attribution share (LAS) = permutation-importance of {Insulin, SkinThickness} ÷ sum of positive importances (held-out rows, 10 repeats, AUC loss).

## 6. Stop rules and validity gates (any failure stops the run and is reported)
1. Reg-0 permuted-label AUC must have mean within 0.5 ± 0.02 for every model.
2. Negative control A: in the simulation with 0 % missing cells, all regimes must give identical predictions (max |ΔAUC| < 1e-9).
3. Negative control B (real data): on the complete-case subset of Pima (no zeros in the five columns), all regimes must coincide exactly.
4. Unit tests proving which regimes read labels and which fit on all rows (Design §10) must pass.
5. Every reported metric must be recomputable from the saved per-row predictions.

## 7. Analysis commitments
- No hyperparameter tuning, feature selection or threshold selection on any held-out data; all model settings are fixed in advance (Design §4).
- All planned runs are reported, including null or unfavourable ones.
- Fold- or split-wise p-values are not used as independent evidence; inference uses corrected variance (Design §6).
- Exploratory analyses are labelled as exploratory.

## 8. Fixed run parameters (frozen before any run)
- **Master seed for all full runs: `20261027`.** All split, permutation, simulation and model seeds are derived from it with `numpy.random.SeedSequence.spawn`. The **dry run uses a different master seed (`1`)**, which is never reused for a reported result.
- Real data: `J = 100` paired stratified 80/20 splits of all 768 rows; the model settings in `STAGE6_DESIGN.md` §4.
- Canary: 10 splits × 100 label permutations per regime × model; flag rule `mean permuted AUC > mu0 + 2·sigma0` (Reg-0 reference).
- Simulation: the grid in `experiment_matrix.csv`, 50 replicates per cell, truth sample of 20,000 rows.
- Software is pinned via `research/leakage_study/environment/requirements.lock.txt`, captured before the dry run.
- The dry run may be used only to check runtime, test-suite health and the per-split SD of paired differences for planning the CI width. **It may not be used to change hypotheses, regimes, models, SESOI, thresholds or decision rules.**

## 9. Amendment log
*(empty at freeze)*
