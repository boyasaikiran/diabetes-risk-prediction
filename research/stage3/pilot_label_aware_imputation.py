"""EXPLORATORY PILOT (Stage 3 feasibility only; NOT a reported result).
Uses the TRAINING split only (seed 42, 614 rows); the 154-row test split is never touched.
Question: does outcome-conditional ('group'/'class-conditional') median imputation of the Pima zeros
inflate cross-validated AUC relative to fold-contained, label-free median imputation, and does a
label-permutation canary detect it?  Writes research/stage3/pilot_results.json"""
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent.parent
import sys  # noqa: E402

sys.path.insert(0, str(ROOT))
from src.data_loader import FEATURES, TARGET  # noqa: E402
from src.preprocessing import ZeroToNaN  # noqa: E402

ZERO_COLS = ["Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI"]
df = pd.read_csv(ROOT / "data/raw/pima_diabetes.csv")
X, y = df[FEATURES], df[TARGET]
X_tr, _X_te, y_tr, _y_te = train_test_split(X, y, test_size=0.20, stratify=y, random_state=42)  # test split deliberately unused
X_tr, y_tr = X_tr.reset_index(drop=True), y_tr.reset_index(drop=True)
R = {"n_train": len(X_tr)}

# ---- descriptive facts on the training split (missingness vs outcome)
miss = {}
for c in ZERO_COLS:
    m = X_tr[c] == 0
    miss[c] = {"n_missing": int(m.sum()), "share_missing": float(m.mean()), "pos_rate_missing": float(y_tr[m].mean()) if m.any() else None,
               "pos_rate_observed": float(y_tr[~m].mean()),
               "class_median_observed": {"neg": float(X_tr.loc[(~m) & (y_tr == 0), c].median()), "pos": float(X_tr.loc[(~m) & (y_tr == 1), c].median())}}
R["missingness_train"] = miss
R["train_pos_rate"] = float(y_tr.mean())


def zero_to_nan(frame):
    f = frame.copy()
    for c in ZERO_COLS:
        f.loc[f[c] == 0, c] = np.nan
    return f


def leaky_class_median(frame, labels):
    """Typical 'group median' practice: medians computed per outcome class over ALL rows, then used to fill each row's NaNs."""
    f = zero_to_nan(frame)
    for c in ZERO_COLS:
        med = f.groupby(labels.values)[c].transform("median")
        f[c] = f[c].fillna(med)
    return f


def model(kind):
    est = LogisticRegression(C=0.1, class_weight="balanced", max_iter=2000) if kind == "LR" else RandomForestClassifier(300, max_depth=5, min_samples_leaf=8, random_state=0, n_jobs=-1)
    return Pipeline([("c", ColumnTransformer([("n", Pipeline([("s", StandardScaler())]), FEATURES)])), ("m", est)])


def valid_pipe(kind):
    num = Pipeline([("i", SimpleImputer(strategy="median")), ("s", StandardScaler())])
    est = LogisticRegression(C=0.1, class_weight="balanced", max_iter=2000) if kind == "LR" else RandomForestClassifier(300, max_depth=5, min_samples_leaf=8, random_state=0, n_jobs=-1)
    return Pipeline([("z", ZeroToNaN()), ("c", ColumnTransformer([("n", num, FEATURES)])), ("m", est)])


def cv_auc(pipe, Xd, yd, seeds=(1, 2, 3)):
    out = []
    for s in seeds:
        out.append(cross_val_score(pipe, Xd, yd, cv=StratifiedKFold(5, shuffle=True, random_state=s), scoring="roc_auc").mean())
    return float(np.mean(out)), float(np.std(out))


res = {}
for kind in ["LR", "RF"]:
    # A: valid, fold-contained, label-free median imputation
    res[f"{kind}_valid_foldcontained_median"] = cv_auc(valid_pipe(kind), X_tr, y_tr)
    # B: leaky - class-conditional median imputation on all training rows BEFORE cross-validation
    X_leak = leaky_class_median(X_tr, y_tr)
    res[f"{kind}_leaky_class_median_before_cv"] = cv_auc(model(kind), X_leak, y_tr)
    # C: label-permutation canary (valid pipeline should be ~0.5; leaky imputation should exceed 0.5)
    rng = np.random.default_rng(7)
    perm_valid, perm_leak = [], []
    for _ in range(5):
        yp = pd.Series(rng.permutation(y_tr.values))
        perm_valid.append(cv_auc(valid_pipe(kind), X_tr, yp, seeds=(1,))[0])
        perm_leak.append(cv_auc(model(kind), leaky_class_median(X_tr, yp), yp, seeds=(1,))[0])
    res[f"{kind}_permuted_labels_valid"] = (float(np.mean(perm_valid)), float(np.std(perm_valid)))
    res[f"{kind}_permuted_labels_leaky_imputation"] = (float(np.mean(perm_leak)), float(np.std(perm_leak)))
R["cv_auc_mean_sd"] = res
R["note"] = "EXPLORATORY PILOT on the training split only; 3 CV seeds (real labels), 5 label permutations; not for reporting; test split untouched."
(Path(__file__).resolve().parent / "pilot_results.json").write_text(json.dumps(R, indent=1), encoding="utf-8")
print(json.dumps(R, indent=1))
