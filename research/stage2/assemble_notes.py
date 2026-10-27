"""Assembles STAGE2_NOTES.md from hand-written notes + generated tables + verification counts."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
V = json.loads((HERE / "sources_verified.json").read_text(encoding="utf-8"))
A = (HERE / "tableA.md").read_text(encoding="utf-8")
B = (HERE / "tableB.md").read_text(encoding="utf-8")
import csv  # noqa: E402

rows = list(csv.DictReader(open(HERE / "LITERATURE_MATRIX.csv", encoding="utf-8-sig")))
n = len(rows)
n_d = sum(r["role"] == "D" for r in rows)
n_pre = [r["key"] for r in rows if "PREPRINT" in r["type / peer-review note"] or "REPOSITORY" in r["type / peer-review note"]]
n_cr = sum("Crossref" in r["verification"] for r in rows)
n_ax = sum("arXiv" in r["verification"] for r in rows)
no_abs = [r["key"] for r in rows if "NOT RETRIEVED" in r["verification"]]

T = f"""# Stage 2 — Literature review notes (support material, not manuscript text)

Date: 27 Oct 2026 · Project: *Diabetes Risk Prediction Using Machine Learning and Explainable AI* · Companion files: `LITERATURE_MATRIX.csv` ({n} sources × 18 fields), `sources_verified.json` (raw metadata and abstracts), `discover.py`, `overlap_search.py`, `verify_sources.py`, `build_stage2.py`.

**How to use these notes.** Per your institution's rule, I give you evidence, tables and feedback, **not** prose for the paper. Every statement below is tied to a source key in the matrix. All study descriptions are **abstract-level paraphrases**; I have **not read the full texts**. Read the full text of any source before you cite it or rely on a number from it.

---

## 1. What was searched, and the limits of that search

- **Tools:** Crossref (bibliographic queries and metadata), OpenAlex (relevance-ranked search, overlap counts, abstracts), PubMed E-utilities, Semantic Scholar, arXiv API, JMLR pages, and general web search. Run on 27 Oct 2026.
- **Topics covered (your list):** diabetes ML; Pima limitations; imbalance and ROC-vs-PR; calibration; thresholds; feature importance and SHAP stability; bias and generalisability; reporting and validation; leakage and selection bias in small data; direct overlap.
- **Not done / not possible:** IEEE Xplore, ACM DL, SpringerLink, ScienceDirect and Google Scholar were not queried directly; no paywalled full texts were read; the 1988 ADAP paper (Smith *et al.*) exists in PMC only as a scanned PDF that my tools cannot read, so **the outcome definition and its time window remain unresolved** (see §8).
- **This is a focused, selective review, not a systematic review.** OpenAlex "total hits" are relevance-ranked keyword matches; a high or low count is **not** evidence that a topic is saturated or empty.
- **Result:** {n} sources verified ({n_d} diabetes/Pima, {n - n_d} methodology/XAI/reporting). Metadata verified via Crossref for {n_cr}, via the arXiv API for {n_ax}, by JMLR page for 2, and via OpenAlex/DataCite for 1 (zenodo_shap).
- **Low-evidence sources, label as such:** {', '.join(n_pre)} (preprints or repository records). Venue quality of several 2025–26 journals was **not assessed**.

## 2. Table A — Diabetes / Pima literature (comparison table; "NR" = not reported in the abstract I read)

{A}

## 3. Table B — Methodology, explainability, reporting and bias sources

{B}

## 4. Overlap map: your candidate directions against what already exists

| Direction | Closest existing works [key] | What they cover (abstract-level) | Overlap | Residual gap seen (not proven) |
|---|---|---|---|---|
| **A.** Calibration-aware risk estimation | calib_first_rs (preprint), leakfree_rs (preprint), reliab_aware, thresh_math | Brier-minimising LR; calibration assessed; reliability diagrams; oversampling raises Brier | **High** (breadth) | Calibration *uncertainty* (slope/intercept with CIs, per Van Calster) on Pima not seen in the abstracts |
| **B.** Threshold trade-off analysis | thresh_math; wynants2019 (guidance) | Joint threshold × oversampling sweeps 0.30–0.70, F1-based, leakage-free | **High** for generic sweeps | Sensitivity-target (screening) thresholds with uncertainty and decision-curve view: not seen |
| **C.** Explanation stability | jaimlnn; zenodo_shap; reliab_aware | Permutation-importance stability on Pima across 5 classifiers (10×5 CV, data reduction); SHAP stability under imbalance; cross-model SHAP agreement | **High** (permutation) / **Medium** (SHAP) | *Local* SHAP stability for a calibrated LR across resamples; SHAP-vs-permutation agreement; dependence on imputation choice: not seen |
| **D.** Multi-family performance + calibration comparison | aposta; leakfree_rs; jaimlnn; etasr; christodoulou (context) | Repeated CV, paired tests, LR often best on Pima | **High** | None evident for generic comparison |
| **E.** Robustness to missingness/perturbation | msys; reliab_aware; akinwumi (preprint) | Median handling of missing/outliers; 5 % input perturbation; covariate-shift simulation | **Medium** | Systematic effect of the zero-as-missing assumption and imputation method on *calibration and explanations* (incl. informative missingness): not seen |
| **F.** Why Pima results may not generalise | aposta (cross-dataset BRFSS); leakfree_rs (2nd dataset) | Cross-dataset checks with a different feature set | **Partial** | Documentary analysis of what the Pima label/timing can support: not seen; depends on Smith 1988 full text |
| **G.** Integrated reproducible evaluation framework | leakfree_rs (preprint); aposta; etasr; reliab_aware | Fold-contained preprocessing, multi-seed CV, calibration, statistics, SHAP | **High** | "Integration" alone is not a defensible novelty claim |
| **H (new).** Reporting/leakage audit of Pima-based ML papers | kapoor (taxonomy); christodoulou (79 % ignored calibration; 68 % validation bias); collins2011; pima_survey | Related audits exist for clinical ML and T2D models; Pima survey notes inconsistent evaluation | **Low-Medium** | I found no systematic audit of Pima papers against TRIPOD+AI/PROBAST/leakage taxonomy; a search protocol would be needed to confirm |

