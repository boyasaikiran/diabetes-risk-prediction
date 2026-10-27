# Methodology

## Leakage safeguards
1. Test split (20 %, stratified, seed 42) is untouched until the final scoring.
2. Imputation medians and scaler parameters are fit inside the sklearn `Pipeline`, so within each CV fold only on that fold's training part, and on the training split for the final model.
3. Hyperparameters, model choice, calibration choice and the decision threshold all use training data only (cross-validation / out-of-fold predictions).
4. No feature selection or resampling was used (8 features; imbalance 35/65 handled by the evaluation metrics and an optional `class_weight` grid for logistic regression).
5. Test results are computed for the selected model only, so the test set cannot guide selection among candidates.

## Candidates
Majority-class baseline, Logistic Regression, Decision Tree, Random Forest, Gradient Boosting, SVM (RBF, probabilities via calibrated wrapper), HistGradientBoosting. Small grids; same stratified 5-fold CV and ROC-AUC refit criterion for all.

## Selection rule
Highest mean CV ROC-AUC; among models within one standard error of it, the one with the lowest interpretability rank wins. Rationale: differences among top models are smaller than fold noise, and a linear model is easier to explain and audit.

## Calibration and threshold
Sigmoid calibration (5-fold) is used only if out-of-fold Brier score on the training split improves (0.160 → 0.151 in the recorded run).
Threshold = highest value with out-of-fold training sensitivity ≥ 0.80. This favours fewer false negatives and is an *operating point*, not a clinically established category. The app therefore reports "at/above vs below the model's threshold" and does not use low/medium/high labels.

## Metrics
Accuracy, precision, sensitivity, specificity, F1, ROC-AUC, PR-AUC, Brier, confusion matrix, calibration curve; 1000-sample stratified bootstrap 95 % CIs on the test set.

## Explainability
Permutation-explainer SHAP applied to the full pipeline's probability with a 100-row training background; contributions are in probability points and sum (with the baseline) to the prediction (tested). Global importance: permutation importance on the test set. Both describe model behaviour, not causation, and are less reliable under correlated features.

## What software tests do not show
Passing tests demonstrate correct code behaviour (validation, shapes, additivity, reports). They say nothing about clinical validity.
