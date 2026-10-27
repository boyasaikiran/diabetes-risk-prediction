"""Extra evidence for the E-report, computed from the saved model and the same seeded split.
Writes report/extra_facts.json and report/figures/sample_report_page.png."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sklearn.model_selection import train_test_split  # noqa: E402

from src.config import load_config  # noqa: E402
from src.data_loader import FEATURES, TARGET, load_dataset  # noqa: E402
from src.predict import Predictor  # noqa: E402
from src.report_generator import build_pdf  # noqa: E402

cfg = load_config()
df = load_dataset()
X, y = df[FEATURES], df[TARGET]
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=cfg["split"]["test_size"], stratify=y, random_state=cfg["seed"])
pred = Predictor()
p = pred.model.predict_proba(X_te)[:, 1]
thr = pred.metadata["threshold"]
yhat = (p >= thr).astype(int)
out = {"n_test": len(y_te), "test_pos": int(y_te.sum()), "test_neg": int((1 - y_te).sum()),
       "train_pos": int(y_tr.sum()), "train_neg": int((1 - y_tr).sum()),
       "recomputed_tp_fp_fn_tn": [int(((yhat == 1) & (y_te == 1)).sum()), int(((yhat == 1) & (y_te == 0)).sum()),
                                  int(((yhat == 0) & (y_te == 1)).sum()), int(((yhat == 0) & (y_te == 0)).sum())]}


def summarise(mask, name):
    sub = X_te[mask]
    zero_missing = {c: int((sub[c] == 0).sum()) for c in ["Insulin", "SkinThickness", "BloodPressure"]}
    out[name] = {"n": int(mask.sum()), "median": {c: float(sub[c].median()) for c in ["Glucose", "BMI", "Age", "Pregnancies"]},
                 "missing_zero_counts": zero_missing, "mean_prob": float(p[mask].mean())}


te = pd.Series(y_te.values, index=X_te.index)
mask = lambda a, b: ((yhat == a) & (te.values == b))  # noqa: E731
summarise(mask(0, 1), "false_negatives")
summarise(mask(1, 0), "false_positives")
summarise(mask(1, 1), "true_positives")
summarise(mask(0, 0), "true_negatives")

# calibration bin sizes (quantile bins, as in evaluate.curve_data)
order = np.argsort(p)
out["calibration_bin_sizes"] = [len(b) for b in np.array_split(order, 8)]

# worked example used in the app screenshots
example = {"Pregnancies": 1, "Glucose": 150, "BloodPressure": "", "SkinThickness": "", "Insulin": "", "BMI": 33.5,
           "DiabetesPedigreeFunction": "", "Age": 45}
r = pred.predict(example)
out["example"] = {"inputs": example, "probability": r.probability, "threshold": r.threshold, "base": r.explanation["base_value"],
                  "method": r.explanation["method"], "warnings": r.warnings,
                  "contributions": [{k: c[k] for k in ("label", "contribution", "imputed")} for c in r.explanation["contributions"]]}
out["example"]["sum_check"] = r.explanation["base_value"] + sum(c["contribution"] for c in r.explanation["contributions"])

# standardised logistic-regression coefficients: mean/SD over the five calibration folds of the saved model
coefs = np.array([cc.estimator.named_steps["clf"].coef_[0] for cc in pred.model.calibrated_classifiers_])
out["lr_coefficients"] = {f: {"mean": float(coefs[:, i].mean()), "sd": float(coefs[:, i].std())} for i, f in enumerate(FEATURES)}
out["lr_intercept_mean"] = float(np.mean([cc.estimator.named_steps["clf"].intercept_[0] for cc in pred.model.calibrated_classifiers_]))

# real PDF report page from the app's generator
pdf = build_pdf(r)
Path(ROOT / "report" / "sample_report.pdf").write_bytes(pdf)
(ROOT / "report" / "extra_facts.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
print(json.dumps(out, indent=1))
