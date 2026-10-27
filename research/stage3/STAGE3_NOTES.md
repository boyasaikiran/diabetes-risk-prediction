# Stage 3 — Choosing a defensible contribution (notes, not manuscript text)

Date: 27 Oct 2026 · You asked for: a **methodological** contribution; focus on **C** (explanation stability) and **E** (robustness to missingness); an honest novelty verdict.
Files: `direction_scores.csv` (all scores), `score_directions.py`, `pilot_label_aware_imputation.py` + `pilot_results.json`, `discover3.py`, `discover3b.py`, `verify3.py`, `sources3_verified.json`.

## 0. Bottom line (read this first)

1. **Neither C nor E, as you framed them, supports a novelty claim.** Both are already covered well enough that an honest paper could not say "novel", "first" or "gap" about them.
   - **C** (explanation stability): crowded (Pima-specific work exists) and, for logistic regression, close to trivial by construction (§4).
   - **E** (robustness to missingness): the general method is well studied in clinical prediction; only a Pima-specific *application* would remain (§5).
2. **One refinement of E does look defensible, and it came from the literature, not from my wish for a result:** several Pima studies describe **outcome-conditional ("group"/"class-conditional") median imputation of the impossible zeros** and report ROC-AUC of 0.93-0.96, versus 0.83-0.85 in leakage-safe studies. I call this **H2: label-aware imputation as a leakage source — quantify the inflation, and detect it.**
3. **What it could honestly be:** an *evaluation-methodology* contribution (a controlled quantification, a label-permutation canary diagnostic, and a recommended protocol), with a **narrow** novelty claim at best, namely "we quantify X", not "we discovered leakage". Whether even that is new is **not proven**: my searches found no prior quantification, but they are not exhaustive and I have not read the full texts of the studies involved.
4. **Your institution wants a methodological contribution.** H2 is the only direction I scored that is both reasonably original *and* methodological. If you would rather not take it, the honest alternative is a replication/audit paper (H1), which may not meet the "methodological" expectation.

## 1. What changed since Stage 2

- Targeted overlap searches for C and E found substantial prior work (§4-5). Newly verified sources: `hypclass`, `attrimp`, `stablerank`, `rashomon_jbhi`, `multiplicity_aaai`, `intervalshap`, `uncert_afa`, `sisk2023`, `jce2024imp`, `sim2025`, `sperrin2020`, `bremen2026`, `pima_leaksafe`, `knn_imp_bmcmrm`, `reportmethods2012` (metadata and abstracts in `sources3_verified.json`; still abstract-level only).
- Reading `pima_leaksafe` (Ali *et al.* 2025) showed a pattern worth testing (§5).
- Direction H split in two: **H1** (reporting audit) and **H2** (label-aware imputation leakage).

## 2. Rubric (explicit; challenge any score)

Scale 1-5, 5 = best for us. Weights sum to 100.

| Criterion | Weight | A score of 5 means |
|---|---|---|
| Evidence that a gap exists | 15 | Searches found no study doing this; reasons to expect a real gap |
| Low overlap with existing work | 20 | No close prior publication found (5) ... several close works (1) |
| Scientific importance | 10 | Changes how the community should evaluate/interpret results |
| Technical feasibility | 10 | Doable with existing code and data |
| Low computational cost | 5 | Minutes on a laptop CPU |
| Low extra-data requirement | 5 | No new dataset needed |
| Statistical validity achievable | 10 | Clear design supports credible inference despite n = 768 |
| Low risk of inconclusive/trivial result | 10 | Result informative whichever way it falls |
| Suitability for a student conference paper | 5 | Scope fits a short paper |
| Methodological (not merely applied) contribution | 10 | Contributes a protocol, diagnostic or evaluation method |

**Caveats on the scoring.** Scores are my judgements from abstracts. H2 was defined *after* I saw the pilot, so it is the score most exposed to confirmation bias; please test it with the sensitivity check and with your own reading. The overlap criterion relies on searches that are not exhaustive.

## 3. Scores

