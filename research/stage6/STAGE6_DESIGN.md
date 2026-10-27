# Stage 6 — Experimental design (design only; no experiment code written or run)

Date: 27 Oct 2026 · Primary RQ approved by you: **H2 — label-aware imputation as a leakage source (quantify the inflation; detect it)**, with a **simulation** included.
Companion files: `PREREG_DRAFT.md` (hypotheses, decision rules, stop rules — to be frozen on your sign-off), `experiment_matrix.csv` (factor levels and run counts).

## 0. Scope, and how the AI-code question is handled

- You left the AI-code answer as the placeholder "[state yes or no …]". **I am treating it as "no" until you state it explicitly.** This stage needs no code, so nothing is blocked now.
- This document is written as a **specification** that a human (you) can implement, including test specifications (§10). If you later answer "yes", I can implement from it; if "no", I can review your code, check results against the plan, and prepare tables/figure specifications.
- Existing AI-written scripts in the repository (`research/stage1_verify.py`, `research/stage3/pilot_label_aware_imputation.py`) were exploratory/audit tools. Decide with your institution whether they may be mentioned or reused; the final experiments should not depend on them.
- No manuscript prose is provided here, only a design.

## 1. Map: questions → experiments → hypotheses → outputs

| RQ | Experiment | Data | Hypotheses | Main outputs |
|---|---|---|---|---|
| Primary | **Exp 1** Inflation on real Pima | Pima (768) | H1-H4 | App/Dep metrics by regime × model |
| Primary | **Exp 2** Label-permutation canary | Pima, simulation | H6 | Detection rates (TPR/FPR) |
| RQ-2 | **Exp 3** Diagnostics: importance and calibration | derived from Exp 1 | H7 | LAS, calibration slope/intercept |
| RQ-1 | **Exp 4** Controlled simulation | synthetic (labelled as such) | H5 (+H2 replication) | Dose-response curves |
| (conditional) | **Exp 5** Replicate published pipelines as described | Pima | none pre-specified | Reproduced vs reported AUC |

Exp 5 is **conditional** on your full-text reading of the three studies (§15).

## 2. Data and splitting strategy

**2.1 Real data.** Pima Indians Diabetes Database as already loaded by the project (768 rows; SHA-256 recorded in `data/raw/provenance.json`). Impossible zeros in Glucose, BloodPressure, SkinThickness, Insulin, BMI are converted to missing; zeros in Pregnancies are valid. Outcome treated as *recorded diabetes status* (not future onset) until Smith 1988 is read.

**2.2 Why all 768 rows and no extra hold-out.** The study estimates *contrasts between preprocessing regimes*, not the performance of a selected model. Nothing is tuned, selected or thresholded on any held-out data (fixed settings, §4), so there is no selection step that a final untouched test set must protect. Using all rows with repeated splitting gives much more stable contrast estimates than the 154-row split of the earlier project. The earlier 154-row split (seed 42) was used for reporting in the earlier project and for audit checks, so it is **not** reserved as a confirmatory set here; this is disclosed.

