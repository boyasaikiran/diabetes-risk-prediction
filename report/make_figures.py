"""Figures for the E-report. Charts use the saved artifacts (artifacts/metrics.json);
diagrams are drawn programmatically. Output: report/figures/*.png"""
import json
import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "figures"
OUT.mkdir(exist_ok=True)
M = json.loads((ROOT / "artifacts" / "metrics.json").read_text(encoding="utf-8"))

plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"], "font.size": 11})
NAVY, BLUE, TEAL, AMBER, GREY = "#10243A", "#247BA0", "#20B2AA", "#F4B942", "#8A979C"

# reuse figures saved by training
for name in ["confusion_matrix", "roc_curve", "pr_curve", "calibration", "feature_importance"]:
    shutil.copy(ROOT / "artifacts" / "figures" / f"{name}.png", OUT / f"{name}.png")


def box(ax, x, y, w, h, text, fc, tc="white", fs=10):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", fc=fc, ec="none"))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", color=tc, fontsize=fs, fontweight="bold", wrap=True)


def arrow(ax, x1, y1, x2, y2, color=NAVY):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=14, lw=1.6, color=color))


# ---- Fig: methodology workflow (offline training + inference) ----
fig, ax = plt.subplots(figsize=(10, 5.6))
ax.set_xlim(0, 10)
ax.set_ylim(0, 6)
ax.axis("off")
ax.text(0.05, 5.7, "A. Offline training (python -m src.train)", color=BLUE, fontsize=12, fontweight="bold")
off = ["Download &\nschema check", "Profile data\n(zeros, classes)", "Stratified split\n614 / 154", "5-fold CV tuning\n7 candidates", "Select model,\ncalibrate, threshold", "Single test\nevaluation", "Save model.joblib\n+ metrics.json"]
w, g = 1.22, 0.2
for i, t in enumerate(off):
    x = 0.05 + i * (w + g)
    box(ax, x, 4.3, w, 1.0, t, AMBER if i == 6 else BLUE, NAVY if i == 6 else "white", 8.5)
    if i < len(off) - 1:
        arrow(ax, x + w + 0.01, 4.8, x + w + g - 0.01, 4.8)
ax.text(0.05, 3.4, "B. Prediction-time inference (app.py)", color=TEAL, fontsize=12, fontweight="bold")
inf = ["User input\n(form)", "Input\nvalidation", "Saved pipeline:\nzero→NaN, impute,\nscale", "Calibrated\nlogistic reg.", "Probability vs\nthreshold", "SHAP\nexplanation", "Dashboard +\nPDF/CSV report"]
for i, t in enumerate(inf):
    x = 0.05 + i * (w + g)
    box(ax, x, 1.9, w, 1.1, t, AMBER if i == 3 else TEAL, NAVY if i == 3 else "white", 8.5)
    if i < len(inf) - 1:
        arrow(ax, x + w + 0.01, 2.45, x + w + g - 0.01, 2.45)
arrow(ax, 0.05 + 6 * (w + g) + w / 2, 4.28, 0.05 + 3 * (w + g) + w / 2, 3.02, AMBER)
ax.text(5.2, 3.45, "loaded, never retrained", fontsize=9, color=NAVY, style="italic")
ax.text(0.05, 0.9, "The test split is touched only in the 'Single test evaluation' stage. Preprocessing statistics are fitted on training data only.",
        fontsize=9.5, color=NAVY)
fig.savefig(OUT / "workflow.png", dpi=200, bbox_inches="tight")
plt.close(fig)

# ---- Fig: software architecture ----
fig, ax = plt.subplots(figsize=(10, 5.2))
ax.set_xlim(0, 10)
ax.set_ylim(-0.1, 5.2)
ax.axis("off")
box(ax, 3.4, 4.3, 3.2, 0.7, "app.py + ui/  (Streamlit, Plotly, CSS)", NAVY, fs=10)
mods = [("validation.py\nfield specs, ranges", 0.2), ("predict.py\nPredictor class", 2.8), ("explainability.py\nSHAP / occlusion", 5.4), ("report_generator.py\nPDF / CSV", 7.9)]
for t, x in mods:
    box(ax, x, 2.9, 1.9, 0.95, t, BLUE, fs=8.5)
    arrow(ax, 5.0, 4.28, x + 0.95, 3.87)
