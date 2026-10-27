# Diabetes Risk Prediction System (Machine Learning + Explainable AI)

An **educational** risk-estimation app: enter a few health measurements, get a model-generated
probability, see which inputs influenced it, and download a report.

> **Not a diagnostic tool.** It cannot confirm or rule out diabetes and has not been clinically
> validated. It is trained on one small, old, single-population dataset. See [Limitations](#limitations).

## Problem statement & objectives
Estimate the probability that a person in a research dataset was labelled diabetic, using
routinely-collected measurements, and make the model's behaviour transparent.
1. Reproducible pipeline: data → preprocessing → model comparison → calibrated final model.
2. Honest evaluation (held-out test, confidence intervals, calibration).
3. Per-prediction explanations that correspond to the actual model output.
4. A validated, privacy-conscious UI with report export.

## Features
- Streamlit dashboard: Home, Risk Estimation, Model Insights, Session History, About.
- Input validation (types, ranges, required/optional, unit hints). Missing optional values are never silently set to zero.
- Seven candidate models + baseline, one evaluation protocol, selection by CV (not test accuracy).
- SHAP (permutation) local explanations with an occlusion fallback; additive to the predicted probability.
- PDF and CSV report download (generated in memory).
- 45 automated tests, Ruff-clean, Dockerfile.

## Stack
Python 3.12 · pandas · scikit-learn · SHAP · Streamlit · Plotly · ReportLab · pytest · Ruff.

## Architecture
```
data_loader ─► preprocessing (ZeroToNaN → median impute → scale, inside one sklearn Pipeline)
     └► train ─► evaluate ─► models/model.joblib + artifacts/metrics.json
validation ─► predict (loads joblib; no retraining) ─► explainability ─► report_generator
app.py + ui/ read the saved artifacts only.
```
Details: [docs/architecture.md](docs/architecture.md).

## Dataset
Pima Indians Diabetes Database (NIDDK; UCI), 768 adult females of Pima heritage, 8 features, binary
outcome (34.9 % positive). Downloaded automatically from OpenML (id 37). Provenance, license notes and
biases: [docs/dataset_card.md](docs/dataset_card.md). **Check the license terms at the source before redistributing.**

## Setup
```bash
python -m venv .venv
.venv\Scripts\activate        # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -r requirements-dev.txt
```

## Train and evaluate
```bash
python -m src.train          # downloads data on first run (needs internet), writes models/ and artifacts/
pytest -q                    # software tests
ruff check .
```
Training is seeded (`config/config.yaml`); two runs gave identical results on this machine.

## Run the app
```bash
streamlit run app.py
```

## Evaluation methodology
Stratified 80/20 split (614 train / 154 test). All candidates tuned with 5-fold stratified CV on **train
only**; preprocessing sits inside the pipeline so it is refit per fold. Selection: best mean CV ROC-AUC,
then the simplest model within one standard error. Sigmoid calibration kept only if it lowered
out-of-fold Brier score. Threshold chosen from out-of-fold *training* predictions (highest specificity with
sensitivity ≥ 0.80). The test set was scored once, for the final model. Full text: [docs/methodology.md](docs/methodology.md).

### Results from the actual run (seed 42; regenerate with `python -m src.train`)
5-fold CV ROC-AUC on training data: Logistic Regression 0.845 · SVM 0.844 · Random Forest 0.842 ·
HistGradientBoosting 0.835 · Gradient Boosting 0.827 · Decision Tree 0.791 · baseline 0.500.
Differences among the top four are within noise, so the simplest (Logistic Regression) was selected.

Held-out test (n=154, threshold 0.294), 95 % bootstrap CI:

| Metric | Value | 95 % CI |
|---|---|---|
| ROC-AUC | 0.809 | 0.735 – 0.872 |
| PR-AUC | 0.664 | 0.564 – 0.771 |
| Sensitivity | 0.815 | 0.704 – 0.907 |
| Specificity | 0.670 | 0.580 – 0.750 |
| Precision | 0.571 | 0.500 – 0.647 |
| Accuracy | 0.721 | 0.649 – 0.786 |
| Brier | 0.174 | 0.142 – 0.209 |

Confusion matrix: TN 67, FP 33, FN 10, TP 44. At this threshold roughly 4 in 10 positive predictions
are false alarms. Permutation importance is dominated by glucose; insulin, blood pressure and skin-fold
thickness contribute essentially nothing. Figures are in `artifacts/figures/` after training.

## Example usage
Defaults in the form (1 pregnancy, glucose 110, BMI 28, age 35, optional fields blank) gave an estimated
probability of 13 % (below the 29 % screening threshold).

## Limitations
- 768 records, one 1990s study, women of Pima heritage only; no external validation.
- The documented label is a WHO glucose-tolerance criterion applied at any survey examination or in routine care; the timing
  relative to the recorded features is not documented and recorded glucose never exceeds 199 mg/dL. The target is therefore
  *recorded diabetes status*, not future onset. Glucose is the strongest predictor, but a training-only ablation shows the other
  features still carry signal (CV ROC-AUC 0.799 glucose alone, 0.768 without glucose, 0.845 all).
- Probabilities are calibrated to a 35 % prevalence and are not personal real-world risks.
- Wide test CIs (n=154). The threshold trades false negatives for false positives; it is not a medical cut-off.
- Explanations show how the model uses inputs, not causes, and can mislead for correlated features.
- Many popular risk factors (family history, smoking, activity, HbA1c) are **not** in this dataset and so are not inputs.

## Privacy
No identifiers requested; no third-party calls; history kept only in session memory; reports generated in
memory. Details: [docs/privacy.md](docs/privacy.md). No regulatory compliance is claimed.

## Deployment
Local, Docker and Streamlit Community Cloud / Hugging Face Spaces: [docs/deployment.md](docs/deployment.md).

## Future improvements
Larger, more representative data (e.g. NHANES / BRFSS with proper survey handling); external validation;
fairness analysis by subgroup; optional opt-in persistent history with deletion; model monitoring.

## Screenshots
Not committed yet. Run the app and save captures to `docs/screenshots/` (none are fabricated here).

## License & acknowledgements
MIT (code). Data: Smith et al. (1988), NIDDK; donated to UCI by V. Sigillito; mirrored on OpenML.
