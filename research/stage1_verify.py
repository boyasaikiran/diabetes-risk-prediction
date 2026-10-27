"""Stage 1 independent verification of the existing project's reported results.

Recomputes everything from the raw CSV, the saved model and the seeded split WITHOUT using
src.evaluate / src.train metric code (except where explicitly stated), then compares with
artifacts/metrics.json. Writes research/stage1/verification_results.json.
Run:  .venv\\Scripts\\python research\\stage1_verify.py
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
OUT = ROOT / "research" / "stage1"
OUT.mkdir(parents=True, exist_ok=True)

import joblib  # noqa: E402
import sklearn  # noqa: E402
from sklearn.base import clone  # noqa: E402
from sklearn.calibration import CalibratedClassifierCV  # noqa: E402
from sklearn.metrics import average_precision_score, brier_score_loss, confusion_matrix, roc_auc_score  # noqa: E402
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split  # noqa: E402

from src.data_loader import FEATURES, TARGET  # noqa: E402
from src.validation import FIELD_SPECS  # noqa: E402

R: dict = {"versions": {"python": sys.version.split()[0], "sklearn": sklearn.__version__, "pandas": pd.__version__, "numpy": np.__version__}}
M = json.loads((ROOT / "artifacts/metrics.json").read_text(encoding="utf-8"))
META = M["metadata"]
SEED = META["seed"]

# ---------------------------------------------------------------- A. data integrity
csv = ROOT / "data/raw/pima_diabetes.csv"
prov = json.loads((ROOT / "data/raw/provenance.json").read_text(encoding="utf-8"))
sha = hashlib.sha256(csv.read_bytes()).hexdigest()
df = pd.read_csv(csv)
R["data"] = {"sha256_matches_provenance": sha == prov["sha256"], "rows": len(df), "positives": int(df[TARGET].sum()),
             "duplicate_rows_incl_target": int(df.duplicated().sum()),
             "duplicate_feature_rows": int(df.duplicated(subset=FEATURES).sum()),
             "feature_rows_duplicated_with_different_label": int((df.groupby(FEATURES)[TARGET].nunique() > 1).sum())}
pos, neg = df[df[TARGET] == 1], df[df[TARGET] == 0]
R["glucose_vs_label"] = {
    "max_glucose_all": float(df.Glucose.max()), "max_glucose_positive": float(pos.Glucose.max()), "max_glucose_negative": float(neg.Glucose.max()),
    "n_glucose_ge_200": int((df.Glucose >= 200).sum()),
    "median_glucose_pos_nonzero": float(pos.Glucose[pos.Glucose > 0].median()), "median_glucose_neg_nonzero": float(neg.Glucose[neg.Glucose > 0].median()),
    "share_positive_with_glucose_lt_140": float(((pos.Glucose > 0) & (pos.Glucose < 140)).mean()),
    "share_positive_with_glucose_lt_126": float(((pos.Glucose > 0) & (pos.Glucose < 126)).mean()),
    "univariate_glucose_auc_nonzero": float(roc_auc_score(df[df.Glucose > 0][TARGET], df[df.Glucose > 0].Glucose)),
}

# ---------------------------------------------------------------- B. split + saved model
X, y = df[FEATURES], df[TARGET]
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.20, stratify=y, random_state=SEED)
R["split"] = {"n_train": len(X_tr), "n_test": len(X_te), "train_pos": int(y_tr.sum()), "test_pos": int(y_te.sum()),
              "matches_metadata": [len(X_tr), len(X_te)] == [META["n_train"], META["n_test"]],
              "train_test_index_overlap": int(len(set(X_tr.index) & set(X_te.index))),
              "exact_feature_row_overlap_train_test": int(len(pd.merge(X_tr.drop_duplicates(), X_te.drop_duplicates(), how="inner"))),
              "test_indices_head": sorted(X_te.index.tolist())[:10]}
bundle = joblib.load(ROOT / "models/model.joblib")
model = bundle["model"]
R["model"] = {"type": type(model).__name__, "classes_": model.classes_.tolist(), "n_calibrated": len(model.calibrated_classifiers_),
              "base_clf": [type(cc.estimator.named_steps["clf"]).__name__ for cc in model.calibrated_classifiers_][:1],
              "C": model.calibrated_classifiers_[0].estimator.named_steps["clf"].C,
              "class_weight": model.calibrated_classifiers_[0].estimator.named_steps["clf"].class_weight,
              "calibrator": type(model.calibrated_classifiers_[0].calibrators[0]).__name__}
p = model.predict_proba(X_te)[:, 1]
thr = META["threshold"]
yhat = (p >= thr).astype(int)
tn, fp, fn, tp = confusion_matrix(y_te, yhat, labels=[0, 1]).ravel()
manual = {"tp": int(((yhat == 1) & (y_te.values == 1)).sum()), "fp": int(((yhat == 1) & (y_te.values == 0)).sum()),
          "fn": int(((yhat == 0) & (y_te.values == 1)).sum()), "tn": int(((yhat == 0) & (y_te.values == 0)).sum())}
rec = {"roc_auc": roc_auc_score(y_te, p), "pr_auc": average_precision_score(y_te, p), "brier": brier_score_loss(y_te, p),
       "sensitivity": tp / (tp + fn), "specificity": tn / (tn + fp), "precision": tp / (tp + fp), "accuracy": (tp + tn) / len(y_te)}
rec["f1"] = 2 * rec["precision"] * rec["sensitivity"] / (rec["precision"] + rec["sensitivity"])
rep = M["test"]["metrics"]
cmp = {"roc_auc": rep["roc_auc"], "pr_auc": rep["pr_auc"], "brier": rep["brier"], "sensitivity": rep["recall_sensitivity"], "specificity": rep["specificity"],
       "precision": rep["precision"], "accuracy": rep["accuracy"], "f1": rep["f1"]}
R["test_metrics"] = {"recomputed": rec, "reported": cmp, "max_abs_diff": max(abs(rec[k] - cmp[k]) for k in rec),
                     "confusion_sklearn": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)}, "confusion_manual": manual,
                     "confusion_reported": rep["confusion_matrix"], "pred_pos_rate": float(yhat.mean())}

# independent bootstrap (different code and seed) vs saved CI
rng = np.random.default_rng(2024)
yv = y_te.values
posi, negi = np.where(yv == 1)[0], np.where(yv == 0)[0]
bs = {k: [] for k in ["roc_auc", "sensitivity", "specificity", "precision", "brier"]}
for _ in range(5000):
    idx = np.concatenate([rng.choice(posi, len(posi)), rng.choice(negi, len(negi))])
    yy, pp = yv[idx], p[idx]
    pr = pp >= thr
    t_p, f_p = ((pr) & (yy == 1)).sum(), ((pr) & (yy == 0)).sum()
    f_n, t_n = ((~pr) & (yy == 1)).sum(), ((~pr) & (yy == 0)).sum()
    bs["roc_auc"].append(roc_auc_score(yy, pp)); bs["brier"].append(brier_score_loss(yy, pp))
    bs["sensitivity"].append(t_p / (t_p + f_n)); bs["specificity"].append(t_n / (t_n + f_p)); bs["precision"].append(t_p / max(t_p + f_p, 1))
saved_ci = M["test"]["ci95"]
key = {"roc_auc": "roc_auc", "sensitivity": "recall_sensitivity", "specificity": "specificity", "precision": "precision", "brier": "brier"}
R["bootstrap"] = {k: {"independent_5000": [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))], "saved_1000": saved_ci[key[k]]} for k, v in bs.items()}
R["bootstrap"]["note"] = "Both resample only the 154 test records for a FIXED model and threshold; training variability and threshold uncertainty are not included."

# ---------------------------------------------------------------- C. leakage checks on the saved model
cv = StratifiedKFold(5, shuffle=True, random_state=SEED)
chk = []
for k, (tr_i, _) in enumerate(cv.split(X_tr, y_tr)):
    sub = X_tr.iloc[tr_i].copy()
    for c in ["Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI"]:
        sub.loc[sub[c] == 0, c] = np.nan
    exp = sub.median().reindex(FEATURES).to_numpy()
    got = model.calibrated_classifiers_[k].estimator.named_steps["prep"].named_steps["columns"].named_transformers_["num"]["impute"].statistics_
    full_tr = X_tr.copy()
    for c in ["Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI"]:
        full_tr.loc[full_tr[c] == 0, c] = np.nan
    chk.append({"fold": k, "imputer_equals_fold_train_median": bool(np.allclose(exp, got)),
                "imputer_equals_full_train_median": bool(np.allclose(full_tr.median().reindex(FEATURES).to_numpy(), got)),
                "imputer_equals_full_dataset_median": bool(np.allclose(df[FEATURES].replace({c: {0: np.nan} for c in ["Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI"]}).median().to_numpy(), got))})
R["preprocessing_fit_check"] = chk

# OOF reproduction: recompute out-of-fold predictions and the threshold independently
base = clone(model.calibrated_classifiers_[0].estimator)  # same pipeline + best params
cal = CalibratedClassifierCV(base, method="sigmoid", cv=cv)
oof = cross_val_predict(cal, X_tr, y_tr, cv=cv, method="predict_proba")[:, 1]
cands = np.unique(np.round(oof, 4))
best = max(t for t in cands if ((oof >= t) & (y_tr.values == 1)).sum() / (y_tr.values == 1).sum() >= 0.80)
R["threshold_reproduction"] = {"saved": thr, "recomputed": float(best), "oof_sens_at_thr": float(((oof >= thr) & (y_tr.values == 1)).sum() / (y_tr.values == 1).sum()),
                               "oof_spec_at_thr": float(((oof < thr) & (y_tr.values == 0)).sum() / (y_tr.values == 0).sum()),
                               "oof_auc": float(roc_auc_score(y_tr, oof)), "oof_brier": float(brier_score_loss(y_tr, oof))}
# threshold mismatch: final model = average of 5 fold-models; compare training-set score distribution
p_tr_final = model.predict_proba(X_tr)[:, 1]
R["threshold_reproduction"]["final_model_in_sample_sens_at_thr"] = float(((p_tr_final >= thr) & (y_tr.values == 1)).sum() / (y_tr.values == 1).sum())
R["threshold_reproduction"]["final_model_in_sample_spec_at_thr"] = float(((p_tr_final < thr) & (y_tr.values == 0)).sum() / (y_tr.values == 0).sum())

# ---------------------------------------------------------------- D. app path vs batch path; validation coverage
from src.predict import Predictor  # noqa: E402

pred = Predictor()
ok_rows, rej = 0, {}
diffs = []
rng2 = np.random.default_rng(0)
for i in rng2.choice(X_te.index, 40, replace=False):
    row = X_te.loc[i]
    raw = {f: ("" if (f in ["Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI"] and row[f] == 0) else float(row[f])) for f in FEATURES}
    try:
        r = pred.predict(raw, explain=False)
        diffs.append(abs(r.probability - float(model.predict_proba(X_te.loc[[i]])[:, 1][0])))
        ok_rows += 1
    except Exception as e:  # noqa: BLE001
        rej[str(e)[:90]] = rej.get(str(e)[:90], 0) + 1
R["app_vs_batch"] = {"n_tested": 40, "accepted": ok_rows, "max_abs_prob_diff_accepted": float(max(diffs)) if diffs else None, "rejected_reasons": rej}
# how many dataset rows would the app's validation reject (non-zero values outside plausibility ranges)?
rejected_rows, by_feat = 0, {}
for _, row in df.iterrows():
    bad = []
    for f in FEATURES:
        v = row[f]
        s = FIELD_SPECS[f]
        zero_missing = f in ["Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI"] and v == 0
        if zero_missing:
            continue
        if not (s.minimum <= v <= s.maximum):
            bad.append(f)
    if bad:
        rejected_rows += 1
        for f in bad:
            by_feat[f] = by_feat.get(f, 0) + 1
R["validation_coverage"] = {"dataset_rows_rejected_by_app_ranges": rejected_rows, "by_feature": by_feat}
# zero vs NaN equivalence
a = pred.model.predict_proba(pd.DataFrame([[1, 0, 70, 20, 0, 30, 0.4, 40]], columns=FEATURES))[0, 1]
b = pred.model.predict_proba(pd.DataFrame([[1, np.nan, 70, 20, np.nan, 30, 0.4, 40]], columns=FEATURES))[0, 1]
R["zero_vs_nan_equivalent"] = bool(abs(a - b) < 1e-12)

# ---------------------------------------------------------------- E. SHAP faithfulness and stability
from src.explainability import explain_prediction  # noqa: E402

ex_rows = X_te.iloc[:6]
adds, methods = [], set()
for i in range(len(ex_rows)):
    xr = ex_rows.iloc[[i]].copy()
    for c in ["Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI"]:
        xr.loc[xr[c] == 0, c] = np.nan
    e = explain_prediction(pred.model, xr, pred.background)
    methods.add(e["method"])
    adds.append(abs(e["base_value"] + sum(c["contribution"] for c in e["contributions"]) - float(pred.model.predict_proba(xr)[:, 1][0])))
xr = ex_rows.iloc[[0]].copy()
for c in ["Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI"]:
    xr.loc[xr[c] == 0, c] = np.nan
runs = []
for sd in range(1, 9):
    e = explain_prediction(pred.model, xr, pred.background, seed=sd)
    runs.append({c["feature"]: c["contribution"] for c in e["contributions"]})
dfr = pd.DataFrame(runs)
R["shap"] = {"methods_used": sorted(methods), "max_additivity_error": float(max(adds)),
             "seed_sd_of_contribution_pp": {k: float(v * 100) for k, v in dfr.std().items()},
             "seed_max_range_pp": float((dfr.max() - dfr.min()).max() * 100),
             "note": "permutation explainer, max_evals=161, 100-row background; contributions in probability units for ONE test row across 8 seeds"}

# ---------------------------------------------------------------- F. CV score reproduction (best params) + single-split sensitivity pointers
from sklearn.model_selection import cross_val_score  # noqa: E402

lr = clone(model.calibrated_classifiers_[0].estimator)
sc = cross_val_score(lr, X_tr, y_tr, cv=cv, scoring="roc_auc")
R["cv_reproduction"] = {"recomputed_mean": float(sc.mean()), "recomputed_sd": float(sc.std()),
                        "saved_mean": M["model_comparison"][0]["cv_roc_auc"], "saved_sd": M["model_comparison"][0]["cv_roc_auc_std"],
                        "note": "same folds were used for tuning, OOF predictions, calibration decision and threshold (not nested)"}

# ---------------------------------------------------------------- G. retrain reproducibility in an isolated copy (does not touch repo artifacts)
tmp = Path(tempfile.mkdtemp(prefix="drp_repro_"))
for d in ["src", "config"]:
    shutil.copytree(ROOT / d, tmp / d)
(tmp / "data" / "raw").mkdir(parents=True)
shutil.copy(csv, tmp / "data/raw/pima_diabetes.csv")
shutil.copy(ROOT / "data/raw/provenance.json", tmp / "data/raw/provenance.json")
proc = subprocess.run([sys.executable, "-W", "ignore", "-m", "src.train"], cwd=tmp, capture_output=True, text=True, timeout=600)
mrep = json.loads((tmp / "artifacts/metrics.json").read_text(encoding="utf-8"))
a1, a2 = M["test"]["metrics"], mrep["test"]["metrics"]
R["retrain_reproducibility"] = {"returncode": proc.returncode,
                                "max_abs_diff_test_metrics": max(abs(a1[k] - a2[k]) for k in ["roc_auc", "pr_auc", "brier", "accuracy", "precision", "recall_sensitivity", "specificity", "f1", "threshold"]),
                                "same_selected_model": mrep["metadata"]["selected_model"] == META["selected_model"],
                                "same_confusion": a1["confusion_matrix"] == a2["confusion_matrix"],
                                "same_cv_table": all(abs(x["cv_roc_auc"] - y["cv_roc_auc"]) < 1e-9 for x, y in zip(M["model_comparison"], mrep["model_comparison"], strict=True))}
shutil.rmtree(tmp, ignore_errors=True)

(OUT / "verification_results.json").write_text(json.dumps(R, indent=1, default=str), encoding="utf-8")
print(json.dumps(R, indent=1, default=str))