| Dir. | Direction | Evidence that a gap exists | Low overlap with existing work | Scientific importance | Technical feasibility | Low computational cost | Low extra-data requirement | Statistical validity achievable | Low risk of inconclusive/trivial result | Suitability for a student conference paper | Methodological (not merely applied) contribution | **Weighted /5** | Rank (baseline / equal / novelty-heavy) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| H2 | Label-aware imputation as a leakage source: quantify inflation and detect it (canary diagnostic) | 3 | 4 | 4 | 5 | 5 | 5 | 4 | 4 | 5 | 3 | **4.00** | 1 / 1 / 1 |
| E | Robustness to missingness / perturbation (as originally defined) | 3 | 2 | 3 | 5 | 5 | 5 | 4 | 3 | 4 | 3 | **3.35** | 2 / 2 / 3 |
| H1 | Reporting/leakage audit of Pima-based ML papers | 3 | 4 | 3 | 3 | 5 | 3 | 3 | 3 | 3 | 2 | **3.20** | 3 / 6 / 2 |
| B | Decision-threshold trade-off analysis | 2 | 2 | 3 | 5 | 5 | 5 | 3 | 3 | 4 | 2 | **3.00** | 4 / 3 / 5 |
| A | Calibration-aware risk estimation | 2 | 1 | 3 | 5 | 5 | 5 | 3 | 3 | 4 | 2 | **2.80** | 5 / 4 / 7 |
| C | Explanation stability (local SHAP / importance) | 3 | 1 | 3 | 4 | 4 | 5 | 3 | 2 | 4 | 3 | **2.80** | 6 / 5 / 6 |
| F | Why Pima results may not generalise (documentary + external) | 3 | 3 | 4 | 2 | 5 | 1 | 2 | 2 | 2 | 2 | **2.65** | 7 / 9 / 4 |
| D | Multi-family performance + calibration comparison | 1 | 1 | 2 | 5 | 4 | 5 | 4 | 4 | 4 | 1 | **2.60** | 8 / 7 / 8 |
| G | Integrated reproducible evaluation framework | 1 | 1 | 2 | 4 | 4 | 5 | 3 | 3 | 3 | 2 | **2.35** | 9 / 8 / 9 |

**Rank robustness.** H2 ranks first under all three weightings; E is 2nd/2nd/3rd; C is 6th/5th/6th. H1 moves a lot (3rd / 6th / 2nd) because it depends on how much weight "novelty" gets and it is a meta-research design.

Per-direction justification:

- **A — Calibration-aware risk estimation:** Calibration-focused Pima work already exists (calib_first_rs preprint, leakfree_rs preprint, reliab_aware). Calibration is under-reported in general (christodoulou 79%), but that is not a Pima gap.
- **B — Decision-threshold trade-off analysis:** thresh_math sweeps thresholds 0.30-0.70 on Pima with repeated leakage-free CV; wynants2019 argues thresholds are ad hoc. Screening-sensitivity-target thresholds with uncertainty not seen, but incremental.
- **C — Explanation stability (local SHAP / importance):** Heavily covered: jaimlnn (permutation importance on Pima, resampling), zenodo_shap, attrimp/hypclass/stablerank preprints, JBHI Rashomon, krishna, alvarez. For logistic regression, interventional SHAP is analytic (beta_j x (x_j - background mean)), so stability is expected to be high and the result trivial.
- **D — Multi-family performance + calibration comparison:** Already done repeatedly (aposta, leakfree_rs, jaimlnn, etasr); christodoulou shows LR is competitive in general.
- **E — Robustness to missingness / perturbation (as originally defined):** General clinical-prediction missing-data methodology is strong (sisk2023, jce2024imp, sim2025, sperrin2020); explainability under imputation has a Twente conference paper and a 2026 thesis; msys studied Pima zeros. Only a Pima-specific application would remain.
- **F — Why Pima results may not generalise (documentary + external):** Needs external datasets with compatible features (none in the project) and the 1988 paper's full text for outcome timing (unread). Cross-dataset work exists but with different feature sets (aposta).
- **G — Integrated reproducible evaluation framework:** leakfree_rs, aposta, etasr, reliab_aware already present 'frameworks'; integration alone is not a defensible novelty claim.
- **H1 — Reporting/leakage audit of Pima-based ML papers:** No Pima-specific audit found (search not exhaustive); audits exist elsewhere (kapoor, christodoulou). Needs systematic search + full texts; meta-research rather than a method, which may not satisfy a 'methodological contribution' expectation.
- **H2 — Label-aware imputation as a leakage source: quantify inflation and detect it (canary diagnostic):** Three Pima studies describe outcome-conditional imputation (msys 'group median'; pima_leaksafe 'class-conditional medians'; Khan 2026 'group-median') and report AUC 0.93-0.956, far above leakage-safe 0.83-0.85; no study quantifying this mechanism was found (not exhaustive). Exploratory pilot (training split only): RF AUC 0.840 -> 0.938 with the leaky pipeline; label-permutation canary 0.49 (valid) vs 0.857 (leaky).