## 5. Research-gap analysis (notes)

**5.1 Established by the literature (with source scope)**
- LR is competitive with, or better than, complex ML on Pima under repeated, fold-contained CV: AUC ≈ 0.83–0.84 [aposta; leakfree_rs (preprint)]; consistent with our own CV 0.845 ± 0.013 (Stage 1 verified).
- Across clinical prediction studies, ML shows no consistent advantage over LR once bias is low [christodoulou; kapoor for a non-medical case].
- Calibration is under-reported (79 % of 71 studies did not address it) and matters for decisions [christodoulou; vancalster2019; steyerberg].
- Leakage and selection bias inflate reported performance [kapoor; varma; cawley; vabalas].
- Post hoc explanations can disagree, be fooled, or be unstable [krishna (preprint); slack; alvarez (preprint); kumar2020]; on Pima specifically, permutation-importance stability is high for few weakly correlated predictors but drops sharply with less training data [jaimlnn].
- Reported Pima accuracies range from ≈ 76 % to > 90 % across studies with different protocols [sisodia; etasr; khanam; msys; rfegru].

**5.2 Repeatedly attempted (do not claim as new):** classifier comparisons on Pima; SMOTE/feature-selection variants; SHAP on Pima [kirbas; aposta; reliab_aware]; leakage-free pipelines [etasr; leakfree_rs; aposta]; threshold × resampling sweeps [thresh_math]; calibration-first LR [akinwumi]; stability of importance [jaimlnn; zenodo_shap].

**5.3 Persisting weaknesses visible in the abstracts**
- Many report accuracy only, with the validation protocol or preprocessing order not stated [khanam; kaur; miao; rfegru].
- Very high claims (accuracy 90–92 %, AUC 0.93) [msys; rfegru] sit far above leakage-safe results (AUC 0.83–0.84) → *check full texts for leakage; do not assert it*.
- Wilcoxon tests on per-fold AUCs [aposta] use correlated folds; the abstract does not mention a variance correction [nadeau; demsar], so **check the full text** before saying anything about it.
- Treatment of Pima's zeros is heterogeneous (median, group median, MICE, mean) [msys; etasr; rfegru].
- Outcome semantics (concurrent status vs onset) are rarely discussed in the abstracts I read.

**5.4 Gaps with at least some evidence behind them (all narrow, all unproven by me)**
1. Local (not only global) explanation stability for a *calibrated LR*, with uncertainty, across resamples — C residual.
2. Sensitivity of calibration and explanations to the zero-as-missing/imputation assumption — E residual.
3. Calibration uncertainty (slope/intercept CIs) and screening-style thresholds with uncertainty on Pima — A/B residual.
4. What the Pima label can and cannot support (outcome timing) — F; blocked until Smith 1988 is read.
5. A measured audit of reporting and leakage practices in Pima-based ML papers — H.

**5.5 Gaps that are too broad or already addressed:** "ML for diabetes lacks explainability" (many SHAP-on-Pima papers); "evaluation lacks leakage control" (≥ 3 works claim this); "no one compares calibration across models on Pima" (soomro, reliab_aware, akinwumi do, at least at abstract level); "SHAP stability is unexplored" (zenodo_shap, jaimlnn exist).

**5.6 Honest assessment (preliminary, to be scored in Stage 3):** the current project does **not** support a strong novelty claim. Directions A, B, D and G are heavily overlapped in 2025–26 (mostly preprints or lower-visibility venues). C and E retain narrow residual questions. F and H are the least overlapped but are conceptual/meta-research and depend on full texts or a search protocol. A publishable framing may need to be a careful **replication / negative-or-null-results / reporting-quality** study rather than a new method.

## 6. Claim → source map (what you may say, and what you may not)