box(ax, 2.8, 1.5, 4.4, 0.8, "models/model.joblib  (pipeline + background + metadata)", AMBER, NAVY, 9)
arrow(ax, 3.75, 2.88, 4.4, 2.32)
arrow(ax, 6.35, 2.88, 5.7, 2.32)
box(ax, 0.2, 0.1, 2.2, 0.8, "train.py + evaluate.py\n(offline)", TEAL, fs=8.5)
box(ax, 2.7, 0.1, 2.2, 0.8, "preprocessing.py\nZeroToNaN, pipeline", TEAL, fs=8.5)
box(ax, 5.2, 0.1, 2.2, 0.8, "data_loader.py\nOpenML, profiling", TEAL, fs=8.5)
box(ax, 7.7, 0.1, 2.1, 0.8, "config.yaml\nseed, paths, CV", TEAL, fs=8.5)
ax.add_patch(FancyBboxPatch((0.1, 0.0), 9.8, 1.0, boxstyle="round,pad=0.02,rounding_size=0.1", fc="none", ec=GREY, ls="--", lw=1.2))
ax.text(5.0, 1.17, "Training-time modules (run offline by src.train)", ha="center", fontsize=9, color=NAVY, style="italic")
arrow(ax, 5.0, 1.38, 5.0, 1.5, GREY)
fig.savefig(OUT / "architecture.png", dpi=200, bbox_inches="tight")
plt.close(fig)

# ---- Fig: CV model comparison ----
comp = sorted(M["model_comparison"], key=lambda r: r["cv_roc_auc"])
fig, ax = plt.subplots(figsize=(7.5, 4))
names = [r["model"].replace(" (majority class)", "") for r in comp]
vals = [r["cv_roc_auc"] for r in comp]
errs = [r["cv_roc_auc_std"] for r in comp]
bars = ax.barh(names, vals, xerr=errs, color=[AMBER if r["model"] == "Logistic Regression" else BLUE for r in comp], capsize=3)
for b, v in zip(bars, vals, strict=True):
    ax.text(v + 0.03, b.get_y() + b.get_height() / 2, f"{v:.3f}", va="center", fontsize=9)
ax.set_xlim(0.4, 1.0)
ax.set_xlabel("Mean ROC-AUC over 5 folds (error bar = SD across folds)")
ax.set_title("Cross-validated ROC-AUC on the training split")
fig.tight_layout()
fig.savefig(OUT / "cv_comparison.png", dpi=200)
plt.close(fig)

# ---- Fig: data profile (class balance + zero counts) ----
prof = M["data_profile"]
fig, axs = plt.subplots(1, 2, figsize=(9, 3.6))
cc = prof["class_counts"]
axs[0].bar(["Negative (0)", "Positive (1)"], [cc["0"], cc["1"]], color=[BLUE, AMBER])
for i, v in enumerate([cc["0"], cc["1"]]):
    axs[0].text(i, v + 8, str(v), ha="center")
axs[0].set_title("Class distribution (n = 768)")
axs[0].set_ylabel("Records")
z = prof["zeros_treated_as_missing"]
zs = sorted(z.items(), key=lambda kv: kv[1])
axs[1].barh([k for k, _ in zs], [v for _, v in zs], color=BLUE)
for i, (_, v) in enumerate(zs):
    axs[1].text(v + 5, i, f"{v} ({v / 768:.0%})", va="center", fontsize=9)
axs[1].set_xlim(0, 480)
axs[1].set_title("Zeros treated as missing")
fig.tight_layout()
fig.savefig(OUT / "data_profile.png", dpi=200)
plt.close(fig)

# ---- Fig: split & CV protocol ----
fig, ax = plt.subplots(figsize=(9, 3.4))
ax.set_xlim(0, 10)
ax.set_ylim(0, 3.4)
ax.axis("off")
box(ax, 0.1, 2.5, 7.9, 0.7, "Training split: 614 records (80%) - stratified", BLUE, fs=10)
box(ax, 8.1, 2.5, 1.8, 0.7, "Test: 154 (20%)", AMBER, NAVY, 10)
for i in range(5):
    x = 0.1 + i * 1.6
    ax.add_patch(FancyBboxPatch((x, 1.4), 1.5, 0.6, boxstyle="round,pad=0.01", fc="#DCE6EC", ec="none"))
    ax.add_patch(FancyBboxPatch((x + i * 0.3, 1.4), 0.3, 0.6, boxstyle="round,pad=0.01", fc=TEAL, ec="none"))
    ax.text(x + 0.75, 1.15, f"Fold {i + 1}", ha="center", fontsize=8)
ax.text(0.1, 2.15, "5-fold stratified CV (teal = validation fold): tuning and model selection only", fontsize=9.5, color=NAVY)
ax.text(0.1, 0.55, "Final fit on all 614 training records + sigmoid calibration + threshold from out-of-fold predictions", fontsize=9.5, color=NAVY)
ax.text(8.1, 1.85, "scored once", fontsize=9.5, color=NAVY)
arrow(ax, 9.0, 2.48, 9.0, 2.0, AMBER)
fig.savefig(OUT / "split_protocol.png", dpi=200, bbox_inches="tight")
plt.close(fig)
print(sorted(p.name for p in OUT.iterdir()))