## 4. Focus on C — explanation stability

**Verdict: no novelty claim supported; high risk of a trivial or null result.**

- **Existing work (abstract-level):**
  - `jaimlnn` (2026): permutation-importance stability across five classifiers on Pima, WDBC and Cleveland, 10×5-fold CV; Pima stability 0.70-0.87; LR 0.90 falls to 0.68 with 25 % of the training data. This is nearly your direction C.
  - `zenodo_shap` (2024, repository record): SHAP stability under class imbalance on Pima.
  - `reliab_aware` (2026): cross-model SHAP agreement (Feature Consistency Index).
  - General ML: SHAP rankings change with retraining across 77 datasets (`attrimp`, preprint); accurate models disagree on attribution by hypothesis class (`hypclass`, preprint); top-10 shortlist instability (`stablerank`, materials domain); Rashomon-set explanations for medical data (`rashomon_jbhi`, JBHI 2024); predictive multiplicity in probabilistic classification (`multiplicity_aaai`, AAAI 2023).
- **Why it is nearly trivial for our model:** for a linear model with an independent background, interventional SHAP in log-odds is analytic: `phi_j = beta_j * (x_j - mean_bg(x_j))`. Local stability then reduces to the stability of `beta_j` and of the background mean, and our Stage 1 check already showed the explainer's own seed noise is ≤ 0.45 percentage points. The calibration step and ensemble averaging add mild non-linearity but not a research question.
- **Residual niche (small):** probability-space local attributions of a *calibrated* model across resamples, or stability *under data-handling choices*. The second is where C connects to E/H2 (§6, secondary question).

## 5. Focus on E — robustness to missingness

**Verdict for E as originally defined: no novelty claim supported. For the refinement H2: a narrow claim may be defensible, pending checks.**

- **Existing work (abstract-level):**
  - Clinical-prediction missing-data methodology: `sisk2023` (simulation of imputation and missing indicators across development and deployment), `jce2024imp` (prognostic performance depends on imputation algorithm), `sim2025` (imputation plus internal validation), `sperrin2020` (missing data should be handled differently for prediction).
  - Explainability under imputation: a Twente conference paper (no DOI), `bremen2026` thesis (uncertainty in explanation).
  - Pima zeros: `msys` (median handling of missing values and outliers), `pima_leaksafe`, `knn_imp_bmcmrm`.
- **Informative missingness is not supported by our data:** in the training split the positive rate among rows with missing insulin is 0.36 versus 0.34 observed, and skin-fold 0.38 versus 0.33; the small-n features (glucose n=4, BMI n=9, BP n=23) are too sparse to say anything. So a "missingness is informative" story (MNAR) would be weak here.

| Training split (n = 614) | Missing (share) | Positive rate if missing | Positive rate if observed | Observed class medians (neg / pos) |
|---|---|---|---|---|
| Glucose | 4 (1%) | 0.50 | 0.35 | 108 / 141.5 |
| BloodPressure | 23 (4%) | 0.48 | 0.34 | 70 / 76 |
| SkinThickness | 175 (29%) | 0.38 | 0.33 | 27 / 33 |
| Insulin | 290 (47%) | 0.36 | 0.34 | 100 / 168 |
| BMI | 9 (1%) | 0.22 | 0.35 | 30.1 / 34.35 |

- **The refinement (H2):** because observed values differ a lot by class (for example insulin median 100 vs 168), a **class-conditional constant** inserted into 47 % of the insulin and 29 % of the skin-fold cells is itself a strong label signal.

### Exploratory pilot (training split only; test split untouched; **not a result to report**)

Same logistic regression (C = 0.1, balanced) and a fixed random forest; 5-fold CV, 3 seeds; AUC mean ± SD across seeds.