| Claim you might want to make | Source(s) | Scope of support | Caution |
|---|---|---|---|
| Calibration is often neglected in clinical ML | christodoulou; vancalster2019 | 71 clinical ML-vs-LR studies (2016–17); guidance paper | Not diabetes-specific |
| ML is not consistently better than LR | christodoulou; kapoor | Low-risk-of-bias comparisons; one civil-war case | Not Pima-specific |
| Leakage/selection bias inflates performance | kapoor; varma; cawley; vabalas | Surveys and simulations | Magnitudes vary by setting; read full texts |
| Pima results differ widely between studies | sisodia; etasr; khanam; msys; rfegru | Reported accuracies ≈ 76–92 % | Protocols differ; do not rank studies |
| Leakage-safe Pima AUC ≈ 0.83–0.84, LR competitive | aposta; leakfree_rs (preprint) | Repeated CV | Preprint; compare to our 0.845 ± 0.013 only with care |
| Importance rankings can be unstable under resampling | jaimlnn | Permutation importance, 3 clinical tabular datasets | Not SHAP; venue quality not assessed |
| Post hoc explainers can disagree | krishna (preprint); jaimlnn | Preprint; WDBC finding | Preprint |
| Risk thresholds are often ad hoc | wynants2019 | Guidance paper | Not empirical |
| Report with TRIPOD+AI; assess with PROBAST | tripodai; wolff | Guidelines | Reporting ≠ validity |
| PR curves are informative with imbalance | saito; davis | Theory/simulation | Does not address calibration |
| The dataset covers adult Pima women only | Dataset documentation (OpenML/UCI) | Documentation text | Cite the documentation; Smith 1988 full text not yet read |
| Target choice can embed bias | obermeyer; gianfrancesco | Health-system algorithm; viewpoint | Different setting |

**Do NOT claim:** "first", "novel framework", "no study has examined calibration/SHAP stability/leakage on Pima", "state of the art", "clinically useful", or that the label means future onset.

## 7. Feedback on the earlier (AI-written) E-report literature chapter

- **Section 2.6 research-gap statement is outdated.** It said the Pima abstracts reviewed do not mention calibration, uncertainty intervals or explanations. True for the three older studies it examined, but misleading overall: several 2025–26 Pima works do (soomro, reliab_aware, akinwumi, jaimlnn, kirbas, aposta). Narrow the claim to the specific studies, or revise it in the light of §4–5.
- Missing sources the chapter should engage with: christodoulou, kapoor, vancalster2019/2016, wolff, and the overlap works in §4.
- Earlier wording about the outcome being "glucose-criterion based" was already corrected in Stage 1/2 fixes; make sure the paper also treats outcome timing as unresolved.
- If any of that chapter's text is reused, remember your institution's authorship rule: it was AI-written.

## 8. Verification log and open items

- **Metadata verified:** all {n} matrix sources (Crossref {n_cr}; arXiv {n_ax}; JMLR pages 2; OpenAlex/DataCite 1). Earlier-report references (Brier 1950, Fawcett 2006, Efron & Tibshirani 1993, Hosmer *et al.*, etc.) were verified in the E-report work, not re-verified here.
- **Abstract not retrieved:** {', '.join(no_abs) or 'none'} → description is general knowledge only; verify.
- **Volume/pages to confirm:** cawley (JMLR 11), demsar (JMLR 7) — titles verified on JMLR pages.
- **Weak provenance:** zenodo_shap (no authors in metadata; repository record); akinwumi's dataset is not named in the abstract portion I read.
- **Unresolved, important:** the Pima **outcome definition/time window** — the 1988 ADAP paper (PMC2245318, free PDF) is scanned; I could not read it. The OpenML/UCI text defines positives by 2-h glucose ≥ 200 mg/dL at any survey examination or in routine care. **Please read the 5-page PDF and tell me (a) how onset is defined, (b) the time window, (c) when the 8 predictors were measured relative to the outcome.**
- **Full texts to obtain first (priority):** jaimlnn, aposta, leakfree_rs, reliab_aware, thresh_math, msys, kirbas, etasr, christodoulou, kapoor.

## 9. Decisions and questions for you (before Stage 3)

1. Which paper *type* is acceptable to you: methodological contribution, **replication/null-result**, **reporting-quality audit** (H), or an educational case study? This determines what novelty claim is honest.
2. Is a literature-based study (H) acceptable, or must the paper include new experiments?
3. May I write the **experiment code** (not the prose) under your institution's AI rule?
4. Can you read Smith 1988 and the top-10 full texts (library access) and report back?
5. Venue/template and page limit (needed only at Stage 7; a shortlist can be verified later).

## 10. Next step
On your answers I will do Stage 3: score directions A–H with an explicit rubric (evidence of gap, overlap, importance, feasibility, cost, statistical validity, risk of null result, suitability) and recommend one primary research question — or state plainly that no direction supports a novelty claim.
"""
(HERE / "STAGE2_NOTES.md").write_text(T, encoding="utf-8")
print(len(T.splitlines()), "lines;", n, "sources; crossref", n_cr, "arxiv", n_ax, "preprints", n_pre, "no abstract", no_abs)
