# Deployment

A clean deployment has **no model file**: models are git-ignored. Always train as part of the build or provide the artifacts from a trusted store.

## Local
```bash
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements-dev.txt
python -m src.train
streamlit run app.py
```

## Docker
```bash
docker build -t diabetes-risk .
docker run -p 8501:8501 diabetes-risk
```
The image trains the model during the build (needs internet to fetch OpenML) so the container starts ready.
Set `DRP_MODEL_DIR` to point at a mounted volume containing `model.joblib` if you prefer external artifacts:
`docker run -p 8501:8501 -v /path/models:/models -e DRP_MODEL_DIR=/models diabetes-risk`.
(Docker was not run in the authoring environment; test the image before relying on it.)

## Streamlit Community Cloud / Hugging Face Spaces
1. Push the repo (no data or models committed).
2. Point the platform at `app.py`; it installs `requirements.txt` (CPU only).
3. Add a build/first-run step that executes `python -m src.train`, or commit the small generated `models/model.joblib`, `models/metadata.json` and `artifacts/metrics.json` after reviewing them. Storage on these platforms is ephemeral; nothing user-entered is persisted by the app.
4. Smoke test: open the Risk Estimation page and press Estimate; confirm Model Insights loads.
