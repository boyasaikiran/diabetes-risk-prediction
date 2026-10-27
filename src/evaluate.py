"""Metrics, bootstrap confidence intervals, curves and figures."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from sklearn.calibration import calibration_curve  # noqa: E402
from sklearn.metrics import (  # noqa: E402
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    precision_recall_curve,
    roc_auc_score,
    roc_curve,
)


def compute_metrics(y_true, proba, threshold: float) -> dict:
    """Threshold-dependent and threshold-free metrics for binary predictions."""
    y = np.asarray(y_true).astype(int)
    p = np.asarray(proba, dtype=float)
    pred = (p >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    div = lambda a, b: float(a / b) if b else float("nan")  # noqa: E731
    precision = div(tp, tp + fp)
    recall = div(tp, tp + fn)
    return {
        "threshold": float(threshold),
        "accuracy": div(tp + tn, len(y)),
        "precision": precision,
        "recall_sensitivity": recall,
        "specificity": div(tn, tn + fp),
        "f1": div(2 * precision * recall, precision + recall)
        if precision == precision and recall == recall
        else float("nan"),
        "roc_auc": float(roc_auc_score(y, p)),
        "pr_auc": float(average_precision_score(y, p)),
        "brier": float(brier_score_loss(y, p)),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "n": int(len(y)),
    }


def bootstrap_ci(y_true, proba, threshold: float, n: int = 1000, seed: int = 42) -> dict:
    """Percentile 95% bootstrap CIs (stratified resampling) for key metrics."""
    y = np.asarray(y_true).astype(int)
    p = np.asarray(proba, dtype=float)
    rng = np.random.default_rng(seed)
    pos, neg = np.where(y == 1)[0], np.where(y == 0)[0]
    keys = ["accuracy", "precision", "recall_sensitivity", "specificity", "f1",
            "roc_auc", "pr_auc", "brier"]
    draws: dict[str, list[float]] = {k: [] for k in keys}
    for _ in range(n):
        idx = np.concatenate([rng.choice(pos, len(pos)), rng.choice(neg, len(neg))])
        m = compute_metrics(y[idx], p[idx], threshold)
        for k in keys:
            draws[k].append(m[k])
    return {
        k: [float(np.nanpercentile(v, 2.5)), float(np.nanpercentile(v, 97.5))]
        for k, v in draws.items()
    }


def curve_data(y_true, proba, bins: int = 8) -> dict:
    """Curve points saved to JSON so the app can render them without recomputation."""
    y = np.asarray(y_true).astype(int)
    p = np.asarray(proba, dtype=float)
    fpr, tpr, _ = roc_curve(y, p)
    prec, rec, _ = precision_recall_curve(y, p)
    frac_pos, mean_pred = calibration_curve(y, p, n_bins=bins, strategy="quantile")
    return {
        "roc": {"fpr": fpr.tolist(), "tpr": tpr.tolist()},
        "pr": {"precision": prec.tolist(), "recall": rec.tolist()},
        "calibration": {"mean_predicted": mean_pred.tolist(), "fraction_positive": frac_pos.tolist()},
    }


def save_figures(out_dir: Path, y_true, proba, metrics: dict, importance: dict, label: str) -> None:
    """Static PNGs for documentation (the app draws interactive versions)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    cd = curve_data(y_true, proba)

    fig, ax = plt.subplots(figsize=(4.5, 4))
    cm = metrics["confusion_matrix"]
    mat = np.array([[cm["tn"], cm["fp"]], [cm["fn"], cm["tp"]]])
    ax.imshow(mat, cmap="Blues")
    for (i, j), v in np.ndenumerate(mat):
        ax.text(j, i, v, ha="center", va="center", fontsize=14,
                color="white" if v > mat.max() / 2 else "black")
    ax.set_xticks([0, 1], ["Pred. neg", "Pred. pos"])
    ax.set_yticks([0, 1], ["Actual neg", "Actual pos"])
    ax.set_title(f"Confusion matrix ({label})")
    fig.tight_layout(); fig.savefig(out_dir / "confusion_matrix.png", dpi=150); plt.close(fig)

    fig, ax = plt.subplots(figsize=(4.5, 4))
    ax.plot(cd["roc"]["fpr"], cd["roc"]["tpr"], label=f"AUC = {metrics['roc_auc']:.3f}")
    ax.plot([0, 1], [0, 1], "--", color="grey")
    ax.set(xlabel="1 - specificity", ylabel="Sensitivity", title=f"ROC ({label})")
    ax.legend(); fig.tight_layout(); fig.savefig(out_dir / "roc_curve.png", dpi=150); plt.close(fig)

    fig, ax = plt.subplots(figsize=(4.5, 4))
    ax.plot(cd["pr"]["recall"], cd["pr"]["precision"], label=f"AP = {metrics['pr_auc']:.3f}")
    ax.set(xlabel="Recall", ylabel="Precision", title=f"Precision-recall ({label})")
    ax.legend(); fig.tight_layout(); fig.savefig(out_dir / "pr_curve.png", dpi=150); plt.close(fig)

    fig, ax = plt.subplots(figsize=(4.5, 4))
    ax.plot(cd["calibration"]["mean_predicted"], cd["calibration"]["fraction_positive"], "o-")
    ax.plot([0, 1], [0, 1], "--", color="grey")
    ax.set(xlabel="Mean predicted probability", ylabel="Observed fraction positive",
           title=f"Calibration ({label}, Brier {metrics['brier']:.3f})")
    fig.tight_layout(); fig.savefig(out_dir / "calibration.png", dpi=150); plt.close(fig)

    names = list(importance)
    means = [importance[k]["mean"] for k in names]
    stds = [importance[k]["std"] for k in names]
    order = np.argsort(means)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.barh([names[i] for i in order], [means[i] for i in order],
            xerr=[stds[i] for i in order], color="#2a7f9e")
    ax.set(xlabel="Drop in ROC-AUC when shuffled", title=f"Permutation importance ({label})")
    fig.tight_layout(); fig.savefig(out_dir / "feature_importance.png", dpi=150); plt.close(fig)
