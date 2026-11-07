# PAPER OUTLINE (framework only; no results, no prose for submission)

All research questions, hypotheses and decision rules below are copied from the frozen `PREREG_DRAFT.md` (`prereg-v1`). Every cell marked **PENDING** depends on Exp 4, the G6 audit and the verification pass. The author writes all submitted text.

## Contribution type (to decide after results and literature)
This is an empirical, pre-registered methodological evaluation of one leakage mechanism (outcome-conditional imputation), not a new algorithm. Novelty claims are limited to what the verified literature review supports (**PENDING**; full-text findings from the author outstanding).

## Candidate working titles (not final; wording depends on results)
1. "How much does outcome-conditional imputation inflate performance on the Pima diabetes data? A pre-registered evaluation"
2. "Label-aware imputation as a leakage source: pre-registered real-data and simulation evidence"
Final title: PENDING.

## Research questions (frozen)
- **Primary RQ.** How much does outcome-conditional imputation of the Pima impossible zeros inflate discrimination, calibration, thresholded metrics and explanation output compared with leakage-safe imputation; how does this depend on model family and missing fraction; and can a label-permutation canary detect it?
- **RQ-1** (simulation): does inflation scale with missing fraction and model flexibility when truth is known?
- **RQ-2**: do importance and calibration outputs reveal the leak?

## Hypotheses and decision rules (frozen; SESOI = 0.02 ROC-AUC)
| ID | Hypothesis | Confirmed if | Refuted if | Status |
|---|---|---|---|---|
| H1 (primary) | Reg-3 inflates apparent ROC-AUC of RF-default by more than SESOI | lower CI bound of E1 > 0.02 | upper bound < 0.02 | PENDING |
| H2 | Inflation larger for flexible models than LR | E1(RF-default) − E1(LR) > 0, CI excludes 0 | CI includes or below 0 | PENDING |
| H3 | Label factor, not statistics scope, drives most inflation | label effect > scope effect, interaction small | otherwise | PENDING |
| H4 | Reg-2/3 raise the deployment gap; Reg-0/1 do not | E2 lower bound > 0.02 (Reg-2/3, RF); E2 within ±0.02 (Reg-0/1) | otherwise | PENDING |
| H5 | (simulation) inflation ≈ 0 at 0% missing, rises with missing fraction | monotone trend; E1 at 0% within ±0.005 | otherwise | PENDING |
| H6 | Canary flags Reg-2/3 for flexible models (TPR ≥ 0.90), not Reg-0/1 (FPR ≤ 0.05) | thresholds met | otherwise | PENDING |
| H7 | (exploratory) importance share of heavily imputed features and calibration slope differ | descriptive | — | PENDING |

## Section plan
1. **Introduction** — context; why evaluation integrity matters; gap (**PENDING**: depends on literature review); objectives; contributions (limited to verified).
2. **Related work** — data leakage and preprocessing leakage; permutation controls; Pima limitations; the three studies describing outcome-conditional imputation; Smith (1988). **PENDING** author's full-text notes and verified bibliography.
3. **Questions and hypotheses** — H1–H7 as above.
4. **Methods** — dataset and label definition (with timing caveat); regimes Reg-0…Reg-3 (Reg-4 not in confirmatory configs); App vs Dep evaluation; splits (J = 100 paired stratified 80/20); models (LR, RF-default, RF-regularised, HGB, SVM-RBF calibrated); negative controls A and B; canary design; simulation generator; metrics; Nadeau–Bengio CIs; Holm (supplementary); seeds.
5. **Experimental setup** — environment, tags/commits, configs, seed, hardware, run design, failure/recovery record (see `REPRODUCIBILITY.md`).
6. **Results** (all PENDING verification):
   - 6.1 Gates and negative controls
   - 6.2 Exp 1: E1–E4 per model; H1–H4
   - 6.3 Exp 2: canary detection TPR/FPR; H6
   - 6.4 Exp 4: inflation vs missing fraction, mechanism, AUC level, n; H5
   - 6.5 Secondary/exploratory (labelled): PR-AUC, Brier, calibration, thresholded metrics, LAS (H7)
7. **Discussion** — interpretation; agreement with prior reports; alternative explanations; inconclusive results. PENDING.
8. **Limitations / threats** — see `SUBMISSION_CHECKLIST.md` §F.
9. **Conclusion and future work** — PENDING; amendments or extra regimes only as separately labelled analyses.
Declarations and references: venue-dependent, PENDING.

## Figure and table specifications (data sources must be verified outputs)
| ID | Content | Source data | Status |
|---|---|---|---|
| F1 | Study workflow and regime diagram (what each regime fits on / whether it reads held-out labels) | frozen PREREG §2 | can be drawn now |
| F2 | Paired split differences E1 per model (distribution + CI) | `results/exp1/metrics.csv` | PENDING |
| F3 | App vs Dep AUC per regime and model (deployment gap) | `results/exp1/metrics.csv` | PENDING |
| F4 | Canary permuted-AUC distributions per regime/model | `results/exp2/permuted_auc.csv.gz` | PENDING |
| F5 | Simulated inflation vs missing fraction, by mechanism/model/n | `results/exp4/runs.csv.gz` | PENDING |
| T1 | Literature comparison (verified entries only) | `LITERATURE_REVIEW.md` | PENDING |
| T2 | Configurations and identifiers | configs, `REPRODUCIBILITY.md` | can be drafted now |
| T3 | Gates and stop rules | `results/audit/AUDIT_G6.json` | PENDING |
| T4 | Pre-registered contrasts: estimate, 95% interval, method, n, decision | `results/analysis/` | PENDING |
| T5 | Threats to validity | checklist §F | can be drafted now |
Each figure/table: caption, axis labels and units, abbreviation key, numbers cross-checked to artifacts.

## Reviewer-style questions the author must be ready to answer
1. Why is the SESOI 0.02, and does the pilot-informed choice bias H1? (disclosed forking path)
2. Is "Reg-3" really what the three studies did? (depends on author's full-text reading; abstract-level only so far)
3. Is the simulation realistic enough to say anything about Pima, and why MCAR/MNAR with OR 1.5?
4. Can any effect be attributed to the label definition itself (glucose criterion) rather than imputation?
5. Why only median imputation, and what about MICE or missing-indicator approaches (explicitly out of scope)?
6. How does the single-dataset scope limit generalisation?
7. What exactly deviated from the protocol, and could any deviation affect conclusions?
8. What is the contribution beyond known advice to split before preprocessing? (needs literature evidence)
9. Why were Nadeau–Bengio intervals used instead of fold-wise tests?
10. How were failed or inconclusive outcomes handled?
