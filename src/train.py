"""Reproducible training: compare candidates, tune, select, calibrate, evaluate once.

Protocol
--------
1. Stratified train/test split (test is untouched until the final step).
2. Every candidate is tuned with the same stratified K-fold CV on TRAIN only.
   The CV folds act as the validation sets; all preprocessing is inside the
   pipeline so it is re-fit per fold (no leakage).
3. Selection: best mean CV ROC-AUC, then the simplest/most interpretable model
   within one standard error of the best.
4. Probability calibration (sigmoid) is kept only if it lowers out-of-fold
   Brier score on TRAIN.
5. The decision threshold is chosen from out-of-fold TRAIN probabilities.
6. The held-out test set is scored once, for the selected model only.
"""
from __future__ import annotations

import json
import logging
import platform
from datetime import UTC, datetime

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.base import clone
from sklearn.calibration import CalibratedClassifierCV
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import (
    GradientBoostingClassifier,
    HistGradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_val_predict, train_test_split
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

from src.config import load_config, resolve, setup_logging
from src.data_loader import FEATURES, TARGET, load_dataset, profile_dataset
from src.evaluate import bootstrap_ci, compute_metrics, curve_data, save_figures
from src.preprocessing import build_model_pipeline

log = logging.getLogger(__name__)
MODEL_VERSION = "1.0.0"


def candidate_models(seed: int) -> dict[str, tuple[object, dict, int]]:
    """name -> (estimator, param grid, interpretability rank; lower = simpler)."""
    return {
        "Baseline (majority class)": (DummyClassifier(strategy="prior"), {}, 0),
        "Logistic Regression": (
            LogisticRegression(max_iter=2000, random_state=seed),
            {"clf__C": [0.01, 0.1, 1, 10], "clf__class_weight": [None, "balanced"]}, 1),
        "Decision Tree": (
            DecisionTreeClassifier(random_state=seed),
            {"clf__max_depth": [2, 3, 4, 6], "clf__min_samples_leaf": [5, 15, 30]}, 2),
        "Random Forest": (
            RandomForestClassifier(n_estimators=300, random_state=seed, n_jobs=-1),
            {"clf__max_depth": [3, 5, None], "clf__min_samples_leaf": [3, 8]}, 3),
        "Gradient Boosting": (
            GradientBoostingClassifier(random_state=seed),
            {"clf__n_estimators": [50, 100, 200], "clf__learning_rate": [0.03, 0.1],
             "clf__max_depth": [2, 3]}, 4),
        "SVM (RBF)": (
            CalibratedClassifierCV(SVC(random_state=seed), ensemble=False, cv=3),
            {"clf__estimator__C": [0.3, 1, 3], "clf__estimator__gamma": ["scale", 0.05]}, 5),
        "HistGradientBoosting": (
            HistGradientBoostingClassifier(random_state=seed),
            {"clf__learning_rate": [0.03, 0.1], "clf__max_depth": [2, 3],
             "clf__max_iter": [100, 200], "clf__l2_regularization": [0.0, 1.0]}, 6),
    }


def choose_threshold(y, oof_proba, target_sensitivity: float) -> float:
    """Highest threshold whose out-of-fold sensitivity >= target (max specificity)."""
    y = np.asarray(y)
    best = 0.0
    for t in np.unique(np.round(oof_proba, 4)):
        pred = oof_proba >= t
        sens = (pred & (y == 1)).sum() / max((y == 1).sum(), 1)
        if sens >= target_sensitivity:
            best = max(best, float(t))
    return best


def run(seed: int | None = None) -> dict:
    cfg = load_config()
    seed = cfg["seed"] if seed is None else seed
    model_dir = resolve(cfg["paths"]["model_dir"]); model_dir.mkdir(parents=True, exist_ok=True)
    art_dir = resolve(cfg["paths"]["artifact_dir"]); art_dir.mkdir(parents=True, exist_ok=True)

    df = load_dataset()
    profile = profile_dataset(df, cfg["data"]["zero_is_missing"])
    (art_dir / "data_profile.json").write_text(json.dumps(profile, indent=2), encoding="utf-8")

    X, y = df[FEATURES], df[TARGET]
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=cfg["split"]["test_size"], stratify=y, random_state=seed)
    log.info("Split: train=%d test=%d", len(X_tr), len(X_te))

    cv = StratifiedKFold(cfg["cv"]["folds"], shuffle=True, random_state=seed)
    scoring = {"roc_auc": "roc_auc", "pr_auc": "average_precision",
               "neg_brier": "neg_brier_score", "recall": "recall", "accuracy": "accuracy"}

    rows, fitted = [], {}
    for name, (est, grid, rank) in candidate_models(seed).items():
        gs = GridSearchCV(build_model_pipeline(est), grid or {}, scoring=scoring,
                          refit="roc_auc", cv=cv, n_jobs=-1)
        gs.fit(X_tr, y_tr)
        i = gs.best_index_
        r = gs.cv_results_
        rows.append({
            "model": name, "rank_interpretability": rank,
            "cv_roc_auc": r["mean_test_roc_auc"][i], "cv_roc_auc_std": r["std_test_roc_auc"][i],
            "cv_pr_auc": r["mean_test_pr_auc"][i], "cv_brier": -r["mean_test_neg_brier"][i],
            "cv_recall_at_0.5": r["mean_test_recall"][i], "cv_accuracy": r["mean_test_accuracy"][i],
            "best_params": json.dumps({k: v for k, v in gs.best_params_.items()}, default=str),
        })
        fitted[name] = gs.best_estimator_
        log.info("%-28s CV AUC %.3f ± %.3f", name, rows[-1]["cv_roc_auc"], rows[-1]["cv_roc_auc_std"])

    comp = pd.DataFrame(rows).sort_values("cv_roc_auc", ascending=False).reset_index(drop=True)
    top = comp.iloc[0]
    se = top.cv_roc_auc_std / np.sqrt(cfg["cv"]["folds"])
    eligible = comp[comp.cv_roc_auc >= top.cv_roc_auc - se]
    chosen = eligible.sort_values("rank_interpretability").iloc[0]["model"]
    log.info("Selected: %s (best CV AUC model: %s)", chosen, top.model)

    base = fitted[chosen]
    # Calibration decision on TRAIN out-of-fold predictions only.
    raw_oof = cross_val_predict(clone(base), X_tr, y_tr, cv=cv, method="predict_proba")[:, 1]
    cal_est = CalibratedClassifierCV(clone(base), method="sigmoid", cv=cv)
    cal_oof = cross_val_predict(cal_est, X_tr, y_tr, cv=cv, method="predict_proba")[:, 1]
    b_raw, b_cal = brier_score_loss(y_tr, raw_oof), brier_score_loss(y_tr, cal_oof)
    use_cal = b_cal < b_raw
    final = clone(cal_est) if use_cal else clone(base)
    final.fit(X_tr, y_tr)
    oof = cal_oof if use_cal else raw_oof
    thr = choose_threshold(y_tr, oof, cfg["threshold"]["target_sensitivity"])
    log.info("Calibration kept=%s (Brier raw %.4f vs cal %.4f); threshold=%.3f", use_cal, b_raw, b_cal, thr)

    # ---- single evaluation on held-out test ----
    p_te = final.predict_proba(X_te)[:, 1]
    test_m = compute_metrics(y_te, p_te, thr)
    test_ci = bootstrap_ci(y_te, p_te, thr, n=cfg["bootstrap"]["n"], seed=seed)
    train_oof_m = compute_metrics(y_tr, oof, thr)
    imp = permutation_importance(final, X_te, y_te, scoring="roc_auc", n_repeats=30, random_state=seed)
    importance = {f: {"mean": float(imp.importances_mean[k]), "std": float(imp.importances_std[k])}
                  for k, f in enumerate(FEATURES)}

    bg = X_tr.sample(n=min(100, len(X_tr)), random_state=seed).reset_index(drop=True)
    metadata = {
        "model_version": MODEL_VERSION,
        "trained_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "selected_model": chosen, "calibrated": bool(use_cal),
        "feature_order": FEATURES, "threshold": thr,
        "threshold_rule": f"max specificity s.t. out-of-fold TRAIN sensitivity >= "
                          f"{cfg['threshold']['target_sensitivity']}",
        "training_prevalence": float(y_tr.mean()),
        "feature_ranges": {f: [float(X_tr[f].min()), float(X_tr[f].max())] for f in FEATURES},
        "seed": seed, "n_train": int(len(X_tr)), "n_test": int(len(X_te)),
        "versions": {"python": platform.python_version(), "scikit_learn": sklearn.__version__,
                     "pandas": pd.__version__, "numpy": np.__version__},
        "dataset": "Pima Indians Diabetes Database (UCI/NIDDK via OpenML 37)",
    }
    metrics = {
        "metadata": metadata,
        "test": {"metrics": test_m, "ci95": test_ci, "curves": curve_data(y_te, p_te)},
        "train_oof": {"metrics": train_oof_m, "curves": curve_data(y_tr, oof)},
        "brier_raw_vs_calibrated_train_oof": [float(b_raw), float(b_cal)],
        "permutation_importance_test": importance,
        "model_comparison": json.loads(comp.to_json(orient="records")),
        "data_profile": profile,
    }
    joblib.dump({"model": final, "background": bg, "metadata": metadata}, model_dir / "model.joblib")
    (model_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    (art_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    comp.to_csv(art_dir / "model_comparison.csv", index=False)
    save_figures(art_dir / "figures", y_te, p_te, test_m, importance, "held-out test")
    log.info("Test: AUC %.3f sens %.3f spec %.3f", test_m["roc_auc"],
             test_m["recall_sensitivity"], test_m["specificity"])
    return metrics


if __name__ == "__main__":
    setup_logging()
    run()
