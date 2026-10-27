"""Diabetes Risk Prediction System — Streamlit app (educational, not diagnostic)."""
from __future__ import annotations

import json
import logging
from datetime import datetime

import pandas as pd
import streamlit as st

from src.config import load_config, resolve, setup_logging
from src.predict import InvalidInputError, ModelNotFoundError, Predictor
from src.report_generator import LIMITATIONS, build_csv, build_pdf
from src.validation import FIELD_SPECS
from ui import components as ui

setup_logging()
log = logging.getLogger("app")
st.set_page_config(page_title="Diabetes Risk Estimator", page_icon="🩺", layout="wide")
ui.inject_css()


@st.cache_resource(show_spinner="Loading model…")
def get_predictor() -> Predictor:
    return Predictor()


@st.cache_data
def get_metrics() -> dict | None:
    p = resolve(load_config()["paths"]["artifact_dir"]) / "metrics.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


try:
    predictor = get_predictor()
except ModelNotFoundError as exc:
    st.title("Diabetes Risk Estimator")
    st.error(str(exc))
    st.code("python -m src.train", language="bash")
    st.stop()

metrics = get_metrics()
meta = predictor.metadata
st.session_state.setdefault("history", [])

page = st.sidebar.radio("Navigate", ["Home", "Risk Estimation", "Model Insights",
                                     "Session History", "About"])
st.sidebar.caption("Educational project · not a medical device")


def home() -> None:
    st.title("Diabetes Risk Prediction System")
    st.caption("Machine learning + explainable AI · educational risk-estimation prototype")
    ui.disclaimer()
    st.write("Enter a few health measurements to see a model-generated probability, which "
             "inputs influenced it, and a downloadable report. The model is a "
             f"{meta['selected_model']} trained on a small public research dataset.")
    c1, c2, c3 = st.columns(3)
    if metrics:
        t = metrics["test"]["metrics"]
        c1.markdown(ui.stat_card("Test ROC-AUC", f"{t['roc_auc']:.2f}",
                                 f"held-out, n={t['n']}"), unsafe_allow_html=True)
        c2.markdown(ui.stat_card("Sensitivity / specificity",
                                 f"{t['recall_sensitivity']:.0%} / {t['specificity']:.0%}",
                                 "at the screening threshold, held-out test"), unsafe_allow_html=True)
    c3.markdown(ui.stat_card("Training data", f"{meta['n_train']} rows",
                             "Pima Indians Diabetes Database"), unsafe_allow_html=True)
    st.subheader("Dataset in one paragraph")
    st.write("768 records from a 1990s NIDDK study of adult females of Pima Indian heritage in "
             "Arizona. The label records diabetes status by a WHO glucose-tolerance criterion (timing relative to the measurements is undocumented). Results "
             "therefore may not apply to other populations. See *About* for details.")


def estimate() -> None:
    st.title("Risk Estimation")
    ui.disclaimer()
    with st.form("inputs"):
        cols = st.columns(2)
        raw: dict = {}
        for i, (name, s) in enumerate(FIELD_SPECS.items()):
            with cols[i % 2]:
                tag = "" if s.required else " (optional)"
                if s.required:
                    num = int if s.integer else float
                    raw[name] = st.number_input(
                        f"{s.label} [{s.unit}]{tag}", min_value=num(s.minimum),
                        max_value=num(s.maximum), value=num(s.default), step=num(s.step),
                        format="%d" if s.integer else "%.1f", help=s.help, key=name)
                else:
                    raw[name] = st.text_input(f"{s.label} [{s.unit}]{tag}", value="",
                                              placeholder="leave blank if unknown",
                                              help=s.help, key=name)
        go = st.form_submit_button("Estimate", type="primary")
    if not go:
        st.info("Fill in the form and press **Estimate**. Optional fields may be left blank.")
        return
    try:
        with st.spinner("Computing…"):
            pred = predictor.predict(raw)
    except InvalidInputError as exc:
        st.error(f"Please correct the inputs — {exc}")
        return
    except Exception:  # noqa: BLE001
        log.exception("Unexpected prediction failure")
        st.error("Something went wrong while computing the estimate. Please try again.")
        return

    st.session_state["history"].append({
        "time": datetime.now().strftime("%H:%M:%S"), "probability": round(pred.probability, 3),
        **{k: (None if v != v else v) for k, v in pred.inputs.items()}})

    side = "at or above" if pred.above_threshold else "below"
    a, b = st.columns([1, 2])
    a.markdown(ui.stat_card("Model-estimated probability", f"{pred.probability:.0%}",
                            f"{side} the model's screening threshold ({pred.threshold:.0%})"),
               unsafe_allow_html=True)
    b.write(f"The model estimates a **{pred.probability:.0%}** probability. This is {side} its "
            f"screening threshold of {pred.threshold:.0%}, an operating point chosen to catch "
            "most positive cases in the training data (it is **not** an established medical "
            "cut-off, and no 'low/medium/high' categories are claimed). The probability is "
            f"calibrated to a dataset in which {meta['training_prevalence']:.0%} of people were "
            "positive, so it should not be read as your personal real-world risk.")
    for w in pred.warnings:
        st.warning(w)

    st.subheader("Which inputs influenced this estimate")
    ex = pred.explanation
    st.plotly_chart(ui.contribution_chart(ex["contributions"]), width="stretch")
    st.write(ex["plain_language"])
    st.caption(f"Method: {ex['method']} on the model's probability output; baseline average "
               f"prediction {ex['base_value']:.0%}. Contributions describe how the model used "
               "each input, not what causes diabetes, and can be unreliable when inputs are "
               "correlated.")
    st.markdown(f'<div class="small">{LIMITATIONS}</div>', unsafe_allow_html=True)
    d1, d2 = st.columns(2)
    d1.download_button("Download report (PDF)", build_pdf(pred), "diabetes_risk_estimate.pdf",
                       "application/pdf")
    d2.download_button("Download report (CSV)", build_csv(pred), "diabetes_risk_estimate.csv",
                       "text/csv")


