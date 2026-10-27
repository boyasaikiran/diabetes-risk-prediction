"""Reusable Streamlit/Plotly UI pieces."""
from __future__ import annotations

from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

from src.report_generator import DISCLAIMER

TEAL, GREY, AMBER = "#0e6e87", "#8a979c", "#d9962b"


def inject_css() -> None:
    css = (Path(__file__).parent / "styles.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def disclaimer() -> None:
    st.markdown(f'<div class="disclaimer"><b>Educational tool, not a diagnosis.</b> {DISCLAIMER}</div>',
                unsafe_allow_html=True)


def stat_card(title: str, value: str, note: str = "") -> str:
    return (f'<div class="card"><h4>{title}</h4><div class="big">{value}</div>'
            f'<div class="small">{note}</div></div>')


def contribution_chart(contribs: list[dict]) -> go.Figure:
    items = list(reversed(contribs))
    fig = go.Figure(go.Bar(
        x=[c["contribution"] * 100 for c in items], y=[c["label"] for c in items],
        orientation="h", marker_color=[AMBER if c["contribution"] > 0 else TEAL for c in items],
        hovertemplate="%{y}: %{x:+.1f} percentage points<extra></extra>"))
    fig.update_layout(height=340, margin=dict(l=0, r=10, t=10, b=30),
                      xaxis_title="Effect on model estimate (percentage points)",
                      plot_bgcolor="white")
    return fig


def _base(title: str, x: str, y: str) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(title=title, xaxis_title=x, yaxis_title=y, height=400,
                      margin=dict(l=10, r=10, t=40, b=70), plot_bgcolor="white",
                      legend=dict(orientation="h", yanchor="top", y=-0.38))
    return fig


def roc_fig(c: dict, auc: float) -> go.Figure:
    f = _base("ROC curve (held-out test)", "1 − specificity", "Sensitivity")
    f.add_scatter(x=c["roc"]["fpr"], y=c["roc"]["tpr"], name=f"AUC {auc:.3f}", line_color=TEAL)
    f.add_scatter(x=[0, 1], y=[0, 1], name="Chance", line=dict(dash="dash", color=GREY))
    return f


def pr_fig(c: dict, ap: float) -> go.Figure:
    f = _base("Precision–recall (held-out test)", "Recall", "Precision")
    f.add_scatter(x=c["pr"]["recall"], y=c["pr"]["precision"], name=f"AP {ap:.3f}", line_color=TEAL)
    return f


def calibration_fig(c: dict) -> go.Figure:
    f = _base("Calibration (held-out test, 8 quantile bins)", "Mean predicted probability",
              "Observed fraction positive")
    f.add_scatter(x=c["calibration"]["mean_predicted"], y=c["calibration"]["fraction_positive"],
                  mode="lines+markers", name="Model", line_color=TEAL)
    f.add_scatter(x=[0, 1], y=[0, 1], name="Perfect", line=dict(dash="dash", color=GREY))
    return f


def confusion_fig(cm: dict) -> go.Figure:
    z = [[cm["tn"], cm["fp"]], [cm["fn"], cm["tp"]]]
    f = go.Figure(go.Heatmap(z=z, x=["Predicted negative", "Predicted positive"],
                             y=["Actual negative", "Actual positive"], text=z,
                             texttemplate="%{text}", colorscale="Blues", showscale=False))
    f.update_layout(title="Confusion matrix (held-out test)", height=340,
                    margin=dict(l=10, r=10, t=40, b=10), yaxis_autorange="reversed")
    return f


def importance_fig(imp: dict) -> go.Figure:
    names = sorted(imp, key=lambda k: imp[k]["mean"])
    f = _base("Permutation importance (held-out test)", "Drop in ROC-AUC when shuffled", "")
    f.add_bar(x=[imp[n]["mean"] for n in names], y=names, orientation="h", marker_color=TEAL,
              error_x=dict(type="data", array=[imp[n]["std"] for n in names]))
    return f
