# Stage 2 — Literature review notes (support material, not manuscript text)

Date: 27 Oct 2026 · Project: *Diabetes Risk Prediction Using Machine Learning and Explainable AI* · Companion files: `LITERATURE_MATRIX.csv` (50 sources × 18 fields), `sources_verified.json` (raw metadata and abstracts), `discover.py`, `overlap_search.py`, `verify_sources.py`, `build_stage2.py`.

**How to use these notes.** Per your institution's rule, I give you evidence, tables and feedback, **not** prose for the paper. Every statement below is tied to a source key in the matrix. All study descriptions are **abstract-level paraphrases**; I have **not read the full texts**. Read the full text of any source before you cite it or rely on a number from it.

---

## 1. What was searched, and the limits of that search

- **Tools:** Crossref (bibliographic queries and metadata), OpenAlex (relevance-ranked search, overlap counts, abstracts), PubMed E-utilities, Semantic Scholar, arXiv API, JMLR pages, and general web search. Run on 27 Oct 2026.
- **Topics covered (your list):** diabetes ML; Pima limitations; imbalance and ROC-vs-PR; calibration; thresholds; feature importance and SHAP stability; bias and generalisability; reporting and validation; leakage and selection bias in small data; direct overlap.
- **Not done / not possible:** IEEE Xplore, ACM DL, SpringerLink, ScienceDirect and Google Scholar were not queried directly; no paywalled full texts were read; the 1988 ADAP paper (Smith *et al.*) exists in PMC only as a scanned PDF that my tools cannot read, so **the outcome definition and its time window remain unresolved** (see §8).
- **This is a focused, selective review, not a systematic review.** OpenAlex "total hits" are relevance-ranked keyword matches; a high or low count is **not** evidence that a topic is saturated or empty.
- **Result:** 50 sources verified (20 diabetes/Pima, 30 methodology/XAI/reporting). Metadata verified via Crossref for 43, via the arXiv API for 5, by JMLR page for 2, and via OpenAlex/DataCite for 1 (zenodo_shap).
- **Low-evidence sources, label as such:** leakfree_rs, calib_first_rs, zenodo_shap, alvarez, krishna, matijevic (preprints or repository records). Venue quality of several 2025–26 journals was **not assessed**.

## 2. Table A — Diabetes / Pima literature (comparison table; "NR" = not reported in the abstract I read)