def insights() -> None:
    st.title("Model Insights")
    if not metrics:
        st.error("metrics.json not found. Run `python -m src.train`.")
        return
    st.info("Model selection used cross-validation on the **training** split. The curves and "
            "metrics below are from the **held-out test split** (n="
            f"{metrics['test']['metrics']['n']}), scored once for the final model.")
    st.subheader("Model comparison (5-fold CV on training data)")
    comp = pd.DataFrame(metrics["model_comparison"]).drop(columns=["rank_interpretability"])
    st.dataframe(comp.round(3), hide_index=True, width="stretch")
    t, ci, curves = (metrics["test"][k] for k in ("metrics", "ci95", "curves"))
    st.subheader(f"Held-out test metrics — {meta['selected_model']}")
    rows = [("Accuracy", "accuracy"), ("Precision", "precision"),
            ("Sensitivity (recall)", "recall_sensitivity"), ("Specificity", "specificity"),
            ("F1", "f1"), ("ROC-AUC", "roc_auc"), ("PR-AUC", "pr_auc"), ("Brier score", "brier")]
    st.dataframe(pd.DataFrame([{"Metric": n, "Value": round(t[k], 3),
                                "95% bootstrap CI": f"{ci[k][0]:.3f} – {ci[k][1]:.3f}"}
                               for n, k in rows]), hide_index=True)
    st.caption(f"Threshold {t['threshold']:.3f}: {meta['threshold_rule']}. "
               "Wide intervals reflect the small test set.")
    c1, c2 = st.columns(2)
    c1.plotly_chart(ui.confusion_fig(t["confusion_matrix"]), width="stretch")
    c2.plotly_chart(ui.roc_fig(curves, t["roc_auc"]), width="stretch")
    c3, c4 = st.columns(2)
    c3.plotly_chart(ui.pr_fig(curves, t["pr_auc"]), width="stretch")
    c4.plotly_chart(ui.calibration_fig(curves), width="stretch")
    st.plotly_chart(ui.importance_fig(metrics["permutation_importance_test"]),
                    width="stretch")
    st.caption("Permutation importance measures reliance on a feature, not causation, and is "
               "shared among correlated features.")


def history() -> None:
    st.title("Session History")
    st.write("Kept only in this browser session's memory. Nothing is saved to disk or sent "
             "anywhere; closing the tab discards it.")
    h = st.session_state["history"]
    if h:
        st.dataframe(pd.DataFrame(h), hide_index=True, width="stretch")
    else:
        st.info("No estimates yet in this session.")
    if st.button("Clear history", disabled=not h):
        st.session_state["history"] = []
        st.rerun()


def about() -> None:
    st.title("About & Documentation")
    ui.disclaimer()
    st.markdown(f"""
**Intended use.** Education and demonstration of an ML workflow. Not for diagnosis, treatment or screening decisions.

**Method.** Stratified 80/20 train/test split; seven candidate models plus a majority-class baseline
tuned with 5-fold CV on training data; selection by CV ROC-AUC with a preference for simpler models
within one standard error; sigmoid calibration kept only if it improved out-of-fold Brier score;
threshold fixed from out-of-fold training predictions; one final evaluation on the test split.
Selected: **{meta['selected_model']}** v{meta['model_version']}, trained {meta['trained_utc']}.

**Dataset.** Pima Indians Diabetes Database (NIDDK; UCI; mirrored on OpenML id 37), 768 adult females
of Pima heritage. Zeros in glucose, blood pressure, skin-fold, insulin and BMI are treated as missing
and imputed with training medians. The outcome follows a WHO glucose-tolerance criterion applied at any
examination or in routine care; its timing relative to the measurements is undocumented. Glucose is the strongest predictor, but the other
features still carry signal.

**Limitations.** Small, old, single-population data; no external validation; probabilities reflect the
dataset's 35% prevalence; explanations are associations, not causes; not clinically validated.

**Privacy.** No identifiers are requested. Inputs are processed in this app's server process and are not
stored or sent to third parties. History lives in session memory only. Reports are generated in memory
and downloaded by you.

**Maintainer.** Project maintainers — see the repository README.
""")


{"Home": home, "Risk Estimation": estimate, "Model Insights": insights,
 "Session History": history, "About": about}[page]()
