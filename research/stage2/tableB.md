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