| Study | Year | Dataset | Method | Validation | Metrics (as reported) | Explainability | Limitations (reviewer notes) | Relationship to our work |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Kavakiotis et al. [kavak] | 2017 | n/a (review) | Systematic review; 4 application categories | n/a | Prediction/diagnosis most popular; ~85% supervised methods; SVM most used; mainly clinical datasets | none stated | Pre-2017; breadth over depth; not a performance benchmark | Context for supervised baselines |
| Chaki et al. [chaki] | 2022 | 107 publications (Scopus, PubMed) | Systematic review by datasets, preprocessing, features, models, assistants, metrics | n/a | Organises the field; lists three open research issues | none stated | Abstract does not name the issues; read full text | Taxonomy of datasets/preprocessing/metrics |
| Khanam et al. [khanam] | 2021 | Pima, 768 | 7 ML algorithms + neural networks | NR | LR and SVM performed well; 2-hidden-layer NN reached 88.6% accuracy | none stated | Validation protocol NR in abstract; accuracy only | Supports LR/SVM as strong Pima baselines |
| Sisodia et al. [sisodia] | 2018 | Pima, 768 | Decision tree, SVM, naive Bayes | NR | Naive Bayes highest accuracy 76.30%; ROC curves used to verify | none stated | Accuracy-centred; calibration NR; protocol NR | Reference accuracy level under simple protocol |
| Kaur et al. [kaur] | 2020 | Pima, 768 | SVM-linear, SVM-RBF, k-NN, ANN, MDR | NR | Compares five models (numbers not in abstract read) | none stated | Results NR | Another multi-model Pima comparison |
| Miao [miao] | 2021 | Pima, 768 | Several ML algorithms; standardisation; later 'adjustment' | NR | SVM best: accuracy 85.06% (standardised), 87.01% after adjustment | Correlation only | Nature of 'adjustment' and whether test data guided it: NR; check full text | Example of high-accuracy single-protocol claims |
| Maniruzzaman et al. [msys] | 2018 | Pima, 768 (268/500) | Group-median imputation of missing, median for outliers; 6 feature selectors × 10 classifiers | NR (validated 'for stability and reliability') | RF+RF reached accuracy 92.26%, sens 95.96%, spec 79.72%, AUC 0.93 | none stated | 'Group median' may be class-conditional (check full text for label use before split); preprocessing order NR | Direct precedent on handling zeros/outliers; magnitude of claims is a leakage red flag to check |
| Kırbaş et al. [kirbas] | 2025 | Pima, 768 | 8 models; SMOTE; scaling; SHAP | Train/test split and 10-fold CV | RF best: acc 82%, F1 0.83 (split); 83%/0.84 (CV); SHAP: glucose, BMI, pregnancies, insulin key | SHAP (global) | Whether SMOTE/scaling are inside folds: NR; calibration NR; SHAP stability NR | Closest 'SHAP on Pima' peer-reviewed precedent |
| Shams et al. [rfegru] | 2025 | Pima, 768 | Mean imputation, normalisation, RFE feature selection, GRU; vs RF, LR, kNN, NB, HGB | NR | Precision/recall/F1/accuracy ≈ 90.5-90.7%, AUC 0.9278 | none stated | Much higher than leakage-safe studies; split and order of preprocessing/feature selection NR | Illustrates the spread of reported performance |
| AbdulAbbas et al. [etasr] | 2025 | Pima, 768 | MICE, SMOTE, z-score, 2 feature-selection methods; RF, MLP, XGBoost, SVM, LR | Single 80:20 split and 5-fold CV | RF 79.79% acc (split); MLP 77.81% acc, ROC-AUC 84.43% (CV) | none stated | Stated aim is leakage prevention; abstract does not mention calibration or explanation; engineered features (Glucose_BMI) selected | Overlaps our leakage-safe preprocessing contribution |
| Hassan et al. [aposta] | 2026 | Pima 768; BRFSS 2015 (8,000 subsample; 253,680 full) | Fold-nested scaling/SMOTE; 10x repeated 5-fold CV; paired Wilcoxon on fold AUCs; nested CV; SHAP on XGBoost | Single split vs repeated CV vs nested CV | Single split favoured XGBoost; repeated CV: LR best (AUC 0.835±0.028); XGBoost worst on Pima; ranking reverses on full BRFSS | SHAP (XGBoost) | Wilcoxon on per-fold AUCs: folds are not independent (see Nadeau & Bengio, Demsar); whether a variance correction was applied is NR, check full text; calibration NR | Strong overlap: leakage-safe repeated-CV model comparison with LR winning on Pima |
| Dalal and Akbar [jaimlnn] | 2026 | Pima, WDBC, Cleveland heart | LR, SVM, RF, HGB, MLP; permutation importance each fold | 10x5-fold stratified CV (50 fits); corrected resampled t-test; Spearman, top-5 Jaccard, top-feature recurrence; data reduced to 25% | Equal AUC but different stability; Pima stability 0.70-0.87, glucose ranked first in every fit of four models; LR 0.90 to 0.68 at 25% data | Permutation importance stability | Permutation importance only (not SHAP); abstract mentions calibration measured; full text needed | Closest overlap with 'explanation stability' direction |
| Lu et al. [thresh_math] | 2026 | Pima; Heart Failure; Thoracic Surgery | 5 classifiers; baseline/SMOTE/ADASYN; thresholds 0.30-0.70 | Leakage-free repeated stratified 10-fold ×5; mixed-effects model | Thresholds <0.5 beneficial on Pima; best F1 0.6890; oversampling tended to increase Brier | none stated | F1-based threshold choice; abstract-level only | Overlaps threshold-analysis direction; shows Brier worsens with oversampling |
| Soomro et al. [leakfree_rs] | 2026 | Pima 768; Early-Stage Diabetes Risk dataset | 6 models (LR, RF, FFNN, BPNN, GRNN, ABC-FFNN); fold-contained preprocessing | Multi-seed stratified 10-fold CV; calibration; pairwise statistical tests | Pima AUC 0.76-0.84 (GRNN 0.837±0.002; LR 0.832; RF 0.829); calibration assessed | none stated | Preprint; details need full text; PREPRINT (Research Square, not peer-reviewed) | Strong overlap with 'reproducible evaluation framework' direction |
| Akinwumi et al. [calib_first_rs] | 2026 | Not named in the abstract portion read (predictors suggest Pima) | 5 predictors; insulin orthogonalised from glucose; Brier minimisation; vs LR, RF, XGB, GB | Covariate-shift simulations | LR AUROC 0.836, AUPRC 0.714, Brier 0.166, 'excellent calibration' | none stated | Preprint; dataset and validation protocol need full text; PREPRINT (Research Square, not peer-reviewed) | Overlaps 'calibration-aware LR' direction |
| V. R. and Sasirekha [reliab_aware] | 2026 | Pima, 768 | LR, RF, XGBoost; SHAP global/local; Feature Consistency Index (cross-model SHAP agreement); perturbation robustness | Brier score, reliability diagrams | XGB AUC 0.8374 best; RF best Brier 0.1646; glucose and BMI consistently attributed; BP, skin thickness weak and unstable | SHAP global+local; FCI | Resampling stability of SHAP not described in abstract; protocol NR | Overlaps calibration + SHAP + robustness at a broad level |
| (authors not listed) [zenodo_shap] | 2024 | Pima | SVM, kNN, DT, XGBoost; SMOTE-Tomek at varying ratios; coefficient of variation of SHAP values | NR | XGBoost: best accuracy but less stable SHAP; SVM more stable | SHAP stability (CV of SHAP) | Provenance weak; cite only with caution; REPOSITORY RECORD (Zenodo; dissertation type; authors not listed in metadata; peer review not evident) | Overlaps SHAP-stability idea (class-imbalance axis) |
| Collins et al. [collins2011] | 2011 | Systematic review of T2D models | Methodological review | n/a | Widespread poor methods: univariate pre-screening, categorising predictors, missing data handling unreported in 41% of studies | none stated | Not about ML specifically | Shows long-standing reporting/method problems in diabetes prediction |
| Noble et al. [noble2011] | 2011 | Systematic review | Standard + realist review | n/a | Many models; few externally validated; usability and use-case often unclear | none stated | Pre-ML era focus | Context: intended use and external validation |
| Abu-Shareha et al. [pima_survey] | 2025 | Pima, 768 | Survey + own evaluation (scaling, feature selection, oversampling) | NR | Preprocessing helps; RF often best; evaluation approaches vary widely | none stated | Abstract-level; may inherit heterogeneity it describes | Evidence that Pima evaluation practice is inconsistent |