**2.3 Split scheme (paired).**
- **J = 100 repeated stratified random 80/20 splits** (614 train / 154 test, stratified by outcome). Split seeds come from `numpy.random.SeedSequence(master).spawn(J)`; the **same 100 splits are used for every regime and model** (pairing).
- Regimes are implemented relative to each split exactly as defined in `PREREG_DRAFT.md` §2 (Reg-1 and Reg-3 use global statistics computed on all 768 rows with the raw zero-to-missing data; Reg-0, Reg-2 and Reg-4 use only the training part).
- For each fitted model, two evaluations on the same 154 held-out rows: **App** (regime's own imputation rule) and **Dep** (label-free training medians).
- **Negative control B:** the same machinery on the **complete-case subset** (rows with no impossible zeros); all regimes must coincide exactly.

**2.4 Why repeated random subsampling rather than k-fold CV.** The Nadeau-Bengio variance correction (§6) is defined for repeated random train/test subsampling and gives a transparent, conservative CI. Splits are *not* independent samples; they are Monte-Carlo replicates on one finite dataset.

**2.5 Simulation data** (§8): each replicate is an independent synthetic dataset (so replicates *are* independent), plus a large independent test sample from the same generator to obtain "true deployment" performance. Synthetic data are labelled synthetic and make no clinical claim.

## 3. Preprocessing (identical across regimes except the imputer)
- Zero-to-missing rule for the five columns only; then the regime's imputer; then standardisation (fit on training rows only, all regimes, applied to held-out rows).
- No resampling (SMOTE), no feature selection, no engineered features, no outlier clipping (all of these are known to interact with leakage and would confound the contrast; listed as limitations).
- Missing-indicator columns are **not** added (a separate question, optional extension).

## 4. Models and fixed settings (not tuned)

| Model | Fixed setting | Why |
|---|---|---|
| LR | `LogisticRegression(C=1.0, max_iter=5000)`, no class weights | Linear reference; pilot suggested small inflation |
| RF-default (**primary**) | `RandomForestClassifier(n_estimators=300, defaults otherwise)` | High capacity: can memorise imputed constants |
| RF-regularised | `n_estimators=300, max_depth=5, min_samples_leaf=8` | Capacity contrast within one family |
| HGB | `HistGradientBoostingClassifier(defaults)` | Boosting family; handles NaN natively but receives imputed values here |
| SVM-RBF | `SVC(C=1, gamma="scale")` with probability via sigmoid wrapper (`CalibratedClassifierCV`, `ensemble=False`, cv=3) | Kernel family |

All random seeds fixed per split. These settings are chosen *a priori* from library defaults and the earlier pilot; no setting is selected using outcome data in this study. A capacity sweep for RF (depth ∈ {2, 4, 8, None}) is included in Exp 4 only.

## 5. Metrics and definitions
- **ROC-AUC**, **PR-AUC** (average precision), **Brier** = mean (p̂ − y)².
- **Calibration intercept and slope:** fit `logit P(y=1) = a + b·logit(p̂)` on the held-out predictions (clip p̂ to [1e-6, 1−1e-6]); ideal a = 0, b = 1.
- **Sensitivity / specificity** at two thresholds fixed *a priori*: τ = 0.5 and τ = training prevalence (≈ 0.349). No threshold is tuned.
- **Leak-feature attribution share (LAS)** = (permutation importance of Insulin + SkinThickness) ÷ (sum of positive importances), where permutation importance is the mean ROC-AUC drop over 10 shuffles of a feature on the 154 held-out rows (App evaluation).
- **Paired contrasts:** differences computed within each split and model (E1-E4 in `PREREG_DRAFT.md` §3).
- **Canary statistic (Exp 2):** mean held-out ROC-AUC across permutations of the outcome labels (global permutation before the regime is applied); flag rule in §7 (Exp 2).

## 6. Statistical analysis plan
1. **Effect sizes first.** Report each contrast as mean ± SD over the J = 100 splits, plus a corrected 95 % CI.
2. **Nadeau-Bengio corrected variance for repeated random subsampling** (do not treat splits as independent):
   `Var_corrected(mean Δ) = (1/J + n_test/n_train) · s²`, where `s²` is the sample variance of the per-split paired differences and `n_test/n_train = 154/614 ≈ 0.25`. CI = mean ± t(J−1, 0.975) · sqrt(Var_corrected).
3. **What this implies (an honest warning):** the correction is dominated by the `n_test/n_train` term, so more splits do not shrink the CI beyond a floor. If the per-split SD of the paired ΔAUC is about 0.02 (a guess; to be measured in the dry run), the CI half-width is about ±0.02. Then an effect near 0.10 (RF) would be conclusive against the SESOI of 0.02, but an effect near 0.03 (LR) would probably remain **inconclusive** on real data. This is why the simulation (independent datasets, ordinary SEs) carries the model-dependence claim.
4. **Multiplicity.** One confirmatory hypothesis (H1). H2-H4 and H6 form a secondary family controlled with Holm's method; H5 and H7 are reported descriptively. Everything else is labelled exploratory.
5. **Simulation:** replicates are independent, so use the mean ΔAUC with SE = s/√n_rep and percentile bootstrap CIs; show full distributions.
6. **Canary evaluation:** detection rate with Wilson 95 % CIs, noting dependence among splits; ROC-style summary of the canary as a classifier of "leaky vs valid" across splits and models.
7. **No** fold-wise or split-wise significance tests presented as independent evidence; **no** conflation of statistical significance with clinical usefulness; no clinical claims.

## 7. Per-experiment specifications

### Exp 1 — Inflation on real Pima (primary)
- **RQ / hypotheses:** primary RQ; H1 (confirmatory), H2-H4.
- **Independent variables:** regime (Reg-0..3; Reg-4 exploratory) × model (5).
- **Dependent variables:** App and Dep ROC-AUC, PR-AUC, Brier, calibration a/b, sens/spec at two thresholds; contrasts E1-E4.
- **Dataset / split:** Pima, J = 100 paired stratified 80/20 splits (§2).
- **Preprocessing / baseline:** §3; baseline = Reg-0.
- **Hyperparameters / seeds:** §4; split seeds spawned from one master seed recorded in the config.
- **Outputs:** per-split per-row predictions (App and Dep), metrics table, contrasts with corrected CIs.
- **Confounders:** model capacity; the fraction of imputed cells (fixed by the data); stratification; RF randomness (fixed seeds).
- **Acceptance:** stop-rule gates pass (`PREREG_DRAFT.md` §6); metrics recompute from saved predictions; H1 decided by the preset rule.
- **Limitations:** one dataset; fixed hyperparameters; emulation of described practice, not authors' code.

### Exp 2 — Label-permutation canary
- **RQ / hypothesis:** can leakage be detected without knowing the true effect; H6.
- **Design:** for each (regime × model), on 10 of the 100 splits: **100 label permutations** (permute outcome labels globally, then apply the regime and the split exactly as in Exp 1, compute held-out AUC). Repeat on simulated datasets at several missing fractions (Exp 4 grid, reduced).
- **Flag rule (pre-specified):** let `μ0, σ0` be the mean and SD of permuted-label AUC for **Reg-0** of that model. A pipeline is **flagged** if its mean permuted-label AUC > `μ0 + 2σ0`.
- **Outputs:** permuted-label AUC distributions; TPR (Reg-2/3 flagged) and FPR (Reg-0/1 flagged) per model and per missing fraction.
- **Confounders:** the canary needs a model flexible enough to exploit the leak (expect low power for LR); the number of permutations.
- **Acceptance:** Reg-0 gate (mean within 0.5 ± 0.02).
- **Limitations:** requires access to the full pipeline code; detects *label use*, not every kind of leakage.

### Exp 3 — Diagnostics: importance and calibration
- **RQ / hypothesis:** RQ-2; H7 (exploratory).
- **Design:** no new fits; permutation importance (10 shuffles) and calibration a/b on Exp 1's held-out predictions; LAS per regime/model; also LR standardised coefficients.
- **Output:** how LAS and calibration slope differ between valid and leaky regimes; whether either separates them (AUC of the diagnostic as a classifier of regime across splits).
- **Limitations:** exploratory; diagnostics measured on the leaky held-out rows by construction.

### Exp 4 — Controlled simulation
Specification in §8. **Hypotheses:** H5, replication of H2 with independent replicates. Includes negative control A (0 % missing).

### Exp 5 — Replicate published pipelines as described (conditional)
Only after you report the three studies' imputation order and use of labels. Re-implement each pipeline *as described* (labelled "our reading"), report reproduced vs reported performance, and no accusation of error unless the text itself shows a violation (e.g., imputation before the split using labels).

## 8. Simulation specification (synthetic data; no clinical claims)
- **Features:** 8 features from a multivariate normal with a correlation matrix estimated from Pima's complete cases (parameters only; no rows copied), then standardised.
- **Outcome:** `y ~ Bernoulli(sigmoid(b0 + κ·β'x))`, β = the Stage-1 standardised LR coefficient pattern (Glucose largest, BMI, Pregnancies, …); κ chosen by calibration on a very large auxiliary sample so that the **oracle (complete-data) AUC** equals the target; `b0` set for prevalence 0.35.
- **Missingness:** features 4 and 5 (mimicking skin-fold and insulin) missing at fraction π; features 2, 3, 6 (glucose, BP, BMI) at 3 %; others 0 %. **Mechanism:** MCAR, or mild outcome-dependent MNAR (odds of missingness multiplied by 1.5 for positives, rescaled to keep overall π).
- **Factors:** π ∈ {0, 0.10, 0.25, 0.50, 0.75}; mechanism ∈ {MCAR, MNAR}; oracle AUC ∈ {0.70, 0.80, 0.90}; n ∈ {768, 5000}; regimes Reg-0..3; models LR, RF-default, HGB (+ RF depth sweep at n = 768, MCAR, π = 0.5); replicates = 50 per cell.
- **Truth:** for each fitted pipeline, **deployment AUC** on a fresh synthetic test sample of 20,000 rows generated with the same missingness mechanism and imputed label-free with training medians; also the oracle AUC on complete data. Inflation = App − Dep; harm = Dep(r) − Dep(Reg-0).
- **Negative control A:** π = 0 (no missing cells): all regimes must be identical.
- **Why this carries RQ-1:** independent replicates allow ordinary CIs, a known truth, and dose-response in π and model capacity, which the single real dataset cannot provide.

## 9. Compute estimate (rough, NOT measured; to be measured in the dry run)

| Experiment | Fits (approx.) | Comment |
|---|---|---|
| Exp 1 | 4 regimes × 5 models × 100 splits = 2,000 (+500 for Reg-4) | minutes to ~30 min on a laptop CPU |
| Exp 2 | 4 × 5 × 10 splits × 100 permutations = 20,000 (+ simulation subset) | tens of minutes to a few hours; parallelisable |
| Exp 3 | no new fits; permutation importance 10 × 8 per fit | small |
| Exp 4 | 5 π × 2 mech × 3 AUC × 2 n × 4 regimes × 3 models × 50 reps = 36,000 (+ RF sweep) | RF at n = 5000 dominates; trim reps or π levels if over budget |

If a budget is exceeded, trim by reducing replicates, not by dropping controls.

## 10. Test specifications (to be implemented before any experiment is run)
1. **Label-isolation:** under Reg-0, Reg-1, Reg-4 the imputed feature matrix is unchanged when outcome labels are permuted; under Reg-2 and Reg-3 it changes.
2. **Scope-isolation:** under Reg-0, Reg-2, Reg-4, modifying the held-out rows' features cannot change the training-row imputed values or fitted statistics; under Reg-1 and Reg-3 it can.
3. **Split integrity:** strata preserved; train/test disjoint; same split indices reused across regimes and models; seed → identical splits.
4. **Metric references:** tiny hand-computed examples for AUC, PR-AUC, Brier, calibration slope/intercept, sensitivity/specificity.
5. **Determinism:** the same seed reproduces predictions bit-for-bit; changing the seed changes them.
6. **Negative controls:** complete-case subset (real) and π = 0 (simulation) yield identical predictions across regimes.
7. **Canary on noise:** on data with no missing values, canary AUC ≈ 0.5 for all regimes and models.
8. **Generator checks:** achieved prevalence and oracle AUC within tolerance; missing fractions match π; MNAR shows outcome dependence; MCAR does not.
9. **Round trip:** metrics recomputed from saved per-row predictions equal the saved metrics.

## 11. Execution checklist and gates
- **G0** Policy answered; RQ and this design approved by you.
- **G1** Environment pinned (lock file), code state committed and tagged; data hash verified.
- **G2** Pre-registration frozen: `PREREG_DRAFT.md` committed and tagged `prereg-v1`.
- **G3** Test suite (§10) passes.
- **G4** Dry run on 5 splits and 3 simulation cells; measure runtime; confirm SD of paired ΔAUC for the CI-width estimate; check no leakage-test failures.
- **G5** Full runs with logs; stop-rule gates monitored.
- **G6** Consistency audit: recompute metrics from predictions; reproduce one cell from scratch.
- **G7** Regenerate all tables/figures from saved result files only.
- **G8** Final technical and academic audit (Stage 11).

## 12. Output-file structure (proposed)
```
research/leakage_study/
  README.md                      how to run each experiment and verify results
  configs/                       exp1_pima.yaml, exp2_canary.yaml, exp4_simulation.yaml, master_seed.yaml
  src/                           regimes, splits, models, metrics, canary, simulate, run_exp*
  tests/                         the nine test groups in §10
  environment/                   lockfile, python/package versions, hardware, git commit/tag
  results/exp1/                  predictions (per split/regime/model/row), metrics.csv, contrasts.csv, importance.csv, summary.json
  results/exp2/                  permuted_auc.csv, detection.csv
  results/exp3/                  diagnostics.csv
  results/exp4/                  runs.csv, contrasts.csv, truth_auc.csv
  figures/                       generated only from results/*; each with a data file
  logs/                          run logs with timestamps and seeds
```

## 13. Reproducibility requirements
- Single master seed in a config file; all seeds derived with `SeedSequence.spawn`; every output records the seed, config hash, commit hash and package versions.
- Pinned dependencies (a lock file), Python version recorded, hardware recorded.
- Data integrity: SHA-256 of the CSV checked at start; raw data never modified.
- Deterministic parallelism (fixed per-task seeds; results independent of worker count).
- Per-row predictions saved so any metric, interval or figure can be regenerated without re-fitting.
- Every figure/table has a script and a source data file; no manual edits to plotted values.

## 14. Planned figures and tables (each tied to a question and a source file)
- **Fig 1** Design schematic: 2 × 2 (label use × statistics scope) plus App vs Dep evaluation. *(RQ primary; drawn from the design)*
- **Fig 2** App vs Dep ROC-AUC by regime × model with corrected CIs. *(Exp 1; `results/exp1/contrasts.csv`)*
- **Fig 3** Dose-response: ΔAUC vs missing fraction by model and mechanism. *(Exp 4)*
- **Fig 4** Permuted-label AUC distributions per regime/model. *(Exp 2)*
- **Fig 5** LAS and calibration slope by regime. *(Exp 3)*
- **Tables:** regimes; Exp 1 contrasts; decomposition (label, scope, interaction); canary TPR/FPR; threats to validity.

## 15. Threats to validity and open items
**Threats:** one real dataset; fixed (untuned) models; emulation of described practice, not the authors' code; "group" may mean something other than outcome class in some studies; Pima label semantics unresolved (timing); the earlier project's test split reused in preparation work; effects for LR may be inconclusive; synthetic data cannot capture all real structure; the pilot informed the SESOI and regime definitions.

**Open items that can change the design:**
1. **Your full-text findings** for `msys`, `pima_leaksafe`, Khan 2026: order of imputation, whether labels are used for test rows, meaning of "group". If any study uses something else (e.g., imputation by class *after* the split with train labels only), add or modify a regime.
2. **Smith 1988:** outcome definition and time window; this affects only how the target is described, not the regimes.
3. **Compute budget** and the exact `J`, replicates and grid after the dry run.
4. Whether to add the **optional extensions** (honest-imputer comparison, SMOTE interaction, external dataset); currently excluded.
5. **AI-code policy answer** (§0).

## 16. What happens next
On your approval: (a) you answer the policy question; (b) we freeze `PREREG_DRAFT.md` (tag `prereg-v1`); (c) Stage 7 starts with the test suite and the dry run. No experiment is run until G0-G4 are satisfied.
