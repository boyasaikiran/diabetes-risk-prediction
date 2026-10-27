# Model card

- **Model:** Logistic Regression (L2) with sigmoid calibration, inside a pipeline (zero→NaN, median imputation, standardisation). Version in `models/metadata.json`.
- **Intended use:** education and demonstration of an ML workflow.
- **Out of scope:** diagnosis, screening decisions, treatment, insurance/employment, use on children or populations other than adults similar to the training data.
- **Training data:** 614 of 768 Pima Indians Diabetes Database rows ([dataset card](dataset_card.md)).
- **Inputs:** the 8 dataset features only; four are optional and imputed when blank.
- **Output:** probability calibrated to the training prevalence (35 %) and a flag relative to a threshold (0.294).

## Performance (held-out test, n = 154, from `artifacts/metrics.json`)
ROC-AUC 0.809 (0.735–0.872) · sensitivity 0.815 · specificity 0.670 · precision 0.571 · Brier 0.174.
Not externally validated. Subgroup performance has not been assessed.

## Caveats
Glucose is the strongest single predictor (training-split CV ROC-AUC 0.799 alone, 0.768 without it, 0.845 with all eight features), but the other features carry signal too. The timing of the outcome relative to the features is undocumented, so the target is recorded diabetes status, not future onset. Probabilities may be miscalibrated for any population with a different prevalence. Not a medical device; no regulatory assessment has been made.