## 3. Table B — Methodology, explainability, reporting and bias sources

| Source [key] | Year | Type | What it contributes (abstract-level) | What it does NOT establish | Use for us |
| --- | --- | --- | --- | --- | --- |
| Davis et al. [davis] | 2006 | conference | ROC dominance iff PR dominance; achievable PR curve; PR more informative for skewed data | Clinical utility | Why report PR-AUC |
| Saito et al. [saito] | 2015 | journal | ROC plots can be deceptive on imbalanced data; PR plots more informative | Calibration | Support for PR reporting |
| Steyerberg et al. [steyerberg] | 2010 | journal | Report discrimination and calibration always; decision-analytic measures if used for decisions | ML-specific recommendations | Metric selection rationale |
| Van Calster et al. (STRATOS) [vancalster2019] | 2019 | journal | Poor calibration can mislead and harm decisions; how to avoid and assess it | Specific method superiority | Core justification for calibration analysis |
| Van Calster et al. [vancalster2016] | 2016 | journal | Defines levels and implications for development/validation | Real-data behaviour of ML models | Vocabulary for calibration claims |
| Niculescu-Mizil et al. [niculescu] | 2005 | conference | Boosted trees/stumps distort probabilities (sigmoid-shaped); naive Bayes pushes to 0/1; other models better calibrated (abstract-level) | Behaviour on small clinical data | Basis for comparing calibrators |
| Vickers et al. [vickers2006] | 2006 | journal | Evaluates models by clinical consequences using only the dataset | That our threshold is clinically right | Possible threshold-utility analysis |
| Wynants et al. (STRATOS) [wynants2019] | 2019 | journal | Thresholds often chosen ad hoc; implicit costs of FP/FN matter | Specific threshold values | Justifies treating threshold as a stated assumption |
| Wolff et al. [wolff] | 2019 | journal | Structured assessment of bias/applicability | Study quality by itself | Checklist to self-audit our study |
| Collins et al. (TRIPOD+AI) [tripodai] | 2024 | journal | Updated reporting items for regression and ML prediction models | Model quality | Checklist for manuscript |
| Riley et al. [riley2019] | 2018 | journal | Sample-size criteria for model development | That 768 is adequate | Quantifies how small 768/268 is relative to parameters |
| Kapoor et al. [kapoor] | 2023 | journal | Leakage widespread; complex ML no better than LR once errors corrected (civil-war example) | Pima-specific leakage rates | Leakage taxonomy; model-info sheet |
| Varma et al. [varma] | 2006 | journal | Evaluates validity of CV error of the optimised classifier (magnitude: read full text) | Size of bias in our setting | Justifies nested CV |
| Cawley and Talbot [cawley] | 2010 | journal (JMLR; no DOI) | Selection-criterion optimisation causes bias in performance estimates | Quantitative bias for Pima | Justifies nested CV |
| Vabalas et al. [vabalas] | 2019 | journal | Validation choices affect bias with small samples; design guidance | Pima-specific thresholds | Small-sample evaluation design |
| Nadeau et al. [nadeau] | 2003 | journal | ABSTRACT NOT RETRIEVED; content known only from general knowledge — verify before citing | — | Why repeated-CV fold comparisons need variance correction |
| Dietterich [dietterich] | 1998 | journal | Reviews tests and their error rates | Modern repeated-CV practice | Model-comparison testing options |
| Demsar [demsar] | 2006 | journal (JMLR; no DOI) | Recommends tests for multi-dataset comparisons (abstract-level) | Single-dataset inference | Caution against naive significance tests |
| Christodoulou et al. [christodoulou] | 2019 | journal | No ML advantage at low risk of bias; 68% potential validation bias; calibration unaddressed in 79% | Current (2026) state | Key background: LR vs ML; calibration neglected |
| Scott et al. [lundberg2017] | 2017 | preprint/conference (NIPS 2017) | Additive attribution framework | Stability | Basis of our explainer |
| Lundberg et al. [lundberg2020] | 2020 | journal | Local explanations combined into global understanding for tree models | Behaviour for linear/calibrated pipelines | Context for SHAP variants |
| I. et al. [kumar2020] | 2020 | conference (ICML 2020) | Mathematical and human-centric problems with Shapley explanations | Empirical size of instability | Caveat on interpreting SHAP |
| Slack et al. [slack] | 2020 | conference | Perturbation-based explainers can be fooled | Behaviour in benign settings | Limits of faithfulness claims |
| David et al. [alvarez] | 2018 | PREPRINT (arXiv) | Current methods perform poorly on robustness metrics | Resampling stability | Concept: similar inputs should give similar explanations |
| Satyapriya et al. [krishna] | 2022 | PREPRINT (arXiv) | Post hoc methods often disagree | Pima-specific | Motivates stability/agreement checks |
| Sara et al. [matijevic] | 2026 | PREPRINT (arXiv) | Predictions vary across training samples; proposed regulariser | LR/tabular stability | Shows instability concept in clinical risk models |
| Ghassemi et al. [ghassemi] | 2021 | journal (viewpoint) | Post hoc explanations do not guarantee trust/fairness | Empirical evidence | Caution on explanation claims |
| Rudin [rudin] | 2019 | journal | Prefer inherently interpretable models | Performance parity in all domains | Supports LR choice |
| Obermeyer et al. [obermeyer] | 2019 | journal | Cost used as proxy for need created bias | Pima issues | Illustrates label/target choice risks |
| Gianfrancesco et al. [gianfrancesco] | 2018 | journal | Lists bias sources | Pima-specific | Framing for population-specific bias |

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

- **Metadata verified:** all 50 matrix sources (Crossref 43; arXiv 5; JMLR pages 2; OpenAlex/DataCite 1). Earlier-report references (Brier 1950, Fawcett 2006, Efron & Tibshirani 1993, Hosmer *et al.*, etc.) were verified in the E-report work, not re-verified here.
- **Abstract not retrieved:** nadeau → description is general knowledge only; verify.
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