| Pipeline | LR | RF |
|---|---|---|
| Valid: fold-contained, label-free median | 0.842 ± 0.003 | 0.840 ± 0.002 |
| **Leaky:** class-conditional median computed on all training rows before CV | 0.875 ± 0.003 | 0.938 ± 0.003 |
| Canary: *permuted* labels, valid pipeline | 0.501 ± 0.013 | 0.493 ± 0.027 |
| Canary: *permuted* labels, leaky imputation | 0.517 ± 0.027 | 0.857 ± 0.007 |

What this suggests (not proves):
- The inflation is **model-dependent**: small for LR (+0.03) but large for RF (+0.10, reaching 0.94, the range reported by the three studies that describe group-median imputation).
- A **label-permutation canary** separates the cases cleanly for flexible models: with *shuffled* labels the valid pipeline sits at chance (≈0.49-0.50) while the leaky one reaches 0.86 for RF. It is **weak for LR** (0.517), so a canary alone would miss leakage in linear models.
- Limits: one split, fixed RF hyperparameters, my emulation of the *described* practice, not the authors' code. Their actual pipelines are unverified.

## 6. Recommended research question (for your approval)

**Primary RQ (H2).** *How much does outcome-conditional imputation of the Pima impossible zeros inflate cross-validated and held-out discrimination, calibration, thresholded metrics and explanation output compared with leakage-safe imputation, how does this depend on model family and on the fraction of missing values, and can a label-permutation canary detect it?*

**Secondary RQ-1 (model dependence).** Why is the inflation small for logistic regression and large for flexible models; does the effect scale with missing fraction in a controlled simulation where the truth is known?

**Secondary RQ-2 (C-lite).** Do global importance and calibration diagnostics reveal the leak (for example spurious importance of insulin/skin-fold, over-confident probabilities), i.e. can explanation or calibration outputs serve as leakage alarms?

*(Optional, only if scope allows)* RQ-3 (E-lite): sensitivity of an honest pipeline to imputation choice (median, MICE, missing-indicator) following `sisk2023`.

**Claim boundaries (for your own writing):**
- *You may say, if the final experiments support it:* "in a controlled replication, outcome-conditional imputation before cross-validation raised RF ROC-AUC from X to Y"; "the canary flagged it"; "the magnitude is consistent with published AUCs of 0.93-0.96 where group-median imputation is described".
- *You may not say:* those studies are leaky or wrong (until their full texts confirm the order of imputation and use of labels); that you are first; that the method is novel; that class-conditional imputation is "never" valid (the safe statement is that outcome labels are unavailable at deployment, so such imputation cannot be applied to new patients).

## 7. Risks and checks needed before committing

1. **Verify the three studies' pipelines from full texts** (`msys`, `pima_leaksafe`, Khan 2026 Zenodo): is imputation done before splitting, are test-set labels used, what does "group" mean?
2. **A deeper novelty search** specific to H2 (full-text and citation-chaining via your library): I found no prior quantification, but that is weak evidence.
3. **The effect may seem "obvious"** to reviewers. The contribution would then rest on the *quantification across models and missing fractions*, the *simulation*, and the *diagnostics*, not on the observation itself. Position it against `kapoor` (taxonomy of leakage) honestly.
4. **Pilot caveats** above; Stage 6 must pre-specify hypotheses and acceptance criteria and never tune on the test set.
5. **Forking-paths disclosure:** H2 emerged from reading the literature and a pilot; the paper should say so.

## 8. Decisions I need from you

1. Approve the **primary RQ** (or choose another direction from the table).
2. Include the **simulation** (controlled missing fraction and class separation) in the plan?
3. Can you obtain/read the full texts of `msys`, `pima_leaksafe`, Khan 2026 and `kapoor`, and report the imputation order?
4. **Still unanswered:** may I write the **experiment code** (not the prose) under your institution's AI rule?
5. Have you read Smith 1988 (PMC2245318)? The outcome timing still matters for how the paper words the target.
6. Venue/template can wait until Stage 7.

## 9. Next step
After your approval I will do **Stage 6 (design only)**: hypotheses, factors and levels, seeds, metrics, statistical analysis plan, leakage-resistant split design, output structure and an acceptance checklist, for your sign-off before any new experiment code is written or run.
