"""Assembles research/stage3/STAGE3_NOTES.md from hand-written notes + generated rubric/score tables."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = (HERE / "rubric_table.md").read_text(encoding="utf-8")
S = (HERE / "scores_table.md").read_text(encoding="utf-8")
N = (HERE / "direction_notes.md").read_text(encoding="utf-8")
P = json.loads((HERE / "pilot_results.json").read_text(encoding="utf-8"))
c = P["cv_auc_mean_sd"]
m = P["missingness_train"]


def f(x):
    return f"{x[0]:.3f} ± {x[1]:.3f}"


pilot_rows = "\n".join([
    f"| Valid: fold-contained, label-free median | {f(c['LR_valid_foldcontained_median'])} | {f(c['RF_valid_foldcontained_median'])} |",
    f"| **Leaky:** class-conditional median computed on all training rows before CV | {f(c['LR_leaky_class_median_before_cv'])} | {f(c['RF_leaky_class_median_before_cv'])} |",
    f"| Canary: *permuted* labels, valid pipeline | {f(c['LR_permuted_labels_valid'])} | {f(c['RF_permuted_labels_valid'])} |",
    f"| Canary: *permuted* labels, leaky imputation | {f(c['LR_permuted_labels_leaky_imputation'])} | {f(c['RF_permuted_labels_leaky_imputation'])} |",
])
miss_rows = "\n".join(f"| {k} | {v['n_missing']} ({v['share_missing']:.0%}) | {v['pos_rate_missing']:.2f} | {v['pos_rate_observed']:.2f} | {v['class_median_observed']['neg']:g} / {v['class_median_observed']['pos']:g} |" for k, v in m.items())

T = f"""# Stage 3 — Choosing a defensible contribution (notes, not manuscript text)

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

{R}

**Caveats on the scoring.** Scores are my judgements from abstracts. H2 was defined *after* I saw the pilot, so it is the score most exposed to confirmation bias; please test it with the sensitivity check and with your own reading. The overlap criterion relies on searches that are not exhaustive.

## 3. Scores

{S}

**Rank robustness.** H2 ranks first under all three weightings; E is 2nd/2nd/3rd; C is 6th/5th/6th. H1 moves a lot (3rd / 6th / 2nd) because it depends on how much weight "novelty" gets and it is a meta-research design.

Per-direction justification:

{N}

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
{miss_rows}

- **The refinement (H2):** because observed values differ a lot by class (for example insulin median 100 vs 168), a **class-conditional constant** inserted into 47 % of the insulin and 29 % of the skin-fold cells is itself a strong label signal.

### Exploratory pilot (training split only; test split untouched; **not a result to report**)

Same logistic regression (C = 0.1, balanced) and a fixed random forest; 5-fold CV, 3 seeds; AUC mean ± SD across seeds.

| Pipeline | LR | RF |
|---|---|---|
{pilot_rows}

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
"""
(HERE / "STAGE3_NOTES.md").write_text(T, encoding="utf-8")
print(len(T.splitlines()), "lines")
