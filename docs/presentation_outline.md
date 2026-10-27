# Presentation outline (10–12 min)
1. Problem and why *educational* framing (1 min)
2. Dataset: Pima, 768 rows, who it represents, zeros-as-missing (2)
3. Pipeline and leakage safeguards: split, in-pipeline preprocessing, CV, one-shot test (2)
4. Results: model comparison, held-out metrics with CIs, calibration (2)
5. Honest finding: glucose is the strongest predictor, other features still add signal; outcome timing is undocumented (1)
6. Explainability demo: live prediction, SHAP bars, caveat on causation (2)
7. Limitations, privacy, future work (1)
Demo script: Home → Risk Estimation (defaults, then glucose 180) → report download → Model Insights → About.
