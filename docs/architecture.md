# Architecture

| Module | Responsibility |
|---|---|
| `src/config.py`, `config/config.yaml` | Central settings, `DRP_MODEL_DIR` override, logging setup |
| `src/data_loader.py` | Download/cache Pima data, schema checks, profiling, provenance |
| `src/preprocessing.py` | `ZeroToNaN` + imputer + scaler pipeline (single source of preprocessing) |
| `src/train.py` | Split, CV tuning, selection, calibration, threshold, final evaluation, artifacts |
| `src/evaluate.py` | Metrics, bootstrap CIs, curves, figures |
| `src/validation.py` | Field specs and input validation (also drives the form) |
| `src/predict.py` | Loads `model.joblib`, validates, predicts, warnings; never trains |
| `src/explainability.py` | SHAP/occlusion local explanations, plain-language summary |
| `src/report_generator.py` | In-memory CSV/PDF reports |
| `app.py`, `ui/` | Streamlit pages, Plotly charts, CSS |

Artifacts: `models/model.joblib` (pipeline + 100-row training background + metadata), `models/metadata.json`,
`artifacts/metrics.json`, `model_comparison.csv`, `figures/*.png`. All generated, none committed.

Flow at inference: form → `validate_inputs` → DataFrame in training feature order → saved pipeline →
probability → SHAP on the same pipeline → page/report. Logs never contain input values.
